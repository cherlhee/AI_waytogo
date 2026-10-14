
- to use perceptron to oil temperature

## 1. Perceptron for oil temperature prediction
For your compressor, possible input variables are:

- Load percentage (%)
- U, V, W phase currents (A)
- Voltage (V)
- Active power (kW)
- Current oil temperature (°C)
- Temperature change over the previous 5 minutes


Single-neuron model for compressor oil temperature prediction
A single neuron computes:


$$
\hat T=w_1x_1+w_2x_2+\cdots+w_nx_n+b
$$
 
For continuous temperature prediction, use a linear output neuron rather than a step activation function.

2. Which model should you use?
Model

Oil temperature application

Single Perceptron

Classify warning vs. normal

Linear neuron

Predict temperature in °C

Multi-Layer Perceptron (MLP)

Learn nonlinear relationships and predict temperature

LSTM

Learn time-series patterns and predict future temperature

For example, you can define a target:


$$
\hat T(t+20)=f(X(t),X(t-1),\ldots)
$$



This predicts oil temperature 20 minutes into the future.

3. Python example using a Perceptron
This example uses a single linear neuron implemented with SGDRegressor to predict oil temperature.



```
import numpy as np
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

# Input: load(%), current(A), voltage(V), power(kW)
X = np.array([
    [40, 50, 380, 20],
    [50, 60, 380, 25],
    [60, 70, 380, 30],
    [70, 80, 380, 35],
    [80, 90, 380, 40],
    [90, 100, 380, 45]
])

# Example oil temperatures (°C)
y = np.array([60, 65, 70, 76, 83, 90])

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = SGDRegressor(
    max_iter=10000,
    tol=1e-6,
    random_state=42
)

model.fit(X_scaled, y)

# Predict oil temperature
new_data = np.array([[85, 95, 380, 42]])

prediction = model.predict(
    scaler.transform(new_data)
)

print("Predicted oil temperature:", prediction[0])
```



The values are illustrative, not actual compressor measurements. For reliable results, use historical compressor data with a chronological train/test split. To predict 20 minutes ahead, the target must be shifted to the temperature measured 20 minutes later.

4. My recommendation for your compressor project
Start by comparing three models:

Single linear neuron — baseline temperature prediction.

MLP with two hidden layers — nonlinear temperature prediction.

LSTM — prediction using historical sensor sequences.

Evaluate each using MAE and RMSE for temperature, and Precision, Recall, and F1 for 80°C, 85°C, and 90°C threshold warnings.

One important question: Do you want the Perceptron to predict the actual oil temperature (e.g., 85°C), or to predict whether oil temperature will exceed 80°C, 85°C, or 90°C within the next 20 minutes? The code and activation function will be different.

/////////////////
