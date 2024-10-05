# camera_feed_handler.py
import logging
import time

import cv2
import numpy as np
import threading

module_logger = logging.getLogger('vector_playground.camera_feed_handler')

class CameraStream:
    def __init__(self, robot, object_detector, enable_high_resolution=True, interval_seconds=1):
        """
        Initializes the CameraStream for a robot.
        :param robot: The robot object.
        :param object_detector: The object detection instance to process the frames.
        :param enable_high_resolution: Whether to capture images in high resolution.
        """
        self.robot = robot
        self.object_detector = object_detector
        self.interval_seconds = interval_seconds
        self.enable_high_resolution = enable_high_resolution
        self.running = False
        self.camera_thread = threading.Thread(target=self._stream_camera, daemon=True)
        self.stream_image = None
        self.latest_image = None

    def start(self):
        """
        Starts the camera stream in a separate thread.
        """
        self.running = True
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Starting the camera stream...')
        self.camera_thread.start()

    def stop(self):
        """
        Stops the camera stream.
        """
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Stopping the camera stream...')
        self.running = False
        if self.camera_thread.is_alive():
            try:
                self.camera_thread.join()
            except Exception as e:
                pass
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Camera stream stopped.')

    def _stream_camera(self):
        """
        Captures frames from the robot's camera at specified intervals and processes them.
        """
        self.robot.camera.init_camera_feed()

        while self.running:

            try:
                latest_image = self.robot.camera._latest_image
            except Exception as e:
                latest_image = None
                pass

            if latest_image:
                # Convert the PIL image to a NumPy array
                frame = np.array(latest_image.raw_image)

                # Convert the image color space from RGBA to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

                # Pass the frame to the object detector for processing
                annotated_frame = self.object_detector.process_frame(frame_rgb)

                self.latest_image = annotated_frame

                # Display the annotated frame
                #cv2.imshow(f'Robot {self.robot.serial} Camera Stream', annotated_frame)

                # Check if 'q' key is pressed
                #if cv2.waitKey(1) & 0xFF == ord('q'):
                #    self.running = False
                #    break

            # Small sleep to reduce CPU usage
            time.sleep(.1)

        #cv2.destroyAllWindows()
        #self.robot.camera.close_camera_feed()