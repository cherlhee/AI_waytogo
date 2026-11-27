

WITH alarm_check AS (
    SELECT *,
        LAG(alarm_dt) OVER (
            PARTITION BY comcode, deviceId, std_item
            ORDER BY alarm_dt
        ) AS prev_alarm_dt
    FROM ai_alarm
    WHERE comcode = 'C00088'
)
SELECT *,
    TIMESTAMPDIFF(
        SECOND, prev_alarm_dt, alarm_dt
    ) AS diff_seconds,
    ROUND(
        TIMESTAMPDIFF(
            SECOND, prev_alarm_dt, alarm_dt
        ) / 60.0, 2
    ) AS diff_minutes
FROM alarm_check
WHERE TIMESTAMPDIFF(
    SECOND, prev_alarm_dt, alarm_dt
) < 3600
ORDER BY alarm_dt DESC
LIMIT 1000;



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