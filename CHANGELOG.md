# Changelog

## 0.1.0 — 9 November 2026

- Recorded synthetic financial-report comparison of three EF Core10.0.14 SQL Server
  collection translations, using one million deterministic transactions.
-1,350 primary timed observations,18 actual execution plans, generated SQL and raw counters.
-60 separate observations verify a report-level `EF.Parameter(ids)` override with the
  global context policy retained and exact matching result aggregates.
- Windows LocalDB reproduction runner, locked NuGet dependencies and evidence verifier.
- MIT license. SQL timing was measured locally; build/evidence CI does not remeasure it.
