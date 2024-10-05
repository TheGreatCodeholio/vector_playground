#!/usr/bin/env python3

import ephem

def calculate_moon_phase():
    moon = ephem.Moon()
    moon.compute()
    phase = moon.phase  # Gives the moon phase as a percentage

    if phase == 0:
        return "New Moon"
    elif 0 < phase < 50:
        return "Waxing Crescent"
    elif phase == 50:
        return "First Quarter"
    elif 50 < phase < 100:
        return "Waxing Gibbous"
    elif phase == 100:
        return "Full Moon"
    elif 100 > phase > 50:
        return "Waning Gibbous"
    elif phase == 50:
        return "Last Quarter"
    else:
        return "Waning Crescent"


def main(robot):
    moon_phase = calculate_moon_phase()
    final_text = f"The current moon phase is {moon_phase}."
    robot.audio_controller.speak_text(final_text)


if __name__ == "__main__":
    main()
