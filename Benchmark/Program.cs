using System.Buffers.Binary;
using System.Data;
using System.Data.Common;
using System.Diagnostics;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;

// Private synthetic experiment. No production connection strings or data.
var root = Path.GetFullPath(args.Length > 0 ? args[0] : "..");
Directory.CreateDirectory(Path.Combine(root, "results"));
Directory.CreateDirectory(Path.Combine(root, "results", "sql"));
Directory.CreateDirectory(Path.Combine(root, "results", "plans"));
Directory.CreateDirectory(Path.Combine(root, "database"));
const string instance = @"(localdb)\JB_EF10Bench_20261109";
const string dbName = "JB_EF10_Synthetic_20261109";
var masterCs = $"Server={instance};Database=master;Integrated Security=true;TrustServerCertificate=true;Connect Timeout=20;Pooling=false";
var cs = $"Server={instance};Database={dbName};Integrated Security=true;TrustServerCertificate=true;Connect Timeout=20;Application Name=PrivateEF10Benchmark";
if (args.Contains("--verify-fix", StringComparer.Ordinal))
{
    await VerifyScopedFix(cs, root);
    return;
}
var jopts = new JsonSerializerOptions { WriteIndented = true };
var runId = "EF10LAB_" + DateTime.UtcNow.ToString("yyyyMMdd_HHmmss", CultureInfo.InvariantCulture);
await using var master = new SqlConnection(masterCs);
await master.OpenAsync();
if (Convert.ToInt32(await Scalar(master, "SELECT COUNT(*) FROM sys.databases WHERE name=@name", new SqlParameter("@name", dbName))) == 0)
{
    var mdf = Path.Combine(root, "database", dbName + ".mdf").Replace("'", "''");
    var ldf = Path.Combine(root, "database", dbName + ".ldf").Replace("'", "''");
    await Execute(master, $"CREATE DATABASE [{dbName}] ON PRIMARY (NAME=N'BenchData',FILENAME=N'{mdf}',SIZE=256MB,FILEGROWTH=64MB) LOG ON (NAME=N'BenchLog',FILENAME=N'{ldf}',SIZE=128MB,FILEGROWTH=64MB)");
}
await using var admin = new SqlConnection(cs);
await admin.OpenAsync();
await Execute(admin, "ALTER DATABASE CURRENT SET COMPATIBILITY_LEVEL=150; ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP=1; ALTER DATABASE CURRENT SET AUTO_UPDATE_STATISTICS OFF;");
if (Convert.ToInt32(await Scalar(admin, "SELECT COUNT(*) FROM sys.tables WHERE name='Transactions'")) == 0)
{
    Console.WriteLine("Seeding 1,000,000 deterministic synthetic transactions...");
    await Execute(admin, await File.ReadAllTextAsync(Path.Combine(root, "seed.sql")));
}
// No changes to seed/index/stats are permitted once an experiment starts.
var expectedAll = new Dictionary<int, Totals>();
using var expectedHash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
var bytes = new byte[21];
for (int n = 0; n < 1_000_000; n++)
{
    int merchant = n < 800_000 ? 1 + n % 1000 : 1001 + (n - 800_000) % 9000;
    long amount = 100 + ((long)n * 37 + 17) % 1_000_000;
    byte status = (byte)((n / 1000 + n) % 10 == 0 ? 0 : 1);
    AppendRow(expectedHash, bytes, n + 1, merchant, amount, status, n % 365);
    if (status == 1)
    {
        var old = expectedAll.GetValueOrDefault(merchant, new Totals(0, 0));
        expectedAll[merchant] = new Totals(old.Count + 1, old.Amount + amount);
    }
}
var generatorHash = Convert.ToHexString(expectedHash.GetHashAndReset()).ToLowerInvariant();
using var actualHash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
long rowCount = 0;
await using (var cmd = new SqlCommand("SELECT Id,MerchantId,AmountMinor,Status,DATEDIFF(day,'20250101',OccurredAt) FROM dbo.Transactions ORDER BY Id", admin))
await using (var reader = await cmd.ExecuteReaderAsync())
{
    while (await reader.ReadAsync())
    {
        AppendRow(actualHash, bytes, reader.GetInt32(0), reader.GetInt32(1), reader.GetInt64(2), reader.GetByte(3), reader.GetInt32(4));
        rowCount++;
    }
}
var storedHash = Convert.ToHexString(actualHash.GetHashAndReset()).ToLowerInvariant();
if (rowCount != 1_000_000 || storedHash != generatorHash) throw new InvalidOperationException("Stored data differs from the deterministic generator.");

