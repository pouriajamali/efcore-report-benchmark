DECLARE @ids nvarchar(4000) = N'[14,15,16,17,18]';

-- EF10LAB_20261109_135518_churn_hot_5_Parameter

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (
    SELECT [i].[value]
    FROM OPENJSON(@ids) WITH ([value] int '$') AS [i]
)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]