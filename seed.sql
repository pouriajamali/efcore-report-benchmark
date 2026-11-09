SET NOCOUNT ON;
IF OBJECT_ID('dbo.Transactions') IS NOT NULL
    THROW 50001, 'Seed target already exists; no existing data will be replaced.', 1;
CREATE TABLE dbo.Transactions (
 Id int NOT NULL CONSTRAINT PK_Transactions PRIMARY KEY CLUSTERED,
 MerchantId int NOT NULL,
 AmountMinor bigint NOT NULL,
 Status tinyint NOT NULL,
 OccurredAt datetime2 NOT NULL
);
WITH d(v) AS (SELECT * FROM (VALUES(0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) t(v)),
 n(v) AS (
 SELECT a.v+10*b.v+100*c.v+1000*d.v+10000*e.v+100000*f.v
 FROM d a CROSS JOIN d b CROSS JOIN d c CROSS JOIN d d CROSS JOIN d e CROSS JOIN d f
 )
INSERT dbo.Transactions WITH (TABLOCK) (Id,MerchantId,AmountMinor,Status,OccurredAt)
SELECT v+1,
 CASE WHEN v<800000 THEN 1+v%1000 ELSE 1001+(v-800000)%9000 END,
 100+(CONVERT(bigint,v)*37+17)%1000000,
 CASE WHEN (v/1000+v)%10=0 THEN 0 ELSE 1 END,
 DATEADD(day,v%365,CONVERT(datetime2,'2025-01-01'))
FROM n;
CREATE INDEX IX_Transactions_MerchantId_Status ON dbo.Transactions(MerchantId,Status) INCLUDE(AmountMinor);
UPDATE STATISTICS dbo.Transactions WITH FULLSCAN;