var modes = new[] { ParameterTranslationMode.MultipleParameters, ParameterTranslationMode.Parameter, ParameterTranslationMode.Constant };
var cases = (from band in new[] { "hot", "cold" } from count in new[] { 5, 50, 500 } select new Scenario(band, count)).ToArray();
var clients = new Dictionary<ParameterTranslationMode, Client>();
foreach (var mode in modes)
{
    var capture = new Capture();
    var options = new DbContextOptionsBuilder<BenchDb>().UseSqlServer(cs, s => s.UseParameterizedCollectionMode(mode).CommandTimeout(60)).AddInterceptors(capture).Options;
    var db = new BenchDb(options);
    await db.Database.OpenConnectionAsync();
    clients[mode] = new Client(db, capture);
}
var version = await Scalar(admin, "SELECT @@VERSION");
var env = new { RunId = runId, StartedUtc = DateTime.UtcNow, SqlServer = version, Compatibility = 150, MaxDop = 1,
    EfCore = typeof(DbContext).Assembly.GetName().Version?.ToString(), SqlClient = typeof(SqlConnection).Assembly.GetName().Version?.ToString(),
    Runtime = RuntimeInformation.FrameworkDescription, OS = RuntimeInformation.OSDescription, Architecture = RuntimeInformation.ProcessArchitecture.ToString(),
    ProcessorCount = Environment.ProcessorCount, Cpu = Environment.GetEnvironmentVariable("PROCESSOR_IDENTIFIER"),
    Database = dbName, Instance = instance, Rows = rowCount, StoredDatasetSha256 = storedHash, GeneratorDatasetSha256 = generatorHash,
    Dataset = "10000 merchants; IDs 1..1000 receive 80% of rows; remaining 9000 receive 20%; 90% status=1; integer minor-unit amounts",
    Index = "(MerchantId,Status) INCLUDE(AmountMinor)", Statistics = "FULLSCAN at initial seed; AUTO_UPDATE_STATISTICS OFF; unchanged throughout",
    Harness = "Release; one in-flight query; 3 rounds x 20 samples per case/mode; 5 warmups per case/mode/round; randomized balanced order; same shared cache settings",
    Cache = "Database-scoped plan-cache clear before each round; buffer pool remains warm; no OS/global cache flush; warmup excluded",
    Churn = "15 new lists per band/size/mode; compile-inclusive client latency, separate from warmed steady measurements",
    Boundary = "LocalDB/SQL Server Express; not production, not a comparison of EF versions; same EF10 with 3 translation modes; client elapsed includes EF and local transport" };
