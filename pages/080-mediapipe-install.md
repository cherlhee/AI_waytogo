1. Install the required package
```
!pip install -U mediapipe

import mediapipe as mp

print(mp.__version__)
print(mp.__file__)
```

2. Download the Pose Landmarker model

```
!wget -O pose_landmarker_full.task \
https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
```


3. process an image

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




import cv2
from google.colab.patches import cv2_imshow




image = cv2.imread("lenna.png")


# cv2.imshow("Image", image)
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

```
