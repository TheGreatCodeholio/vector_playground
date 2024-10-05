import asyncio
import logging
import random
import threading

from anki_vector.events import Events
from anki_vector.util import *

module_logger = logging.getLogger('vector_playground.task_manager')

class TaskManager:
    def __init__(self, robot):
        """
        Initializes the task manager.
        :param robot: The robot object.
        """
        self.robot = robot
        self.subscribed = False
        self.observed_event = threading.Event()
        self.loop = asyncio.new_event_loop()
        self.current_task = None  # Keep track of the current task
        self.task_lock = threading.Lock()
        self.task_manager_thread = threading.Thread(target=self._start_loop, daemon=True)
        self.running = False

    def _start_loop(self):
        """
        Starts the event loop in a separate thread.
        """
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start(self):
        """
        Starts the camera stream in a separate thread.
        """
        self.running = True
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Starting the Task Manager...')
        self.robot.events.subscribe(self._on_object_observed, Events.robot_observed_object, self.observed_event)
        self.subscribed = True
        self.task_manager_thread.start()

    def stop(self):
        """
        Stops the event loop and waits for the loop thread to finish.
        """
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Stopping the Task Manager...')
        self.running = False
        if self.subscribed:
            self.robot.events.unsubscribe(self._on_object_observed, Events.robot_observed_object)
            self.subscribed = False
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.task_manager_thread.join()
        module_logger.info(f'[{self.robot.name}-{self.robot.serial}] Stopped the Task Manager.')

    def _run_coroutine(self, coro):
        """
        Schedules a coroutine to run in the event loop.
        """
        with self.task_lock:
            self.current_task = asyncio.run_coroutine_threadsafe(coro, self.loop)

    def cancel_current_task(self):
        """
        Cancels the currently running task if any.
        """
        with self.task_lock:
            if self.current_task:
                self.current_task.cancel()
                try:
                    # Wait for the task to be cancelled
                    self.current_task.result()
                except (asyncio.CancelledError, asyncio.InvalidStateError):
                    module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Previous task was cancelled.')
                self.current_task = None

    def _on_object_observed(self, robot, event_type, event, evt):
        pass

    def intent_imperative_dance(self):
        """
        Makes the robot perform a dance.
        """
        self.cancel_current_task()
        module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Starting intent_imperative_dance')
        self._run_coroutine(self.robot.behavior.app_intent(intent='intent_imperative_dance'))

    def intent_system_sleep(self):
        """
        Makes the robot go to sleep.
        """
        self.cancel_current_task()
        module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Starting intent_system_sleep')
        self._run_coroutine(self.robot.behavior.app_intent(intent='intent_system_sleep'))

    def intent_imperative_fetchcube(self):
        """
        Makes the robot fetch the cube.
        """
        self.cancel_current_task()
        module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Starting intent_imperative_fetchcube')
        self._run_coroutine(self.robot.behavior.app_intent(intent='intent_imperative_fetchcube'))

    def intent_imperative_findcube(self):
        """
        Makes the robot find the cube.
        """

        self.cancel_current_task()
        module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Starting intent_imperative_findcube')
        self._run_coroutine(self.robot.behavior.app_intent(intent='intent_imperative_findcube'))

    def intent_explore_start(self):
        """
        Starts the robot's exploration behavior.
        """

        self.cancel_current_task()
        module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Starting intent_explore_start')
        self._run_coroutine(self.robot.behavior.app_intent(intent='intent_explore_start'))


    def intent_play_rollcube(self):
        """
        Makes the robot play by rolling the cube.
        """

        self.cancel_current_task()
        module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Starting intent_play_rollcube')
        self._run_coroutine(self.robot.behavior.app_intent(intent='intent_play_rollcube'))

    def enter_charger(self):
        """
        Makes the robot go to the charger.
        """
        self.cancel_current_task()
        module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Starting behavior drive on charger')
        self._run_coroutine(self.robot.behavior.drive_on_charger())

    def leave_charger(self):
        self.cancel_current_task()
        module_logger.debug(f'[{self.robot.name}-{self.robot.serial}] Starting behavior drive off charger')
        self._run_coroutine(self.robot.behavior.drive_off_charger())

    def perform_random_task(self):
        """
        Performs a random task by randomly selecting one of the task methods.
        """
        task_methods = [
            self.intent_imperative_dance,
            self.intent_system_sleep,
            self.intent_imperative_fetchcube,
            self.intent_imperative_findcube,
            self.intent_explore_start,
            self.intent_play_rollcube,
            self.leave_charger,
            self.enter_charger
        ]
        task_method = random.choice(task_methods)
        task_method()

    def wait_for_current_task(self, timeout=None):
        """
        Waits for the current task to complete.
        """
        with self.task_lock:
            if self.current_task:
                try:
                    result = self.current_task.result(timeout=timeout)
                    return result
                except asyncio.TimeoutError:
                    print("Task timed out.")
                except Exception as e:
                    print(f"Task resulted in exception: {e}")
        return None

