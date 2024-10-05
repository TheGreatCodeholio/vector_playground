# date_intent.py
from datetime import datetime

def get_date():
    now = datetime.now()
    readable_date_time = now.strftime("%A, %B %d, %Y")
    return readable_date_time

def main(robot):
    date = get_date()
    robot.audio_controller.speak_text(date)