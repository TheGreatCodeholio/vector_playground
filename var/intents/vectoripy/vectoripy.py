#!/usr/bin/env python3
import logging
import threading
import time
import anki_vector
from anki_vector.util import degrees
from var.intents.vectoripy.config import SCREEN_UPDATE_INTERVAL, LIFT_THRESHOLD
from var.intents.vectoripy.Spotify import SpotifyClient  # Import the Spotify client module
from var.intents.vectoripy.UI import UIGenerator  # Import the UI generator module

intent_logger = logging.getLogger('vector_playground.intents.vectoripy')

def spotify_intent_loop(robot, spotify_client, ui_generator):
    """Main function to control Vector's interaction with Spotify."""

    # Connect to Vector

    robot.behavior.set_head_angle(degrees(45.0))
    robot.behavior.set_lift_height(0.0)

    # Initial state variables
    current_track_name = None

    # Set initial lift height to 40% (around 40 mm)
    robot.behavior.set_lift_height(0.4)
    time.sleep(1)  # Allow time for the lift to adjust
    baseline_lift_height = robot.lift_height_mm
    intent_logger.debug(f"Baseline lift height: {baseline_lift_height} mm")

    while True:
        intent_logger.debug(robot.intent_data["vectoripy"])
        # Check for touch to pause/resume the song
        if robot.touch.last_sensor_reading.is_being_touched:
            pause_spotify(robot, spotify_client)

        # Disengage lift motor for manual movement
        robot.motors.set_lift_motor(0.0)

        # Get the current lift height in mm
        vec_lift = robot.lift_height_mm
        # Skip to the next song if the lift is raised significantly above baseline
        if vec_lift > (baseline_lift_height + LIFT_THRESHOLD):
            skip_spotify(robot, spotify_client, "next")
            robot.behavior.set_lift_height(0.4)  # Reset lift to baseline
            time.sleep(0.5)  # Delay to avoid retriggering

        # Go back to the previous song if the lift is lowered significantly below baseline
        elif vec_lift < (baseline_lift_height - LIFT_THRESHOLD):
            skip_spotify(robot, spotify_client, "previous")
            robot.behavior.set_lift_height(0.4)  # Reset lift to baseline
            time.sleep(0.5)  # Delay to avoid retriggering

        # Get the current track details from Spotify
        track_data = spotify_client.get_current_playback()

        if track_data:
            robot.intent_data["vectoripy"]["is_paused"] = False  # Reset the pause state
            track_name = track_data['track_name']

            # Update the display if the track has changed
            if track_name != current_track_name:
                current_track_name = track_name

                # Perform a head animation to signal the song change
                robot.behavior.set_head_angle(degrees(10.0))
                robot.behavior.set_head_angle(degrees(45.0))

                # Reset the scrolling offsets for track and artist names
                ui_generator.reset_offsets()
                intent_logger.info(f"Now playing: {track_name}")

            # Generate and display the updated UI on Vector's screen
            ui_image = ui_generator.create_ui_image(track_data)
            screen_data = anki_vector.screen.convert_image_to_screen_data(ui_image)
            robot.screen.set_screen_with_image_data(screen_data, SCREEN_UPDATE_INTERVAL)

        else:
            # Display a default image if no track is playing
            robot.intent_data["vectoripy"]["is_paused"] = True
            default_image = ui_generator.create_default_image()
            screen_data = anki_vector.screen.convert_image_to_screen_data(default_image)
            robot.screen.set_screen_with_image_data(screen_data, SCREEN_UPDATE_INTERVAL)

        # Wait for the next update interval
        if not robot.intent_data["vectoripy"]["running"]:
            robot.anim.play_animation_trigger('WakeupGetout', 1)
            break

        time.sleep(SCREEN_UPDATE_INTERVAL)

def pause_spotify(robot, spotify_client):
    if robot.intent_data["vectoripy"]["is_paused"]:
        spotify_client.resume_playback()
        intent_logger.info("Resumed playback!")
        robot.intent_data["vectoripy"]["is_paused"] = False
    else:
        spotify_client.pause_playback()
        intent_logger.info("Paused playback!")
        robot.intent_data["vectoripy"]["is_paused"] = True

def skip_spotify(robot, spotify_client, action):
    if action == "next":
        spotify_client.next_track()
        intent_logger.info("Skipped to the next track!")
    elif action == "previous":
        spotify_client.previous_track()
        intent_logger.info("Skipped to the previous track!")


def get_spotify_action(utterance):
    utterance = utterance.lower()  # Convert to lowercase for case-insensitive matching

    # Keywords or actions we're looking for
    if "start" in utterance and "spotify" in utterance:
        return "start"
    elif "stop" in utterance and "spotify" in utterance:
        return "stop"
    elif "pause" in utterance and "spotify" in utterance:
        return "pause"
    elif "unpause" in utterance or "resume" in utterance:  # Cover both "unpause" and "resume"
        return "unpause"
    elif "next" in utterance or "skip" in utterance:
        return "next"
    elif "previous" in utterance or "back" in utterance:
        return "previous"
    else:
        return "unknown action"

def main(robot, user_query):
    if robot is None or user_query is None:
        intent_logger.error(f"Error getting robot, or user query")
        return
    spotify_client = SpotifyClient()
    ui_generator = UIGenerator()

    action = get_spotify_action(user_query)
    if "vectoripy" not in robot.intent_data:
        robot.intent_data["vectoripy"] = {'running': False, "is_paused": False}

    if action == "start":
        if robot.intent_data["vectoripy"]["running"] == True:
            intent_logger.info("Vectoripy already running!")
            return
        else:
            robot.intent_data["vectoripy"]["running"] = True
            threading.Thread(target=spotify_intent_loop, args=(robot, spotify_client, ui_generator), daemon=True).start()
    elif action == "stop":
        if robot.intent_data["vectoripy"]["running"] == False:
            intent_logger.info("Vectoripy already stopped!")
        else:
            robot.intent_data["vectoripy"]["running"] = False
    elif action in ["next", "previous"]:
        skip_spotify(robot, spotify_client, action)
    elif action in ["pause", "unpause"]:
        pause_spotify(robot, spotify_client)
    else:
        intent_logger.error(f"Unknown action: {action}")
        return


if __name__ == "__main__":
    main(robot=None, user_query=None)