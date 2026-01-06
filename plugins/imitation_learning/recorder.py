import json
from datetime import datetime
from loguru import logger

class StateActionRecorder:
    """
    "Watch and Learn" Imitation Learning Plugin.
    Records (Game State, Player Action) pairs for model training.
    """
    def __init__(self, session_name: str = "default"):
        self.session_name = session_name
        self.recording = False
        self.data = []

    def start_recording(self):
        self.recording = True
        self.data = []
        logger.info(f"Imitation Learning: Started recording session '{self.session_name}'")

    def record_step(self, state_snapshot: dict, action: dict):
        if not self.recording:
            return
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "state": state_snapshot,
            "action": action
        }
        self.data.append(entry)

    def stop_recording(self, save_path: str = "scripts/imitation_data.json"):
        self.recording = False
        with open(save_path, "w") as f:
            json.dump(self.data, f, indent=2)
        logger.success(f"Imitation Learning: Saved {len(self.data)} steps to {save_path}")
