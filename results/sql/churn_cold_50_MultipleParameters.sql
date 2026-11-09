DECLARE @ids1 int = 5014;
DECLARE @ids2 int = 5015;
DECLARE @ids3 int = 5016;
DECLARE @ids4 int = 5017;
DECLARE @ids5 int = 5018;
DECLARE @ids6 int = 5019;
DECLARE @ids7 int = 5020;
DECLARE @ids8 int = 5021;
DECLARE @ids9 int = 5022;
DECLARE @ids10 int = 5023;
DECLARE @ids11 int = 5024;
DECLARE @ids12 int = 5025;
DECLARE @ids13 int = 5026;
DECLARE @ids14 int = 5027;
DECLARE @ids15 int = 5028;
DECLARE @ids16 int = 5029;
DECLARE @ids17 int = 5030;
DECLARE @ids18 int = 5031;
DECLARE @ids19 int = 5032;
DECLARE @ids20 int = 5033;
DECLARE @ids21 int = 5034;
DECLARE @ids22 int = 5035;
DECLARE @ids23 int = 5036;
DECLARE @ids24 int = 5037;
DECLARE @ids25 int = 5038;
DECLARE @ids26 int = 5039;
DECLARE @ids27 int = 5040;
DECLARE @ids28 int = 5041;
DECLARE @ids29 int = 5042;
DECLARE @ids30 int = 5043;
DECLARE @ids31 int = 5044;
DECLARE @ids32 int = 5045;
DECLARE @ids33 int = 5046;
DECLARE @ids34 int = 5047;
DECLARE @ids35 int = 5048;
DECLARE @ids36 int = 5049;
DECLARE @ids37 int = 5050;
DECLARE @ids38 int = 5051;
DECLARE @ids39 int = 5052;
DECLARE @ids40 int = 5053;
DECLARE @ids41 int = 5054;
DECLARE @ids42 int = 5055;
DECLARE @ids43 int = 5056;
DECLARE @ids44 int = 5057;
DECLARE @ids45 int = 5058;
DECLARE @ids46 int = 5059;
DECLARE @ids47 int = 5060;
DECLARE @ids48 int = 5061;
DECLARE @ids49 int = 5062;
DECLARE @ids50 int = 5063;

-- EF10LAB_20261109_135518_churn_cold_50_MultipleParameters

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (@ids1, @ids2, @ids3, @ids4, @ids5, @ids6, @ids7, @ids8, @ids9, @ids10, @ids11, @ids12, @ids13, @ids14, @ids15, @ids16, @ids17, @ids18, @ids19, @ids20, @ids21, @ids22, @ids23, @ids24, @ids25, @ids26, @ids27, @ids28, @ids29, @ids30, @ids31, @ids32, @ids33, @ids34, @ids35, @ids36, @ids37, @ids38, @ids39, @ids40, @ids41, @ids42, @ids43, @ids44, @ids45, @ids46, @ids47, @ids48, @ids49, @ids50)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]