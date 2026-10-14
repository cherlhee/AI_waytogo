# 3-1. Perceptron

#### 1. AND 게이트 퍼셉트론


```
import numpy as np

# 입력 데이터
X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])
print(X.shape)
print(X)


# AND 정답
y = np.array([0, 0, 0, 1])
print(y.shape)
print(y)


# 가중치와 편향 초기화
w = [0.3, -0.1]
print(w)

# 학습률
lr = 0.1

# 활성화 함수
def step(x):
    return 1 if x >= 0.1999 else 0


    

# 학습
# 학습
w = [0.3, -0.1]

for epoch in range(5):
    #print(f"w={w}")
    print('*'*70)

    for i in range(len(X)):
        print(f"-- X={X[i]}")


        # 가중합
        z = np.dot(X[i], w) 

        print(f"-- z={z}")

        # 예측
        y_pred = step(z)
        print(f"-- y_pred={y_pred}")

        # 오차
        error = y[i] - y_pred
        print(f"-- error={error}")

        # 가중치 업데이트
        w = w + lr * error * X[i]
        print(f" /////////////// w={w}")




    print(f"epoch={epoch+1}, w={w}")

```
**********************************************************************
-- X=[0 0]
-- z=0.0
-- y_pred=0
-- error=0
 /////////////// w=[ 0.3 -0.1]
-- X=[0 1]
-- z=-0.1
-- y_pred=0
-- error=0
 /////////////// w=[ 0.3 -0.1]
-- X=[1 0]
-- z=0.3
-- y_pred=1
-- error=-1
 /////////////// w=[ 0.2 -0.1]
-- X=[1 1]
-- z=0.09999999999999998
-- y_pred=0
-- error=1
 /////////////// w=[0.3 0. ]
epoch=1, w=[0.3 0. ]
**********************************************************************
-- X=[0 0]
-- z=0.0
-- y_pred=0
-- error=0
 /////////////// w=[0.3 0. ]
-- X=[0 1]
-- z=0.0
-- y_pred=0
-- error=0
 /////////////// w=[0.3 0. ]
-- X=[1 0]
-- z=0.3
-- y_pred=1
-- error=-1
 /////////////// w=[0.2 0. ]
-- X=[1 1]
-- z=0.19999999999999998
-- y_pred=1
-- error=0
 /////////////// w=[0.2 0. ]
epoch=2, w=[0.2 0. ]
**********************************************************************
-- X=[0 0]
-- z=0.0
-- y_pred=0
-- error=0
 /////////////// w=[0.2 0. ]
-- X=[0 1]
-- z=0.0
-- y_pred=0
-- error=0
 /////////////// w=[0.2 0. ]
-- X=[1 0]
-- z=0.19999999999999998
-- y_pred=1
-- error=-1
 /////////////// w=[0.1 0. ]
-- X=[1 1]
-- z=0.09999999999999998
-- y_pred=0
-- error=1
 /////////////// w=[0.2 0.1]



```
# 테스트
print("\n결과")
print(f"w={w}")

for x in X:
    z = np.dot(x, w) + b
    prediction = step(z)

    print(
        f"{x} -> {prediction}"
    )
```


결과
w=[0.1 0.1]
[0 0] -> 0
[0 1] -> 0
[1 0] -> 0
[1 1] -> 0



#### 2. 핵심 원리

뉴런의 출력

$$ 
Y=step \left [ \sum_{i=1}^n {x_i w_i} -\theta \right ]
$$

