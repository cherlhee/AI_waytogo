



SELECT *
FROM ai_analysis
WHERE input_time >= '2026-11-07 00:00:00'
  AND input_time <  '2026-11-08 00:00:00'
ORDER BY input_time ASC;




SELECT
    comcode,
    deviceId,
    COUNT(*) AS total_count,
    MIN(input_time) AS first_time,
    MAX(input_time) AS last_time
FROM ai_data
WHERE input_time >= '2026-11-01 00:00:00'
  AND input_time <  '2026-11-07 00:00:00'
GROUP BY comcode, deviceId;