await WriteJson("environment.json", env);
Console.WriteLine($"Verified rows={rowCount}, SHA256={storedHash}");
var samples = new List<Sample>();
var diagnostics = new List<object>();
var rng = new Random(20761109);
var snapshots = new Dictionary<string, Snapshot>();
var exportedSql = new HashSet<string>();
for (int round = 1; round <= 3; round++)
{
    await Execute(admin, "ALTER DATABASE SCOPED CONFIGURATION CLEAR PROCEDURE_CACHE;");
    var combinations = (from s in cases from m in modes select (s, m)).ToArray();
    // All methods/cases warm before any timed observations, no per-value warmup in churn.
    for (int warm = 0; warm < 5; warm++)
    foreach (var (s, m) in combinations.OrderBy(_ => rng.Next())) await Run(s, m, "steady", round, -1, 0, false);
    await SaveDmv($"warmup-round-{round}", 5);
    for (int sample = 0; sample < 20; sample++)
    foreach (var (s, m) in combinations.OrderBy(_ => rng.Next())) await Run(s, m, "steady", round, sample, 0, true);
    await SaveDmv($"steady-round-{round}", 25);
    if (round == 3)
    {
        foreach (var (key, snap) in snapshots.Where(x => x.Key.StartsWith("steady", StringComparison.Ordinal)))
            await SaveActualPlan(key, snap);
    }
    Console.WriteLine($"Steady round {round}/3 done; all aggregates matched.");
}
await Execute(admin, "ALTER DATABASE SCOPED CONFIGURATION CLEAR PROCEDURE_CACHE;");
for (int variant = 1; variant <= 15; variant++)
foreach (var (s, m) in (from s in cases from m in modes select (s, m)).OrderBy(_ => rng.Next()))
    await Run(s, m, "churn", 1, variant - 1, variant, true);
await SaveDmv("churn");

using (var writer = new StreamWriter(Path.Combine(root, "results", "samples.csv"), false, new UTF8Encoding(false)))
{
    writer.WriteLine("phase,round,sample,band,size,mode,client_ms,command_parameters,sql_shape_sha256,result_sha256,result_groups,matching_transactions,total_amount_minor");
    foreach (var s in samples)
        writer.WriteLine(string.Join(',', s.Phase, s.Round, s.Iteration, s.Band, s.Size, s.Mode, s.ClientMs.ToString("F6", CultureInfo.InvariantCulture), s.Parameters, s.SqlShape, s.ResultHash, s.Groups, s.Count, s.Amount));
}
await WriteJson("diagnostics.json", diagnostics);
await WriteJson("validation.json", new { DataHashMatches = storedHash == generatorHash, StoredDatasetSha256 = storedHash, RawTimedSamples = samples.Count,
    SteadySamples = samples.Count(x => x.Phase == "steady"), ChurnSamples = samples.Count(x => x.Phase == "churn"), AggregateChecks = "Every warmup/timed result checked against independently generated counts and exact integer totals for each merchant", ResultsAllMatch = true, FinishedUtc = DateTime.UtcNow });
foreach (var c in clients.Values) await c.Db.DisposeAsync();
Console.WriteLine($"COMPLETE: {samples.Count} timed observations, validation passed; public publication=none.");

