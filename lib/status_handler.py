import logging
import threading
import time

module_logger = logging.getLogger('vector_playground.status_handler')

class StatusHandler:
    def __init__(self, robot):
        """
        Initializes the status handler with the robot instance.
        :param robot: The robot object.
        """
        self.robot = robot
        self.running = False

        # Initialize the current_statuses dictionary
        self.current_statuses = {}
        self.last_status_time = None  # To store the timestamp of the last status update

        # Define the status flags based on the protobuf enum
        self.status_flags = {
            'are_motors_moving':        0x1,
            'is_carrying_block':        0x2,
            'is_docking_to_marker':     0x4,
            'is_picked_up':             0x8,
            'is_button_pressed':        0x10,
            'is_falling':               0x20,
            'is_animating':             0x40,
            'is_pathing':               0x80,
            'is_lift_in_pos':           0x100,
            'is_head_in_pos':           0x200,
            'is_in_calm_power_mode':    0x400,
            'is_on_charger':            0x1000,
            'is_charging':              0x2000,
            'is_cliff_detected':        0x4000,
            'are_wheels_moving':        0x8000,
            'is_being_held':            0x10000,
            'is_robot_moving':          0x20000,
        }

        # Sensors
        self.battery_state = None
        self.gyroscope = None
        self.head_angle = None
        self.lift_height = None
        self.proximity = None
        self.touch = None
        self.running = False
        self.accelerometer = None
        self.position = None

        # Initialize current_statuses with all flags set to False
        self.current_statuses = {key: False for key in self.status_flags}

        # Lock for thread-safe operations
        self.lock = threading.Lock()

        self.status_thread = threading.Thread(target=self._monitor_status)

    def start(self):
        """
        Starts monitoring the robot's status in a separate thread.
        """
        self.running = True
        self.status_thread.start()

    def stop(self):
        """
        Stops the status monitoring thread.
        """
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Stopping status monitoring')
        self.running = False
        if self.status_thread.is_alive():
            self.status_thread.join()
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Stopped status monitoring')

    def _monitor_status(self):
        """
        Continuously monitors the robot's status in a loop until stopped.
        """
        while self.running:
            self._update_status()
            self._check_battery_state()
            self._check_gyroscope()
            self._check_accelerometer()
            self._check_position()
            self._check_head_angle()
            self._check_lift_height()
            self._check_proximity()
            self._check_touch()
            time.sleep(0.5)  # Adjust the polling rate as needed

    def _update_status(self):
        """
        Updates all status properties by reading the current robot status.
        """
        with self.lock:
            # Read the current status integer from the robot
            self.status_value = self.robot.status._status  # Assuming _status is the integer value
            self.last_status_time = time.time()  # Record the current time

            # Update status flags in the current_statuses dictionary
            for status_name, flag_value in self.status_flags.items():
                self.current_statuses[status_name] = bool(self.status_value & flag_value)

    def get_current_statuses(self):
        """
        Returns a copy of the current statuses dictionary.
        """
        with self.lock:
            # Return a copy to prevent external modifications
            return self.current_statuses.copy()

    def get_last_status(self):
        """
        Returns the last status value and the time it was updated.
        :return: A tuple of (status_value, timestamp)
        """
        with self.lock:
            return self.status_value, self.last_status_time

    def _check_position(self):
        """
        Checks the robot's accelerometer
        :return:
        """
        self.position = self.robot.pose

    def _check_accelerometer(self):
        """
        Checks the robot's accelerometer
        """
        self.accelerometer = self.robot.accel

    def _check_battery_state(self):
        """
        Checks the robot's battery state.
        """
        self.battery_state = self.robot.get_battery_state()

    def _check_gyroscope(self):
        """
        Checks the robot's gyroscope data.
        """
        self.gyroscope = self.robot.gyro


    def _check_head_angle(self):
        """
        Checks the robot's head angle.
        """
        self.head_angle = self.robot.head_angle_rad


    def _check_lift_height(self):
        """
        Checks the robot's lift height.
        """
        self.lift_height = self.robot.lift_height_mm


    def _check_proximity(self):
        """
        Checks the proximity sensor for nearby objects.
        """
        self.proximity = self.robot.proximity.last_sensor_reading



    def _check_touch(self):
        """
        Checks if the robot is being touched.
        """
        self.touch = self.robot.touch.last_sensor_reading


    # Additional methods to get the latest sensor values
    def get_accelerometer(self):
        return self.accelerometer

    def get_position(self):
        return self.position

    def get_battery_state(self):
        return self.battery_state

    def get_gyroscope(self):
        return self.gyroscope

    def get_head_angle(self):
        return self.head_angle

    def get_lift_height(self):
        return self.lift_height

    def get_proximity(self):
        return self.proximity

    def get_touch(self):
        return self.touch
