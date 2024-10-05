# object_detector.py
import logging

import cv2
import mediapipe as mp
from ultralytics import YOLO

module_logger = logging.getLogger('vector_playground.object_detection')

class ObjectDetector:
    def __init__(self, config_data, min_detection_confidence=0.68):
        """
        Initializes the ObjectDetector with MediaPipe solutions for hands and face,
        and Ultralytics YOLO model for general object detection.
        :param min_detection_confidence: Minimum confidence value ([0.0, 1.0]) for detections to be considered successful.
        """
        self.min_detection_confidence = min_detection_confidence

        # Initialize MediaPipe solutions
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands_data = []
        self.objects_data = []
        self.model_path = config_data.get("object_detection_model_path", 'var/yolo/yolov8x.pt')
        # Create instances of the solutions
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=self.min_detection_confidence
        )

        # Initialize the YOLO model (e.g., YOLOv8n for nano model)
        self.yolo_model = YOLO(self.model_path)

    def process_frame(self, frame):
        """
        Processes a frame to detect hands, faces, and objects, and annotates the detections.
        :param frame: The input frame in RGB format.
        :return: The annotated frame in BGR format (suitable for OpenCV display).
        """
        current_hand_data = []
        current_object_data = []

        # Process the frame for hand detection
        hands_result = self.hands.process(frame)

        # Convert the image color space from RGB to BGR for OpenCV drawing
        annotated_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Draw hand landmarks and collect data
        if hands_result.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(hands_result.multi_hand_landmarks):
                # Draw landmarks
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

                # Collect landmarks
                handList = []
                h, w, c = annotated_frame.shape
                for lm in hand_landmarks.landmark:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    handList.append((cx, cy))

                # Initialize upCount
                upCount = 0

                # Finger indices
                finger_tips = [8, 12, 16, 20]
                finger_pips = [6, 10, 14, 18]

                # Count fingers
                for tip, pip in zip(finger_tips, finger_pips):
                    if handList[tip][1] < handList[pip][1]:  # Finger is up
                        upCount += 1

                # Determine hand label
                handLabel = hands_result.multi_handedness[idx].classification[0].label

                # Determine hand facing direction
                if handList[17][0] > handList[5][0]:
                    handFacing = 'front'
                else:
                    handFacing = 'back'

                # Thumb processing
                if handLabel == 'Right':
                    if handFacing == 'front':
                        if handList[4][0] > handList[3][0]:
                            upCount += 1
                    else:
                        if handList[4][0] < handList[3][0]:
                            upCount += 1
                else:  # Left hand
                    if handFacing == 'front':
                        if handList[4][0] < handList[3][0]:
                            upCount += 1
                    else:
                        if handList[4][0] > handList[3][0]:
                            upCount += 1

                # Collect hand data
                hand_data = {
                    'handedness': handLabel,
                    'facing': handFacing,
                    'raised_fingers': upCount,
                    'index_finger_tip': {
                        'x': handList[8][0],
                        'y': handList[8][1]
                    }
                    # You can add more data if needed
                }
                current_hand_data.append(hand_data)

        # Perform object detection using YOLO
        # Ultralytics YOLO expects images in BGR format
        results = self.yolo_model(annotated_frame, verbose=False)

        # Iterate over the detections and draw bounding boxes and labels
        for result in results:
            for box in result.boxes:
                # Extract the bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                # Get the class ID and confidence
                class_id = int(box.cls[0])
                confidence = box.conf[0]

                # Filter out weak detections
                if confidence < self.min_detection_confidence:
                    continue

                # Get the class name
                class_name = self.yolo_model.model.names[class_id]

                # Compute center coordinates
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                # Collect object data
                object_data = {
                    'class_name': class_name,
                    'confidence': float(confidence),
                    'center': {'x': center_x, 'y': center_y}
                }
                current_object_data.append(object_data)

                # Draw the bounding box and label
                color = (0, 255, 0)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                label = f"{class_name}: {confidence * 100:.1f}%"
                cv2.putText(annotated_frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        self.objects_data = current_object_data
        self.hands_data = current_hand_data
        return annotated_frame

    def __del__(self):
        # Release resources when the object is destroyed
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()
