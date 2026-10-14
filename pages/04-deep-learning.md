- neural network with more than two hidden layers

![](https://static.wikidocs.net/images/page/448935/image_202610100606.png)

Each neuron calculates a weighted sum and applies an activation function:
$$
z=\sum_i w_i x_i+b
$$

$$
\hat y=f(z)
$$

- $x_i$: input data
- $w_i$: weight
- $b$: bias
- $\hat y$: predicted output
- 

- backpropagation training
![](https://static.wikidocs.net/images/page/448935/image_202610100610.png)




$$
\boxed{w_{jk}(p+1)=w_{jk}(p)+\Delta w_{jk}(p)}
$$

$w_{jk}(p+1) : $	Updated weight after the next training step
$w_{jk}(p) : $	Current weight
$\Delta w_{jk}(p) : $	Change applied to the weight
$p : $	Training-step or iteration index
$j,k : $	Indices identifying the neurons connected by the weight


$$
\Delta w_{jk}(p)=\alpha \times y_j(p)\times \delta_k(p)
$$

$\Delta w_{jk}(p) : $	Change in the connection weight
$\alpha : $	Learning rate
$y_j(p) : $	Output of the sending neuron j
$\delta_k(p) : $	error gradient for neuron k
$p : $	Training iteration or pattern index

$$

\delta_k(p)=
\frac{\partial y_k(p)}{\partial X_k(p)}
\times e_k(p)
$$

The equation means:
Local error signal = derivative of the neuron's output × prediction error.

$\delta_k(p) : $	Local error signal for neuron \(k\)
$y_k(p) : $	Actual output of neuron \(k\)
$X_k(p) : $	Net input to neuron \(k\), before its activation function
$\frac{\partial y_k}{\partial X_k} : $	Derivative of the activation function
$e_k(p) : $	Desired output minus actual output
$p : $ Training pattern or iteration index


the error signal in a neural network during training
$$
e_k(p)=y_{d,k}(p)-y_k(p)
$$

![](https://static.wikidocs.net/images/page/448935/image_202610100645.png)




```

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 1. XOR training data
# ============================================================

X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])

T = np.array([0, 1, 1, 0])


# ============================================================
# 2. Sigmoid function
# ============================================================

def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# ============================================================
# 3. Initialize weights and thresholds
# ============================================================

np.random.seed(42)

w13 = np.random.uniform(-1, 1)
w23 = np.random.uniform(-1, 1)

w14 = np.random.uniform(-1, 1)
w24 = np.random.uniform(-1, 1)

w35 = np.random.uniform(-1, 1)
w45 = np.random.uniform(-1, 1)

# Thresholds (constant input = -1)
theta3 = np.random.uniform(-1, 1)
theta4 = np.random.uniform(-1, 1)
theta5 = np.random.uniform(-1, 1)

alpha = 0.5
epochs = 30000

loss_history = []


# ============================================================
# 4. Training
# ============================================================

for epoch in range(epochs):

    total_error = 0

    for p in range(4):

        x1, x2 = X[p]
        target = T[p]

        # ----------------------------------------------------
        # STEP 1: Forward propagation
        # ----------------------------------------------------

        # Hidden neuron 3
        net3 = x1*w13 + x2*w23 - theta3
        y3 = sigmoid(net3)

        # Hidden neuron 4
        net4 = x1*w14 + x2*w24 - theta4
        y4 = sigmoid(net4)

        # Output neuron 5
        net5 = y3*w35 + y4*w45 - theta5
        y5 = sigmoid(net5)

        # ----------------------------------------------------
        # STEP 2: Calculate error
        # ----------------------------------------------------

        error = target - y5

        total_error += 0.5 * error**2

        # ----------------------------------------------------
        # STEP 3: Output neuron delta
        # ----------------------------------------------------

        delta5 = y5 * (1 - y5) * error

        # ----------------------------------------------------
        # STEP 4: Hidden neuron deltas
        # Use current weights before updating
        # ----------------------------------------------------

        delta3 = y3 * (1 - y3) * delta5 * w35

        delta4 = y4 * (1 - y4) * delta5 * w45

        # ----------------------------------------------------
        # STEP 5: Weight updates
        # ----------------------------------------------------

        # Hidden -> Output
        w35 += alpha * y3 * delta5
        w45 += alpha * y4 * delta5

        # Input -> Hidden
        w13 += alpha * x1 * delta3
        w23 += alpha * x2 * delta3

        w14 += alpha * x1 * delta4
        w24 += alpha * x2 * delta4

        # ----------------------------------------------------
        # STEP 6: Threshold updates
        # Constant input = -1
        # ----------------------------------------------------

        theta3 -= alpha * delta3
        theta4 -= alpha * delta4
        theta5 -= alpha * delta5

    loss_history.append(total_error)

    if epoch % 3000 == 0:
        print(f"Epoch {epoch:5d}, SSE={total_error:.6f}")


# ============================================================
# 5. Test trained network
# ============================================================

print("\nXOR Test Results")
print("-" * 55)

correct = 0

for p in range(4):

    x1, x2 = X[p]

    y3 = sigmoid(x1*w13 + x2*w23 - theta3)
    y4 = sigmoid(x1*w14 + x2*w24 - theta4)

    y5 = sigmoid(y3*w35 + y4*w45 - theta5)

    prediction = int(y5 >= 0.5)

    if prediction == T[p]:
        correct += 1

    print(
        f"Input=({x1},{x2}) "
        f"Target={T[p]} "
        f"Output={y5:.4f} "
        f"Prediction={prediction}"
    )

print(f"\nAccuracy = {correct/4*100:.1f}%")


# ============================================================
# 6. Print trained weights and thresholds
# ============================================================

print("\nFinal Weights")
print("-" * 30)

for name, value in [
    ("w13", w13), ("w23", w23),
    ("w14", w14), ("w24", w24),
    ("w35", w35), ("w45", w45),
    ("theta3", theta3),
    ("theta4", theta4),
    ("theta5", theta5)
]:
    print(f"{name:8s} = {value:.6f}")


# ============================================================
# 7. Plot training error
# ============================================================

plt.figure(figsize=(8, 4))
plt.plot(loss_history)
plt.xlabel("Epoch")
plt.ylabel("Sum of Half-Squared Errors")
plt.title("XOR Backpropagation Training")
plt.grid(True)
plt.show()


```

Below is a Python implementation using NumPy, following the equations shown in the pages. It does not use TensorFlow or PyTorch, so you can examine every calculation.
1. Equations from the uploaded pages
Forward propagation (순전파)
$$
y_k(p)=\operatorname{sigmoid}\left(\sum_{i=1}^{m}x_i(p)w_{ik}(p)-\theta_k\right)
$$

Output layer error
$$
\delta_k(p)=y_k(p)[1-y_k(p)]e_k(p)
$$

where \(e_k(p)=d_k(p)-y_k(p)\).
Output layer weight update
$$
\Delta w_{ik}(p)=\alpha x_i(p)\delta_k(p)
$$

Hidden layer error
$$
\delta_j(p)=y_j(p)[1-y_j(p)]
\sum_{k=1}^{L}\delta_k(p)w_{jk}(p)
$$

Hidden layer weight update
$$
\Delta w_{ij}(p)=\alpha x_i(p)\delta_j(p)
$$

New weights
$$
w_{ij}(p+1)=w_{ij}(p)+\Delta w_{ij}(p)
$$

![](https://static.wikidocs.net/images/page/448935/image_202610130555_xNWG6RU.jpeg)

![](https://static.wikidocs.net/images/page/448935/image_202610130555.jpeg)

![](https://static.wikidocs.net/images/page/448935/image_202610130555_bR0DIJ0.jpeg)

The following code implements all five equations, including the bias terms corresponding to \(-\theta\).
2. Complete Python code
Download Python code — backpropagation_pages33_35.py
The example uses this neural network:

The code includes:
- 2 input neurons, 2 hidden neurons, 1 output neuron
- Sigmoid activation function
- Forward propagation
- Output and hidden-layer delta calculations
- Weight and bias updates
- 10,000 training epochs
- Error graph
3. Training results
The example learns the XOR problem.
Input \(x_1,x_2\)	Target	Predicted output
0, 0	0	0.04561
0, 1	1	0.94706
1, 0	1	0.95860
1, 1	0	0.04039
Tr



```
import numpy as np
import matplotlib.pyplot as plt

# Backpropagation example: 2 inputs -> 2 hidden neurons -> 1 output
# Equations from pages 33-35; bias b = -theta.
np.set_printoptions(precision=5, suppress=True)

X = np.array([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
target = np.array([[0.], [1.], [1.], [0.]])  # XOR
alpha = 0.5
epochs = 10000
rng = np.random.default_rng(7)
W1 = rng.uniform(-1, 1, (2, 2))
b1 = np.zeros((1, 2))
W2 = rng.uniform(-1, 1, (2, 1))
b2 = np.zeros((1, 1))

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))

loss_history = []
for epoch in range(epochs):
    # Forward pass: y = sigmoid(sum(x*w) - theta)
    hidden = sigmoid(X @ W1 + b1)
    output = sigmoid(hidden @ W2 + b2)

    # Output delta: delta_k = y_k * (1-y_k) * (target-y_k)
    error = target - output
    delta_output = output * (1.0 - output) * error

    # Hidden delta: delta_j = y_j*(1-y_j)*sum(delta_k*w_jk)
    # Use OLD W2 before any weight updates.
    delta_hidden = hidden * (1.0 - hidden) * (delta_output @ W2.T)

    # Weight increments: Delta_w = alpha * input * delta
    # Mean over samples is used for batch gradient descent.
    dW2 = alpha * hidden.T @ delta_output / len(X)
    db2 = alpha * np.mean(delta_output, axis=0, keepdims=True)
    dW1 = alpha * X.T @ delta_hidden / len(X)
    db1 = alpha * np.mean(delta_hidden, axis=0, keepdims=True)

    W2 += dW2
    b2 += db2
    W1 += dW1
    b1 += db1

    loss = 0.5 * np.mean(error**2)
    loss_history.append(loss)
    if (epoch + 1) % 1000 == 0:
        print(f'Epoch {epoch+1:5d} | Mean half-squared error: {loss:.6f}')

hidden = sigmoid(X @ W1 + b1)
prediction = sigmoid(hidden @ W2 + b2)
print('\nInput | Target | Prediction | Class')
for x, t, p in zip(X, target[:, 0], prediction[:, 0]):
    print(f'{x.astype(int)} | {int(t)} | {p:.5f} | {int(p >= 0.5)}')
print('\nW1:\n', W1, '\nb1:', b1, '\nW2:\n', W2, '\nb2:', b2)

plt.plot(np.arange(1, epochs + 1), loss_history)
plt.xlabel('Epoch')
plt.ylabel('Mean half-squared error')
plt.title('Backpropagation training loss')
plt.grid(True)
plt.tight_layout()
plt.savefig('/mnt/data/backpropagation_loss.png', dpi=160)
plt.show()
```

![](https://static.wikidocs.net/images/page/448935/image_202610130622.png)
