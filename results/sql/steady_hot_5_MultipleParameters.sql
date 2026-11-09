DECLARE @ids1 int = 1;
DECLARE @ids2 int = 2;
DECLARE @ids3 int = 3;
DECLARE @ids4 int = 4;
DECLARE @ids5 int = 5;

-- EF10LAB_20261109_135518_steady_hot_5_MultipleParameters

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (@ids1, @ids2, @ids3, @ids4, @ids5)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]