# date_intent.py
import logging
from datetime import datetime

intent_logger = logging.getLogger('vector_playground.intents.date_intent')

def get_date():
    now = datetime.now()
    readable_date_time = now.strftime("%A, %B %d, %Y")
    return readable_date_time

def main(robot, user_query):
    date = get_date()
    robot.audio_controller.speak_text(date)