async Task Run(Scenario s, ParameterTranslationMode mode, string phase, int round, int iteration, int variant, bool timed)
{
    var client = clients[mode];
    int start = (s.Band == "hot" ? 1 : 5001) + variant * 13;
    var ids = Enumerable.Range(start, s.Size).ToArray();
    string key = $"{phase}_{s.Band}_{s.Size}_{mode}";
    string tag = $"{runId}_{key}";
    var query = client.Db.Transactions.TagWith(tag).Where(t => t.Status == 1 && ids.Contains(t.MerchantId))
        .GroupBy(t => t.MerchantId).Select(g => new ReportRow { MerchantId = g.Key, Count = g.LongCount(), Amount = g.Sum(t => t.AmountMinor) }).OrderBy(x => x.MerchantId);
    client.Capture.Detailed = !timed;
    long started = Stopwatch.GetTimestamp();
    var result = await query.ToListAsync();
    double elapsed = Stopwatch.GetElapsedTime(started).TotalMilliseconds;
    var expected = ids.Where(expectedAll.ContainsKey).Select(id => new ReportRow { MerchantId = id, Count = expectedAll[id].Count, Amount = expectedAll[id].Amount }).ToList();
    if (result.Count != expected.Count || result.Zip(expected).Any(x => x.First.MerchantId != x.Second.MerchantId || x.First.Count != x.Second.Count || x.First.Amount != x.Second.Amount))
        throw new InvalidOperationException($"Wrong result {key} variant={variant}");
    var sqlText = client.Capture.Text;
    var parameterCount = client.Capture.ParameterCount;
    if (!sqlText.Contains(tag, StringComparison.Ordinal)) throw new InvalidOperationException("SQL tag mismatch");
    if ((mode == ParameterTranslationMode.Constant && parameterCount != 0)
        || (mode == ParameterTranslationMode.Parameter && (parameterCount != 1 || !sqlText.Contains("OPENJSON", StringComparison.Ordinal)))
        || (mode == ParameterTranslationMode.MultipleParameters && (parameterCount < s.Size || sqlText.Contains("OPENJSON", StringComparison.Ordinal))))
        throw new InvalidOperationException("Unexpected collection translation shape: " + key);
    if (phase == "steady" && !snapshots.ContainsKey(key))
    {
        snapshots[key] = client.Capture.Last ?? throw new InvalidOperationException("No diagnostic snapshot");
    }
    if (exportedSql.Add(key))
    {
        await File.WriteAllTextAsync(Path.Combine(root, "results", "sql", key + ".sql"), query.ToQueryString(), new UTF8Encoding(false));
    }
    if (timed)
    {
        var fingerprint = Hash(string.Join(';', result.Select(x => $"{x.MerchantId}:{x.Count}:{x.Amount}")));
        samples.Add(new Sample(phase, round, iteration, s.Band, s.Size, mode.ToString(), elapsed, parameterCount, Hash(sqlText), fingerprint, result.Count, result.Sum(x => x.Count), result.Sum(x => x.Amount)));
    }
}
async Task SaveDmv(string phase, long? expectedExecutions = null)
{
    var values = new List<Dictionary<string, object?>>();
    const string sql = "SELECT t.text,qs.execution_count,qs.total_worker_time,qs.total_elapsed_time,qs.total_logical_reads,qs.total_rows,qs.plan_generation_num,CONVERT(varchar(130),qs.plan_handle,1) AS plan_handle FROM sys.dm_exec_query_stats qs CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) t WHERE CHARINDEX(@needle,t.text)>0";
    await using var cmd = new SqlCommand(sql, admin);
    cmd.Parameters.AddWithValue("@needle", runId + "_");
    await using var reader = await cmd.ExecuteReaderAsync();
    while (await reader.ReadAsync())
    {
        var row = new Dictionary<string, object?>();
        for (int i = 0; i < reader.FieldCount; i++) row[reader.GetName(i)] = reader.IsDBNull(i) ? null : reader.GetValue(i);
        values.Add(row);
    }
    if (expectedExecutions is not null && (values.Count != 18 || values.Any(v => Convert.ToInt64(v["execution_count"]) != expectedExecutions)))
        throw new InvalidOperationException($"Unexpected warmed cached execution counts in {phase}: {JsonSerializer.Serialize(values.Select(v=>v["execution_count"]))}; plans={values.Count}");
    await WriteJson($"dmv-{phase}.json", values);
}
async Task SaveActualPlan(string key, Snapshot snap)
{
    await using var connection = new SqlConnection(cs);
    await connection.OpenAsync();
    await Execute(connection, "SET STATISTICS XML ON;");
    await using var cmd = new SqlCommand(snap.Text, connection) { CommandTimeout = 60 };
    foreach (var p in snap.Parameters) cmd.Parameters.Add(new SqlParameter(p.Name, p.Type) { Value = p.Value, Size = p.Size });
    await using var reader = await cmd.ExecuteReaderAsync();
    string? xml = null;
    do
    {
        bool isPlan = reader.FieldCount == 1 && reader.GetName(0).Contains("Showplan", StringComparison.OrdinalIgnoreCase);
        while (await reader.ReadAsync()) if (isPlan) xml = reader.GetString(0);
    } while (await reader.NextResultAsync());
    if (xml is null) throw new InvalidOperationException("No actual execution plan captured: " + key);
    await File.WriteAllTextAsync(Path.Combine(root, "results", "plans", key + ".sqlplan"), xml, new UTF8Encoding(false));
    diagnostics.Add(new { Key = key, ActualPlan = "plans/" + key + ".sqlplan", Boundary = "Separate diagnostic execution after timed observations; not included in latency or pre-diagnostic DMV counts" });
}
async Task WriteJson(string name, object value) => await File.WriteAllTextAsync(Path.Combine(root, "results", name), JsonSerializer.Serialize(value, jopts) + "\n", new UTF8Encoding(false));
static string Hash(string s) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(s))).ToLowerInvariant();
static async Task VerifyScopedFix(string connectionString, string outputRoot)
{
    // Additional targeted check: default stays scalar; only the report opts into JSON.
    var capture = new Capture();
    var options = new DbContextOptionsBuilder<BenchDb>().UseSqlServer(connectionString, s => s.UseParameterizedCollectionMode(ParameterTranslationMode.MultipleParameters)).AddInterceptors(capture).Options;
    await using var db = new BenchDb(options);
    await db.Database.OpenConnectionAsync();
    var ids = Enumerable.Range(5001, 500).ToArray();
    var prefix = "EF10FIX_" + DateTime.UtcNow.ToString("yyyyMMdd_HHmmss", CultureInfo.InvariantCulture);
    var baseline = db.Transactions.TagWith(prefix + "_baseline").Where(t => t.Status == 1 && ids.Contains(t.MerchantId));
    var patched = db.Transactions.TagWith(prefix + "_scoped").Where(t => t.Status == 1 && EF.Parameter(ids).Contains(t.MerchantId));
    IQueryable<ReportRow> Report(IQueryable<PaymentTransaction> q) => q.GroupBy(t => t.MerchantId).Select(g => new ReportRow { MerchantId=g.Key,Count=g.LongCount(),Amount=g.Sum(t=>t.AmountMinor) }).OrderBy(r=>r.MerchantId);
    var queries = new[] { Report(baseline), Report(patched) };
    var expectedHash = File.ReadLines(Path.Combine(outputRoot,"results","samples.csv")).Skip(1).Select(x=>x.Split(','))
        .First(x=>x[0]=="steady" && x[3]=="cold" && x[4]=="500")[9];
    var times = new List<double>[] {new(),new()};
    var raw = new List<object>();
    var sql = new string[2];
    var counts = new int[2];
    var random = new Random(9071);
    for (int iteration=-5;iteration<30;iteration++)
    foreach (int which in Enumerable.Range(0,2).OrderBy(_=>random.Next()))
    {
        long started=Stopwatch.GetTimestamp();
        var rows=await queries[which].ToListAsync();
        double elapsed=Stopwatch.GetElapsedTime(started).TotalMilliseconds;
        var resultHash=Hash(string.Join(';',rows.Select(x=>$"{x.MerchantId}:{x.Count}:{x.Amount}")));
        if(resultHash!=expectedHash)throw new InvalidOperationException("Scoped fix changed the report result.");
        if(which==0 && (capture.ParameterCount!=500 || capture.Text.Contains("OPENJSON",StringComparison.Ordinal)))throw new InvalidOperationException("Global default unexpectedly changed.");
        if(which==1 && (capture.ParameterCount!=1 || !capture.Text.Contains("OPENJSON",StringComparison.Ordinal)))throw new InvalidOperationException("Scoped fix did not generate JSON.");
        sql[which]=capture.Text;counts[which]=capture.ParameterCount;
        if(iteration>=0){times[which].Add(elapsed);raw.Add(new{Iteration=iteration,Variant=which==0?"default-scalar":"scoped-EF.Parameter",ClientMs=elapsed,ResultSha256=resultHash});}
    }
    var result=new { GlobalDefault="MultipleParameters",ScopedChange="EF.Parameter(ids)",Case="500 cold merchants, same fixed list as primary benchmark",WarmupsPerVariant=5,SamplesPerVariant=30,
        AllResultsMatch=true,ExpectedResultSha256=expectedHash,Raw=raw,Sql=sql,ParameterCounts=counts,FinishedUtc=DateTime.UtcNow,
        TimingBoundary="Warmed sequential paired follow-up, randomized order; separate from primary 1350 observations" };
    await File.WriteAllTextAsync(Path.Combine(outputRoot,"results","scoped-fix.json"),JsonSerializer.Serialize(result,new JsonSerializerOptions{WriteIndented=true})+"\n",new UTF8Encoding(false));
    foreach(int which in Enumerable.Range(0,2)) await File.WriteAllTextAsync(Path.Combine(outputRoot,"results","sql",which==0?"fix-baseline.sql":"fix-scoped-json.sql"),await Task.FromResult(queries[which].ToQueryString()),new UTF8Encoding(false));
    Console.WriteLine("Scoped fix verified: global scalar=500 parameters; local EF.Parameter=1 JSON parameter; 60 timed results match primary fingerprint.");
}
static void AppendRow(IncrementalHash hash, byte[] b, int id, int merchant, long amount, byte status, int day)
{
    BinaryPrimitives.WriteInt32LittleEndian(b.AsSpan(0,4), id); BinaryPrimitives.WriteInt32LittleEndian(b.AsSpan(4,4), merchant);
    BinaryPrimitives.WriteInt64LittleEndian(b.AsSpan(8,8), amount); b[16] = status; BinaryPrimitives.WriteInt32LittleEndian(b.AsSpan(17,4), day); hash.AppendData(b);
}
static async Task Execute(SqlConnection c, string sql) { await using var cmd = new SqlCommand(sql, c) { CommandTimeout = 180 }; await cmd.ExecuteNonQueryAsync(); }
static async Task<object?> Scalar(SqlConnection c, string sql, params SqlParameter[] parameters) { await using var cmd = new SqlCommand(sql, c); cmd.Parameters.AddRange(parameters); return await cmd.ExecuteScalarAsync(); }