![](https://static.wikidocs.net/images/page/446635/image_202610100012.png)

단층 퍼셉트론

![](https://static.wikidocs.net/images/page/446635/image_202610100014.png)


학습할 때는

$$ 
w_i (p+1) = w_i (p) + \vartriangle w_i (p) 
$$
$$ 
\boxed{\vartriangle w_i (p) = \alpha \times x_i (p) \times e(p) }
$$
$$ 
e(p) = Y_d (p)- Y(p) 
$$




![](https://static.wikidocs.net/images/page/446635/image_202610100600.png)

입력 → 가중합 → 예측 → 오차 계산 → 가중치 수정

과정을 반복하는 것이 퍼셉트론입니다.




### 3. 퍼셉트론 예제


- 퀴즈; OR 게이트 - 퍼셉트론
```

import numpy as np

# 입력 데이터
X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])

print(X.shape)
print(X)


# OR gate 정답
y = np.array([0, 1, 1, 1])

print(y.shape)
print(y)


# 가중치와 편향 초기화
w = [0.3, -0.1]


# 학습률
lr = 0.1

print(w)



# 활성화 함수
def step(x):
    return 1 if x >= 0.1999 else 0





# 학습
w = [0.3, -0.1]

for epoch in range(5):
    #print(f"w={w}")
    print('*'*70)

    for i in range(len(X)):
        print(f"-- X={X[i]}")


        # 가중합
        z = np.dot(X[i], w)

        print(f"-- z={z}")

        # 예측
        y_pred = step(z)
        print(f"-- y_pred={y_pred}")

        # 오차
        error = y[i] - y_pred
        print(f"-- error={error}")

        # 가중치 업데이트
        w = w + lr * error * X[i]
        print(f" /////////////// w={w}")




    print(f"epoch={epoch+1}, w={w}")




# 테스트
print("\n********** 테스트 결과 : ")
print(f"w={w}")

for x in X:
    z = np.dot(x, w)
    prediction = step(z)

    print(
        f"{x} -> {prediction}"
    )

```


********** 테스트 결과 : 
w=[0.3 0.2]
[0 0] -> 0
[0 1] -> 1
[1 0] -> 1
[1 1] -> 1



- Quiz; XOR gate 구현하기

```
import numpy as np

# 입력 데이터
X = np.array([
    [0, 0],
    [0, 1],
    [1, 0],
    [1, 1]
])

print(X.shape)
print(X)


# XOR gate 정답
y = np.array([0, 1, 1, 0])

print(y.shape)
print(y)


# 가중치와 편향 초기화
w = [0.3, -0.1]


# 학습률
lr = 0.1

print(w)



# 활성화 함수
def step(x):
    return 1 if x >= 0.1999 else 0





# 학습
w = [0.3, -0.1]

for epoch in range(10):
    #print(f"w={w}")
    print('*'*70)

    for i in range(len(X)):
        print(f"-- X={X[i]}")


        # 가중합
        z = np.dot(X[i], w)

        print(f"-- z={z}")

        # 예측
        y_pred = step(z)
        print(f"-- y_pred={y_pred}")

        # 오차
        error = y[i] - y_pred
        print(f"-- error={error}")

        # 가중치 업데이트
        w = w + lr * error * X[i]
        print(f" /////////////// w={w}")




    print(f"epoch={epoch+1}, w={w}")




# 테스트
print("\n********** 테스트 결과 : ")
print(f"w={w}")

for x in X:
    z = np.dot(x, w)
    prediction = step(z)

    print(
        f"{x} -> {prediction}"
    )
print("??? error: could not solve")
```


**********************************************************************
-- X=[0 0]
-- z=0.0
-- y_pred=0
-- error=0
 /////////////// w=[ 0.1 -0.1]
-- X=[0 1]
-- z=-0.1
-- y_pred=0
-- error=1
 /////////////// w=[0.1 0. ]
-- X=[1 0]
-- z=0.09999999999999998
-- y_pred=0
-- error=1
 /////////////// w=[0.2 0. ]
-- X=[1 1]
-- z=0.19999999999999998
-- y_pred=1
-- error=-1
 /////////////// w=[ 0.1 -0.1]
epoch=9, w=[ 0.1 -0.1]
**********************************************************************
-- X=[0 0]
-- z=0.0
-- y_pred=0
-- error=0
 /////////////// w=[ 0.1 -0.1]
-- X=[0 1]
-- z=-0.1
-- y_pred=0
-- error=1
 /////////////// w=[0.1 0. ]
-- X=[1 0]
-- z=0.09999999999999998
-- y_pred=0
-- error=1
 /////////////// w=[0.2 0. ]
-- X=[1 1]
-- z=0.19999999999999998
-- y_pred=1
-- error=-1
 /////////////// w=[ 0.1 -0.1]
epoch=10, w=[ 0.1 -0.1]

********** 테스트 결과 : 
w=[ 0.1 -0.1]
[0 0] -> 0
[0 1] -> 0
[1 0] -> 0
[1 1] -> 0
??? error: could not solve




-  온도와 압력으로 정상(0) / 이상(1)을 판단하는 퍼셉트론

```
import numpy as np

# 입력 데이터
# [온도, 압력]
X = np.array([
    [30, 2],
    [35, 2.5],
    [40, 3],
    [80, 6],
    [90, 7]
])

# 정답
# 0 = 정상
# 1 = 이상
y = np.array([0, 0, 0, 1, 1])

# 가중치 초기화
w = np.zeros(2)
b = 0

# 학습률
lr = 0.01


# 계단 함수
def step(x):
    if x >= 0:
        return 1
    else:
        return 0


# 퍼셉트론 학습
for epoch in range(100):

    for i in range(len(X)):

        # ① 가중합
        z = np.dot(X[i], w) + b

        # ② 예측
        prediction = step(z)

        # ③ 오차
        error = y[i] - prediction

        # ④ 가중치 수정
        w = w + lr * error * X[i]

        # ⑤ 편향 수정
        b = b + lr * error


print("학습 완료")
print("가중치 :", w)
print("편향 :", b)


# 테스트
print("\n테스트")

test_data = np.array([
    [32, 2.1],
    [85, 6.5]
])

for x in test_data:

    z = np.dot(x, w) + b
    result = step(z)

    print(
        f"온도={x[0]}, 압력={x[1]} "
        f"-> {'이상' if result == 1 else '정상'}"
    )

```
학습 완료
가중치 : [0.   0.01]
편향 : -0.03

테스트
온도=32.0, 압력=2.1 -> 정상
온도=85.0, 압력=6.5 -> 이상

