#### 1. install required package
`!pip install -U mediapipe`

#### 2. import mediapipe
```
import mediapipe as mp

print(mp.__version__)
print(mp.__file__)
```

#### 3. Download the Pose Landmarker model
```
!wget -O pose_landmarker_full.task \
https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
```


#### 4. initialize

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
    num_poses=3 # for detecting multiple poses;
)



# Create pose landmarker
pose = vision.PoseLandmarker.create_from_options(options)

print("Pose Landmarker initialized")

```



#### 5. test reading a movie
```
import os

input_path = "/content/fall.mp4"

print(os.path.exists(input_path))
```
```
# to convert mp4 to mjpg
!ffmpeg -y -i /content/fall.mp4 \
    -c:v mjpeg \
    -q:v 3 \
    /content/fall_converted.avi
```

#### 6. open a movie

```
import cv2

video_path = "/content/fall_converted.avi"

cap = cv2.VideoCapture(video_path)

print("Opened:", cap.isOpened())
```

```
if cap.isOpened():
    print("FPS:", cap.get(cv2.CAP_PROP_FPS))
    print("Width:", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("Height:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    ret, frame = cap.read()
    print("First frame:", ret)
```

cap.release()



#### 7. detect fall from a movie

import cv2
import mediapipe as mp
import math
from collections import deque

```
! ============================================================
! 1. Video
! ============================================================

video_path = "/content/fall_converted.avi"
output_path = "/content/fall_result.mp4"


cap = cv2.VideoCapture(video_path)


if not cap.isOpened():
    raise RuntimeError("Cannot open video")
    

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


print("FPS:", fps)
print("Size:", width, height)
```



```
! ============================================================
! 2. MediaPipe Pose Landmarker
! ============================================================


from mediapipe.tasks import python
from mediapipe.tasks.python import vision


model_path = "/content/pose_landmarker_full.task"


base_options = python.BaseOptions(
    model_asset_path=model_path
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_poses=1
)


pose = vision.PoseLandmarker.create_from_options(options)
```



```
! ============================================================
! 3. Output video
! ============================================================


fourcc = cv2.VideoWriter_fourcc(*"mp4v")

out = cv2.VideoWriter(
    output_path,
    fourcc,
    fps,
    (width, height)
)

if not out.isOpened():
    raise RuntimeError("Cannot create output video")
```



```
! ============================================================
! 4. Fall detection parameters
! ============================================================


! Number of previous frames used for comparison
HISTORY_FRAMES = 15


! Waist downward movement threshold
WAIST_DROP_THRESHOLD = 0.12


! Number of consecutive detections required
FALL_CONFIRM_FRAMES = 3

waist_history = deque(maxlen=HISTORY_FRAMES)

fall_count = 0
fall_detected = False
```



```
! ============================================================
! 5. Skeleton connections
! ============================================================


POSE_CONNECTIONS = [

    # Head
    (0, 11),
    (0, 12),

    # Shoulders
    (11, 12),

    # Left arm
    (11, 13),
    (13, 15),

    # Right arm
    (12, 14),
    (14, 16),

    # Torso
    (11, 23),
    (12, 24),
    (23, 24),

    # Left leg
    (23, 25),
    (25, 27),

    # Right leg
    (24, 26),
    (26, 28)
]

JOINTS = [
    0,
    11, 12,
    13, 14,
    15, 16,
    23, 24,
    25, 26,
    27, 28
]

```


```

! ============================================================
! 6. Read video
! ============================================================


frame_count = 0

while True:

```
    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    # --------------------------------------------------------
    # OpenCV BGR -> RGB
    # --------------------------------------------------------

    image_rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # --------------------------------------------------------
    # MediaPipe image
    # --------------------------------------------------------

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=image_rgb
    )

    # --------------------------------------------------------
    # Pose detection
    # --------------------------------------------------------

    result = pose.detect(mp_image)


    # ========================================================
    # 7. If person detected
    # ========================================================

    if result.pose_landmarks:

        landmarks = result.pose_landmarks[0]

        # ----------------------------------------------------
        # Left and right hip
        # ----------------------------------------------------

        left_hip = landmarks[23]
        right_hip = landmarks[24]

        # ----------------------------------------------------
        # Waist center
        # ----------------------------------------------------

        waist_x = (
            left_hip.x +
            right_hip.x
        ) / 2

        waist_y = (
            left_hip.y +
            right_hip.y
        ) / 2

        # ----------------------------------------------------
        # Save waist position
        # ----------------------------------------------------

        waist_history.append(waist_y)


        # ====================================================
        # 8. Calculate waist height change
        # ====================================================

        waist_drop = 0

        if len(waist_history) >= HISTORY_FRAMES:

            old_waist_y = waist_history[0]
            current_waist_y = waist_history[-1]

            # Positive = moving downward
            waist_drop = (
                current_waist_y -
                old_waist_y
            )


            # =================================================
            # 9. Fall condition
            # =================================================

            if waist_drop > WAIST_DROP_THRESHOLD:

                fall_count += 1

            else:

                fall_count = 0


            # -----------------------------------------------
            # Confirm fall
            # -----------------------------------------------

            if fall_count >= FALL_CONFIRM_FRAMES:

                fall_detected = True

        # ====================================================
        # 10. Draw waist point
        # ====================================================

        waist_px_x = int(waist_x * width)
        waist_px_y = int(waist_y * height)

        cv2.circle(
            frame,
            (waist_px_x, waist_px_y),
            8,
            (0, 255, 255),
            -1
        )


        # ====================================================
        # 11. Draw skeleton
        # ====================================================

        for start, end in POSE_CONNECTIONS:

            x1 = int(landmarks[start].x * width)
            y1 = int(landmarks[start].y * height)

            x2 = int(landmarks[end].x * width)
            y2 = int(landmarks[end].y * height)

            cv2.line(
                frame,
                (x1, y1),
                (x2, y2),
                (255, 0, 0),
                2
            )


        # ----------------------------------------------------
        # Draw joints
        # ----------------------------------------------------

        for i in JOINTS:

            x = int(landmarks[i].x * width)
            y = int(landmarks[i].y * height)

            cv2.circle(
                frame,
                (x, y),
                4,
                (0, 255, 0),
                -1
            )


        # ====================================================
        # 12. Display waist information
        # ====================================================

        cv2.putText(
            frame,
            f"Waist Y: {waist_y:.3f}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Waist Drop: {waist_drop:.3f}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )


    # ========================================================
    # 13. Fall warning
    # ========================================================

    if fall_detected:

        cv2.putText(
            frame,
            "FALL DETECTED!",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            4
        )

    else:

        cv2.putText(
            frame,
            "NORMAL",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            3
        )


    # ========================================================
    # 14. Save frame
    # ========================================================

    out.write(frame)




```
! ============================================================
! 15. Release
! ============================================================


cap.release()
out.release()

print("Processed frames:", frame_count)
print("Saved:", output_path)
```
