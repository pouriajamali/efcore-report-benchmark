DECLARE @ids nvarchar(4000) = N'[5001,5002,5003,5004,5005]';

-- EF10LAB_20261109_135518_steady_cold_5_Parameter

SELECT [t].[MerchantId], COUNT_BIG(*) AS [Count], COALESCE(SUM([t].[AmountMinor]), CAST(0 AS bigint)) AS [Amount]
FROM [Transactions] AS [t]
WHERE [t].[Status] = CAST(1 AS tinyint) AND [t].[MerchantId] IN (
    SELECT [i].[value]
    FROM OPENJSON(@ids) WITH ([value] int '$') AS [i]
)
GROUP BY [t].[MerchantId]
ORDER BY [t].[MerchantId]