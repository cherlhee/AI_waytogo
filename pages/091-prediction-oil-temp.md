
## HOW to use perceptron to oil temperature

Algorithm for oil temperature prediction
- Confidence Factor of Rule-base
- Fuzzy of Rule-base
- Single Perceptron
- Random Forest
- Multi-Layer Perceptron (MLP)
- LSTM



### 1. Single-neuron model for compressor oil temperature prediction
A single neuron computes:


$$
\hat T=w_1x_1+w_2x_2+\cdots+w_nx_n+b
$$
 
For example, you can define a target:

$$
\hat T(t+20)=f(X(t),X(t-1),\ldots)
$$


- Load percentage (%)
- U, V, W phase currents (A)
- Voltage (V)
- Active power (kW)
- Current oil temperature (°C)
- Temperature change over the previous 5 minutes

 
This predicts oil temperature 20 minutes into the future.



### 2. Python example using a Perceptron
This example uses a single linear neuron implemented with SGDRegressor to predict oil temperature.



```python
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

``` >>>>> Predicted oil temperature: 85.80012949784121 ```


The values are illustrative, not actual compressor measurements. For reliable results, use historical compressor data with a chronological train/test split. To predict 20 minutes ahead, the target must be shifted to the temperature measured 20 minutes later.

