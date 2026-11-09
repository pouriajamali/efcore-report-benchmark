-- EF10LAB_20261109_135518_churn_cold_5_Constant

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (5014, 5015, 5016, 5017, 5018)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]