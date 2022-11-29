import json

class SpeakingState():
    def __init__(self, speaking):
        self.speaking = speaking

    def json(self):
        return json.dumps({"speaking": self.speaking})
