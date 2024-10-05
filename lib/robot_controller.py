import logging
import threading
import time
from anki_vector import behavior

from lib.audio_controller import AudioController
from lib.camera_feed_handler import CameraStream
from lib.intent_controller import IntentController
from lib.movement_controller import MovementController
from lib.object_detection_handler import ObjectDetector
from lib.status_handler import StatusHandler
from lib.task_manager import TaskManager

module_logger = logging.getLogger('vector_playground.robot_controller')

class RobotController:
    def __init__(self, robot, config_data, intent_loader, on_control_lost_callback=None):
        """
        Initializes the robot controller.
        :param robot: The robot object.
        :param on_control_lost_callback: A callback function to call when control is lost.
        """

        self.robot = robot
        self.robot.intent_data = {}
        self.on_control_lost_callback = on_control_lost_callback
        self.control_lost_listener_started = False
        self.status_handler = StatusHandler(self.robot)
        self.robot.status_handler = self.status_handler
        self.object_detector = ObjectDetector(config_data)
        self.camera_stream = CameraStream(self.robot, self.object_detector)
        self.movement_controller = MovementController(self.robot)
        self.robot.movement_controller = self.movement_controller
        self.audio_controller = AudioController(self.robot)
        self.robot.audio_controller = self.audio_controller
        self.intent_controller = IntentController(self.robot, intent_loader)
        self.task_manager = TaskManager(self.robot)

        self.last_task_time = time.time()
        self.running = False
        self.control_thread = threading.Thread(target=self._control_loop)
        self.behavior_thread = threading.Thread(target=self._behavior_control)

    def start(self):
        """
        Starts the robot's main control loop and the camera stream.
        """
        self.running = True
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Starting Robot Controller')
        self.control_thread.start()
        self.camera_stream.start()
        self.task_manager.start()
        self.status_handler.start()
        if not self.control_lost_listener_started:
            self.robot.conn.loop.create_task(self._on_control_lost())
            self.control_lost_listener_started = True

    def stop(self):
        """
        Stops the camera stream and any ongoing tasks.
        """
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Stopping Robot Controller')
        self.running = False
        self.control_lost_listener_started = False

        if self.control_thread is not None and self.control_thread.is_alive():
            self.control_thread.join()

        if self.camera_stream:
            self.camera_stream.stop()

        self.task_manager.stop()
        self.status_handler.stop()

    def _control_loop(self):
        """
        The main control loop of the robot, which manages actions and tasks.
        """
        while self.running:
            # Check if it's time for a new random task (e.g., every 5 seconds)
            if time.time() - self.last_task_time > 15:
                # self.task_manager.perform_random_task()
                # self.last_task_time = time.time()
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Gyroscope: {self.status_handler.gyroscope.x}x {self.status_handler.gyroscope.y}y {self.status_handler.gyroscope.z}z')
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Head Angle: {self.status_handler.head_angle}')
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Lift Height: {self.status_handler.lift_height}')
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Proximity: {self.status_handler.proximity.distance.distance_mm}')
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Accelerometer: {self.status_handler.accelerometer}')
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Position: {self.status_handler.position}')
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Current Status: {self.status_handler.current_statuses}')
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Objects Detected: {self.object_detector.objects_data}')
                module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Hands Detected: {self.object_detector.hands_data}')
                self.last_task_time = time.time()

            time.sleep(.1)

    async def _on_control_lost(self):
        while True:
            await self.robot.conn.control_lost_event.wait()
            module_logger.warning(f'[{self.robot.name}-{self.robot.serial}] Control lost for robot.')

            # Call the callback function if provided
            if self.on_control_lost_callback and self.running:
                self.on_control_lost_callback(self.robot.serial)

            break

    def _behavior_control(self):
        behavior.ReserveBehaviorControl()