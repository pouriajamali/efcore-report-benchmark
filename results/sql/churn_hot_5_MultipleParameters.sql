DECLARE @ids1 int = 14;
DECLARE @ids2 int = 15;
DECLARE @ids3 int = 16;
DECLARE @ids4 int = 17;
DECLARE @ids5 int = 18;

-- EF10LAB_20261109_135518_churn_hot_5_MultipleParameters

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (@ids1, @ids2, @ids3, @ids4, @ids5)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]