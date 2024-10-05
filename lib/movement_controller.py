import logging


from anki_vector.util import distance_mm, speed_mmps, degrees

module_logger = logging.getLogger('vector_playground.movement_controller')

class MovementController:
    def __init__(self, robot):
        self.robot = robot

    def control_move_wheels(self, left_wheel_speed: float, right_wheel_speed: float, left_wheel_acceleration: float = None, right_wheel_acceleration: float = None):
        """

        :param left_wheel_speed: Speed of the left tread (in millimeters per second).
        :param right_wheel_speed: Speed of the right tread (in millimeters per second).
        :param left_wheel_acceleration: Acceleration of left tread (in millimeters per second squared)
                            ``None`` value defaults this to the same as l_wheel_speed.
        :param right_wheel_acceleration: Acceleration of right tread (in millimeters per second squared)
                            ``None`` value defaults this to the same as r_wheel_speed.
        :return: None
        """

        try:
            self.robot.motors.set_wheel_motors(left_wheel_speed, right_wheel_speed, left_wheel_acceleration, right_wheel_acceleration)
        except Exception as e:
            module_logger.error(e)

    def control_move_lift(self, speed: float):
        """

        :param speed: Motor speed for Vector's lift, measured in radians per second.
        :return: None
        """

        try:
            self.robot.motors.set_lift_motor(speed)
        except Exception as e:
            module_logger.error(e)

    def control_move_head(self, speed: float):
        """

        :param speed: Motor speed for Vector's head, measured in radians per second.
        :return: None
        """

        try:
            self.robot.motors.set_head_motor(speed)
        except Exception as e:
            module_logger.error(e)

    def control_stop_all(self):
        """
        Stops All Motors
        :return:
        """

        try:
            self.robot.motors.stop_all_motors()
        except Exception as e:
            module_logger.error(e)

    # Movement methods
    def control_drive_straight(self, distance: float, speed:float, should_play_anim=True):
        """
        :param distance: The distance in mm to drive
            (>0 for forwards, <0 for backwards)
        :param speed: The speed to drive at in mm/s
            (should always be >0, the abs(speed) is used internally) max 220 mm/s
        :param should_play_anim: Whether to play idle animations whilst driving
            (tilt head, hum, animated eyes, etc.)
        :return:
        """

        self.robot.behavior.drive_straight(distance_mm(distance), speed_mmps(speed), should_play_anim=should_play_anim)

    def control_turn_in_place(self, angle: float, speed: float=45, accel: float=100, angle_tolerance: float=2, is_absolute:bool=False):
        """

        :param angle: Degrees: The angle to turn. Positive values turn to the left, negative values to the right.
        :param speed: Degrees: Angular turn speed (per second).
        :param accel: Degrees: Acceleration of angular turn (per second squared).
        :param angle_tolerance: Degrees: angular tolerance to consider the action complete (this is clamped to a minimum of 2 degrees internally).
        :param is_absolute: True to turn to a specific angle, False to turn relative to the current pose.

        :return: None
        """


        self.robot.behavior.turn_in_place(angle=degrees(angle), speed=degrees(speed), accel=degrees(accel), angle_tolerance=degrees(angle_tolerance), is_absolute=is_absolute
        )

    def control_set_head_angle(self, angle, acceleration: float = 10.0, max_speed: float=10.0, duration: float=0):

        """

        :param angle: Desired angle for Vector's head.
            (:const:`MIN_HEAD_ANGLE` to :const:`MAX_HEAD_ANGLE`).
            (we clamp it to this range internally).
        :param acceleration: Acceleration of Vector's head in radians per second squared.
        :param max_speed: Maximum speed of Vector's head in radians per second.
        :param duration: Time for Vector's head to move in seconds. A value
                of zero will make Vector try to do it as quickly as possible.
        :return:
        """

        self.robot.behavior.set_head_angle(angle=degrees(angle), accel=acceleration, max_speed=max_speed, duration=duration)

    def control_set_lift_height(self, height: float, accel: float =10.0, max_speed: float=10.0, duration: float=0.0):
        """
        :param height: desired height for Vector's lift 0.0 (bottom) to
                1.0 (top) (we clamp it to this range internally).
        :param accel: Acceleration of Vector's lift in radians per
                second squared.
        :param max_speed: Maximum speed of Vector's lift in radians per second.
        :param duration: Time for Vector's lift to move in seconds. A value
                of zero will make Vector try to do it as quickly as possible.

        :return:
        """
        self.robot.behavior.set_lift_height(height=height, accel=accel, max_speed=max_speed, duration=duration)
