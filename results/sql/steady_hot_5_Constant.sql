-- EF10LAB_20261109_135518_steady_hot_5_Constant

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (1, 2, 3, 4, 5)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]