record Totals(long Count, long Amount);
record Scenario(string Band, int Size);
record Sample(string Phase,int Round,int Iteration,string Band,int Size,string Mode,double ClientMs,int Parameters,string SqlShape,string ResultHash,int Groups,long Count,long Amount);
record Client(BenchDb Db,Capture Capture);
record CapturedParameter(string Name,SqlDbType Type,int Size,object Value);
record Snapshot(string Text,CapturedParameter[] Parameters);
sealed class Capture : DbCommandInterceptor
{
    public bool Detailed { get; set; }
    public string Text { get; private set; } = "";
    public int ParameterCount { get; private set; }
    public Snapshot? Last { get; private set; }
    public override ValueTask<InterceptionResult<DbDataReader>> ReaderExecutingAsync(DbCommand command, CommandEventData eventData, InterceptionResult<DbDataReader> result, CancellationToken cancellationToken=default)
    {
        Text = command.CommandText;
        ParameterCount = command.Parameters.Count;
        // Parameter cloning is restricted to untimed warmups, not the measured path.
        if (Detailed) Last = new Snapshot(Text, command.Parameters.Cast<SqlParameter>().Select(p=>new CapturedParameter(p.ParameterName,p.SqlDbType,p.Size,p.Value)).ToArray());
        return ValueTask.FromResult(result);
    }
}
sealed class BenchDb(DbContextOptions<BenchDb> options) : DbContext(options)
{
    public DbSet<PaymentTransaction> Transactions => Set<PaymentTransaction>();
    protected override void OnModelCreating(ModelBuilder m)
    {
        m.Entity<PaymentTransaction>().ToTable("Transactions").HasKey(x=>x.Id);
        m.Entity<PaymentTransaction>().Property(x=>x.Status).HasColumnType("tinyint");
    }
}
sealed class PaymentTransaction
{
    public int Id { get; set; }
    public int MerchantId { get; set; }
    public long AmountMinor { get; set; }
    public byte Status { get; set; }
    public DateTime OccurredAt { get; set; }
}
sealed class ReportRow
{
    public int MerchantId { get; set; }
    public long Count { get; set; }
    public long Amount { get; set; }
}
