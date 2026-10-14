### 1. Install the required package


`!pip install -U mediapipe`


```
import mediapipe as mp

print(mp.__version__)
print(mp.__file__)
```


### 2. Download the Pose Landmarker model

```
!wget -O pose_landmarker_full.task \
https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
```

### 3. load the model

```

import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Model configuration
base_options = python.BaseOptions(
    model_asset_path="pose_landmarker_full.task"
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_poses=1
)

# Create pose landmarker
pose = vision.PoseLandmarker.create_from_options(options)

print("Pose Landmarker initialized")
```






### 4. Process an image


```
import cv2
import mediapipe as mp
from google.colab.patches import cv2_imshow


image = cv2.imread("person.jpg")


#cv2.imshow("Image", image)
cv2_imshow(image)



# OpenCV BGR -> RGB
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
cv2_imshow(image_rgb)


# Convert to MediaPipe Image
mp_image = mp.Image(
    image_format=mp.ImageFormat.SRGB,
    data=image_rgb
)

# Detect pose
result = pose.detect(mp_image)

print(result)




# to get skeleton points;
if result.pose_landmarks:
    landmarks = result.pose_landmarks[0]

    for i, landmark in enumerate(landmarks):
        print(
            i,
            "x =", landmark.x,
            "y =", landmark.y,
            "z =", landmark.z,
            "visibility =", landmark.visibility
        )

```


.522736132144928 y = 0.8004016280174255 z = 0.3189942240715027 visibility = 0.7600340247154236
30 x = 0.47524139285087585 y = 0.8015855550765991 z = 0.25167137384414673 visibility = 0.6014643311500549
31 x = 0.5397322773933411 y = 0.8321723341941833 z = 0.06803754717111588 visibility = 0.9372886419296265
32 x = 0.48818570375442505 y = 0.8341379165649414 z = -0.01094707753509283 visibility = 0.9215171337127686



```
0  = Nose
11 = Left Shoulder
12 = Right Shoulder
13 = Left Elbow
14 = Right Elbow
15 = Left Wrist
16 = Right Wrist
23 = Left Hip
24 = Right Hip
25 = Left Knee
26 = Right Knee
27 = Left Ankle
28 = Right Ankle
```

```
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),

    (9, 10),

    (11, 12),

    (11, 13), (13, 15),
    (15, 17), (15, 19), (15, 21),

    (12, 14), (14, 16),
    (16, 18), (16, 20), (16, 22),

    (11, 23),
    (12, 24),

    (23, 24),

    (23, 25), (25, 27),
    (27, 29), (27, 31),

    (24, 26), (26, 28),
    (28, 30), (28, 32)
]
```


```
if result.pose_landmarks:

    landmarks = result.pose_landmarks[0]

    h, w, _ = image.shape

    # Draw landmarks
    for landmark in landmarks:

        x = int(landmark.x * w)
        y = int(landmark.y * h)

        cv2.circle(
            image,
            (x, y),
            15, #circle size
            (0, 255, 0),
            -1
        )

    # Draw skeleton connections
    for start, end in POSE_CONNECTIONS:

        x1 = int(landmarks[start].x * w)
        y1 = int(landmarks[start].y * h)

        x2 = int(landmarks[end].x * w)
        y2 = int(landmarks[end].y * h)

        cv2.line(
            image,
            (x1, y1),
            (x2, y2),
            (255, 0, 0),
            15 # line thickness
        )
```
```


import matplotlib.pyplot as plt

plt.figure(figsize=(10, 8))
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.axis("off")
plt.show()
```

![](https://static.wikidocs.net/images/page/445736/image_202610091929.png)
