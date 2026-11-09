DECLARE @ids1 int = 14;
DECLARE @ids2 int = 15;
DECLARE @ids3 int = 16;
DECLARE @ids4 int = 17;
DECLARE @ids5 int = 18;
DECLARE @ids6 int = 19;
DECLARE @ids7 int = 20;
DECLARE @ids8 int = 21;
DECLARE @ids9 int = 22;
DECLARE @ids10 int = 23;
DECLARE @ids11 int = 24;
DECLARE @ids12 int = 25;
DECLARE @ids13 int = 26;
DECLARE @ids14 int = 27;
DECLARE @ids15 int = 28;
DECLARE @ids16 int = 29;
DECLARE @ids17 int = 30;
DECLARE @ids18 int = 31;
DECLARE @ids19 int = 32;
DECLARE @ids20 int = 33;
DECLARE @ids21 int = 34;
DECLARE @ids22 int = 35;
DECLARE @ids23 int = 36;
DECLARE @ids24 int = 37;
DECLARE @ids25 int = 38;
DECLARE @ids26 int = 39;
DECLARE @ids27 int = 40;
DECLARE @ids28 int = 41;
DECLARE @ids29 int = 42;
DECLARE @ids30 int = 43;
DECLARE @ids31 int = 44;
DECLARE @ids32 int = 45;
DECLARE @ids33 int = 46;
DECLARE @ids34 int = 47;
DECLARE @ids35 int = 48;
DECLARE @ids36 int = 49;
DECLARE @ids37 int = 50;
DECLARE @ids38 int = 51;
DECLARE @ids39 int = 52;
DECLARE @ids40 int = 53;
DECLARE @ids41 int = 54;
DECLARE @ids42 int = 55;
DECLARE @ids43 int = 56;
DECLARE @ids44 int = 57;
DECLARE @ids45 int = 58;
DECLARE @ids46 int = 59;
DECLARE @ids47 int = 60;
DECLARE @ids48 int = 61;
DECLARE @ids49 int = 62;
DECLARE @ids50 int = 63;

-- EF10LAB_20261109_135518_churn_hot_50_MultipleParameters

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (@ids1, @ids2, @ids3, @ids4, @ids5, @ids6, @ids7, @ids8, @ids9, @ids10, @ids11, @ids12, @ids13, @ids14, @ids15, @ids16, @ids17, @ids18, @ids19, @ids20, @ids21, @ids22, @ids23, @ids24, @ids25, @ids26, @ids27, @ids28, @ids29, @ids30, @ids31, @ids32, @ids33, @ids34, @ids35, @ids36, @ids37, @ids38, @ids39, @ids40, @ids41, @ids42, @ids43, @ids44, @ids45, @ids46, @ids47, @ids48, @ids49, @ids50)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]