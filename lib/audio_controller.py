

class AudioController:
    def __init__(self, robot):
        self.robot = robot

    def speak_text(self, text: str):
        self.robot.behavior.say_text(text)
