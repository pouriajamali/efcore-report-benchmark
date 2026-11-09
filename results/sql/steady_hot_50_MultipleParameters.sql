DECLARE @ids1 int = 1;
DECLARE @ids2 int = 2;
DECLARE @ids3 int = 3;
DECLARE @ids4 int = 4;
DECLARE @ids5 int = 5;
DECLARE @ids6 int = 6;
DECLARE @ids7 int = 7;
DECLARE @ids8 int = 8;
DECLARE @ids9 int = 9;
DECLARE @ids10 int = 10;
DECLARE @ids11 int = 11;
DECLARE @ids12 int = 12;
DECLARE @ids13 int = 13;
DECLARE @ids14 int = 14;
DECLARE @ids15 int = 15;
DECLARE @ids16 int = 16;
DECLARE @ids17 int = 17;
DECLARE @ids18 int = 18;
DECLARE @ids19 int = 19;
DECLARE @ids20 int = 20;
DECLARE @ids21 int = 21;
DECLARE @ids22 int = 22;
DECLARE @ids23 int = 23;
DECLARE @ids24 int = 24;
DECLARE @ids25 int = 25;
DECLARE @ids26 int = 26;
DECLARE @ids27 int = 27;
DECLARE @ids28 int = 28;
DECLARE @ids29 int = 29;
DECLARE @ids30 int = 30;
DECLARE @ids31 int = 31;
DECLARE @ids32 int = 32;
DECLARE @ids33 int = 33;
DECLARE @ids34 int = 34;
DECLARE @ids35 int = 35;
DECLARE @ids36 int = 36;
DECLARE @ids37 int = 37;
DECLARE @ids38 int = 38;
DECLARE @ids39 int = 39;
DECLARE @ids40 int = 40;
DECLARE @ids41 int = 41;
DECLARE @ids42 int = 42;
DECLARE @ids43 int = 43;
DECLARE @ids44 int = 44;
DECLARE @ids45 int = 45;
DECLARE @ids46 int = 46;
DECLARE @ids47 int = 47;
DECLARE @ids48 int = 48;
DECLARE @ids49 int = 49;
DECLARE @ids50 int = 50;

-- EF10LAB_20261109_135518_steady_hot_50_MultipleParameters

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (@ids1, @ids2, @ids3, @ids4, @ids5, @ids6, @ids7, @ids8, @ids9, @ids10, @ids11, @ids12, @ids13, @ids14, @ids15, @ids16, @ids17, @ids18, @ids19, @ids20, @ids21, @ids22, @ids23, @ids24, @ids25, @ids26, @ids27, @ids28, @ids29, @ids30, @ids31, @ids32, @ids33, @ids34, @ids35, @ids36, @ids37, @ids38, @ids39, @ids40, @ids41, @ids42, @ids43, @ids44, @ids45, @ids46, @ids47, @ids48, @ids49, @ids50)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]