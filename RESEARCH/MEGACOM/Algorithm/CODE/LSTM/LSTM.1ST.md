

==🔴make a full code==
==🔴I've prepared the **complete updated LSTM prediction program**, based on your uploaded lstm_predict.py.==



### Download

### 1. Functions included

|Function|Description|
|---|---|
|get_latest()|Retrieve the latest sensor data from ai_data|
|get_history()|Retrieve historical sensor data for LSTM|
|write_results()|Save predictions for 10, 30, 60, and 120 minutes|
|update_actuals()|Retrieve actual temperatures at prediction target times|
|log_metrics()|Calculate MAE and RMSE for each prediction horizon|
|integrated_gradients()|Calculate feature contributions|

The program retains your existing LSTM model loading, feature processing, and feature-importance calculations.

### 2. Database values

The program uses the following relationships:

|Column|Source or calculation|
|---|---|
|oil_temp_current|ai_data.io003 at input_time|
|lstm_prediction|LSTM prediction|
|oil_temp_actual|ai_data.io003 at prediction_target_time|
|prediction_error|lstm_prediction - oil_temp_actual|
|MAE|Average absolute prediction error|
|RMSE|Root mean squared prediction error|

MAE and RMSE are calculated separately for each prediction horizon and displayed in the logs. They are **not stored in additional database columns**.

### 3. Automatic actual-temperature updates

For example, when the prediction is generated at 10:00:

|Horizon|Target time|Actual-temperature update|
|---|---|---|
|10 minutes|10:10|After target time|
|30 minutes|10:30|After target time|
|60 minutes|11:00|After target time|
|120 minutes|12:00|After target time|

The program searches for the nearest sensor measurement within **±5 seconds** of the target time.

It waits until the latest available sensor timestamp is at least five seconds beyond the target before finalizing the match. If no valid measurement is found, oil_temp_actual remains NULL.

### 4. Required MySQL columns

Before running the program, ensure that ai_lstm_r contains:

```
oil_temp_current DECIMAL(10,2)
oil_temp_actual DECIMAL(10,2)
prediction_error DECIMAL(10,2)
```

To add any missing columns, use ALTER TABLE. Do not add columns that already exist.

### 5. Execution

Run once:

```
python lstm_predict_full.py --once
```

Continuous operation, checking every five seconds:

```
python lstm_predict_full.py --interval 5
```

The program uses your existing config.py, lstm_features.py, and trained LSTM models.

### 6. MAE and RMSE calculation

The program calculates:

MAE=1N∑i=1N∣T^i−Ti∣MAE=N1​i=1∑N​∣T^i​−Ti​∣RMSE=1N∑i=1N(T^i−Ti)2RMSE=N1​i=1∑N​(T^i​−Ti​)2​

These metrics use completed predictions only.

**Important before production use:** The code has passed Python syntax validation, but I have not executed it against your MySQL database or trained models. Also, the existing ON DUPLICATE KEY UPDATE behavior requires an appropriate unique key to prevent duplicate prediction records. The actual-temperature matching assumes ai_data.input_time uses the format YYYY-MM-DD HH:MM:SS.

lstm_predict_full.py코드