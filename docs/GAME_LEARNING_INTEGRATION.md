# Game Learning Integration Guide

> Quick reference for developers implementing the [Game Automation Roadmap](GAME_AUTOMATION_ROADMAP.md)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         AAS Hub                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Imitation Learning Plugin                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │   Capture    │  │   Training   │  │  Inference  │ │ │
│  │  │   Manager    │→ │   Pipeline   │→ │   Engine    │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│            ↕ gRPC                  ↕ Vision API             │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │ Project Maelstrom│    │   AI Assistant (Vision)      │  │
│  │  (Game Client)   │    │   VisionClient + GPT-4o      │  │
│  └──────────────────┘    └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
AaroneousAutomationSuite/
├── plugins/
│   └── imitation_learning/
│       ├── __init__.py               (Plugin registration)
│       ├── recorder.py               (Phase 1: EXISTS - needs enhancement)
│       ├── capture_manager.py        (Phase 1.1: TODO)
│       ├── action_space.py           (Phase 1.2: TODO)
│       ├── dataset_manager.py        (Phase 1.3: TODO)
│       ├── vision_encoder.py         (Phase 2.1: TODO)
│       ├── state_encoder.py          (Phase 2.2: TODO)
│       ├── models/
│       │   ├── policy_network.py     (Phase 3.1: TODO)
│       │   └── value_network.py      (Phase 6: TODO)
│       ├── training/
│       │   ├── bc_trainer.py         (Phase 3.2: TODO)
│       │   └── rl_trainer.py         (Phase 6.2: TODO)
│       ├── inference_engine.py       (Phase 3.4: TODO)
│       └── ghost_mode.py             (Phase 4.1: TODO - AAS-303)
│
├── core/
│   ├── managers/
│   │   └── adapters/
│   │       ├── action_space.py       (Shared action definitions)
│   │       └── base.py               (GameAdapter - EXISTS)
│   └── ipc/
│       └── server.py                 (gRPC bridge - EXISTS)
│
├── data/                              (Phase 1: Create structure)
│   ├── episodes/
│   │   ├── ep_001/
│   │   │   ├── metadata.json
│   │   │   └── frames/
│   │   │       ├── frame_0001.jpg
│   │   │       └── ...
│   │   └── ...
│   ├── models/
│   │   ├── policy_v1/
│   │   │   ├── checkpoint_epoch_10.pth
│   │   │   └── config.json
│   │   └── ...
│   └── logs/
│       └── tensorboard/
│
├── scripts/
│   ├── train_policy.py               (Phase 3.2: TODO)
│   ├── evaluate_policy.py            (Phase 3.3: TODO)
│   └── collect_demonstrations.py     (Phase 1: TODO)
│
└── docs/
    ├── GAME_AUTOMATION_ROADMAP.md    (THIS ROADMAP)
    └── GAME_LEARNING_INTEGRATION.md  (THIS GUIDE)
```

## Phase 1 Quick Start

### Step 1: Install ML Dependencies

Add to `requirements.txt`:
```txt
# Machine Learning
torch>=2.0.0
torchvision>=0.15.0
stable-baselines3>=2.0.0
tensorboard>=2.12.0
opencv-python>=4.8.0
pillow>=10.0.0
scikit-learn>=1.3.0

# Optional: For advanced features
optuna>=3.2.0  # Hyperparameter tuning
dvc>=3.0.0     # Dataset versioning
mlflow>=2.5.0  # Experiment tracking
```

Install:
```bash
pip install -r requirements.txt
```

### Step 2: Create Data Directory Structure

```bash
python scripts/setup_ml_dirs.py
```

Create `scripts/setup_ml_dirs.py`:
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

dirs = [
    "episodes",
    "models",
    "logs/tensorboard",
    "cache/embeddings",
]

for dir_path in dirs:
    full_path = DATA_DIR / dir_path
    full_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created {full_path}")

print("\nML directory structure ready!")
```

### Step 3: Enhance StateActionRecorder

Current `plugins/imitation_learning/recorder.py` is minimal. Enhance it:

```python
# plugins/imitation_learning/capture_manager.py
import json
import time
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, Any, Optional
import asyncio

class CaptureManager:
    """
    Enhanced data capture for behavioral cloning.
    Synchronizes screenshots, game state, and player actions.
    """
    def __init__(self, episode_name: str, fps: float = 2.0):
        self.episode_name = episode_name
        self.fps = fps
        self.frame_interval = 1.0 / fps
        
        self.episode_dir = Path(f"data/episodes/{episode_name}")
        self.frames_dir = self.episode_dir / "frames"
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_recording = False
        self.frame_count = 0
        self.episode_data = {
            "episode_id": episode_name,
            "start_time": None,
            "end_time": None,
            "frames": []
        }
    
    def start_recording(self):
        """Begin episode recording"""
        self.is_recording = True
        self.episode_data["start_time"] = datetime.now().isoformat()
        logger.info(f"🎬 Recording started: {self.episode_name}")
    
    async def capture_frame(self, game_state: Dict[str, Any], action: Dict[str, Any], 
                           screenshot_data: Optional[bytes] = None):
        """
        Capture a single frame with synchronized state and action.
        
        Args:
            game_state: Dict from Maelstrom snapshot (health, mana, position, etc.)
            action: Dict describing player action (type, params, timestamp)
            screenshot_data: Optional raw image bytes
        """
        if not self.is_recording:
            return
        
        frame_id = f"frame_{self.frame_count:06d}"
        screenshot_path = None
        
        if screenshot_data:
            screenshot_path = self.frames_dir / f"{frame_id}.jpg"
            screenshot_path.write_bytes(screenshot_data)
        
        frame_entry = {
            "frame_id": frame_id,
            "timestamp": time.time(),
            "screenshot_path": str(screenshot_path) if screenshot_path else None,
            "game_state": game_state,
            "action": action
        }
        
        self.episode_data["frames"].append(frame_entry)
        self.frame_count += 1
        
        if self.frame_count % 10 == 0:
            logger.debug(f"Captured {self.frame_count} frames")
    
    def stop_recording(self) -> str:
        """Stop recording and save episode data"""
        self.is_recording = False
        self.episode_data["end_time"] = datetime.now().isoformat()
        
        metadata_path = self.episode_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(self.episode_data, f, indent=2)
        
        logger.success(f"✅ Episode saved: {self.frame_count} frames → {metadata_path}")
        return str(metadata_path)
```

### Step 4: Integrate with Maelstrom

Modify `core/ipc/server.py` to support frame streaming:

```python
# Add to BridgeService class
async def RecordDemonstration(self, request_iterator, context):
    """
    Streaming RPC: Maelstrom continuously sends (state, action, screenshot).
    Hub saves to episode dataset.
    """
    from plugins.imitation_learning.capture_manager import CaptureManager
    
    episode_name = f"demo_{int(time.time())}"
    capture = CaptureManager(episode_name, fps=2.0)
    capture.start_recording()
    
    try:
        async for demo_frame in request_iterator:
            game_state = json.loads(demo_frame.game_state_json)
            action = json.loads(demo_frame.action_json)
            screenshot_bytes = demo_frame.screenshot_data
            
            await capture.capture_frame(game_state, action, screenshot_bytes)
        
        metadata_path = capture.stop_recording()
        return bridge_pb2.RecordingResponse(
            success=True,
            episode_path=metadata_path
        )
    except Exception as e:
        logger.error(f"Recording failed: {e}")
        return bridge_pb2.RecordingResponse(success=False, message=str(e))
```

## Phase 2-3 Workflow

### Training Pipeline Overview

```python
# scripts/train_policy.py (simplified)
import torch
from torch.utils.data import DataLoader
from plugins.imitation_learning.dataset_manager import EpisodeDataset
from plugins.imitation_learning.models.policy_network import PolicyNetwork
from plugins.imitation_learning.training.bc_trainer import BCTrainer

def main():
    # 1. Load dataset
    dataset = EpisodeDataset("data/episodes")
    train_loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # 2. Initialize model
    policy = PolicyNetwork(
        state_dim=690,  # 512 vision + 50 stats + 128 temporal
        action_dim=20,  # Number of discrete actions
        hidden_dim=256
    )
    
    # 3. Train
    trainer = BCTrainer(policy, train_loader)
    trainer.train(epochs=50, lr=1e-4)
    
    # 4. Save checkpoint
    torch.save(policy.state_dict(), "data/models/policy_v1/checkpoint.pth")
    print("✅ Training complete!")

if __name__ == "__main__":
    main()
```

### Integration with AAS Hub

```python
# plugins/imitation_learning/__init__.py
from loguru import logger
from .inference_engine import InferenceEngine

class ImitationLearningPlugin:
    """
    Plugin registration for ML-based game automation.
    """
    def __init__(self, hub):
        self.hub = hub
        self.inference_engine = None
    
    async def start(self):
        """Load trained model on startup"""
        model_path = "data/models/policy_v1/checkpoint.pth"
        if Path(model_path).exists():
            self.inference_engine = InferenceEngine(model_path)
            await self.inference_engine.load_model()
            logger.success("🤖 ML Policy loaded successfully")
        else:
            logger.warning("No trained model found. Run training first.")
    
    async def predict_action(self, game_state: dict) -> dict:
        """Get AI's suggested action for current game state"""
        if not self.inference_engine:
            return {"type": "no_op"}
        
        return await self.inference_engine.predict(game_state)

def register(hub):
    """Plugin entry point"""
    plugin = ImitationLearningPlugin(hub)
    hub.register_plugin("imitation_learning", plugin)
    return plugin
```

## Integration Points

### 1. With Task Manager

```python
# core/managers/tasks.py - Add ML task type
class TaskType(Enum):
    # ... existing types
    ML_TRAINING = "ml_training"
    ML_INFERENCE = "ml_inference"
```

### 2. With Vision Client

```python
# plugins/ai_assistant/vision_adapter.py is already implemented
# Use VisionClient.describe_screenshot() for state encoding
from plugins.ai_assistant.vision_adapter import VisionClient

async def encode_screenshot(screenshot_path: str) -> str:
    config = load_config()
    vision = VisionClient(config)
    description = await vision.describe_screenshot(screenshot_path)
    return description
```

### 3. With Artifact Manager

```python
# core/managers/artifacts.py - Store training artifacts
class ArtifactManager:
    async def save_model_checkpoint(self, model_name: str, data: bytes):
        path = self.artifacts_dir / "models" / f"{model_name}.pth"
        await self._write_file(path, data)
```

## Testing Strategy

### Unit Tests
```python
# tests/test_imitation_learning.py
import pytest
from plugins.imitation_learning.capture_manager import CaptureManager

@pytest.mark.asyncio
async def test_capture_frame():
    manager = CaptureManager("test_episode", fps=1.0)
    manager.start_recording()
    
    await manager.capture_frame(
        game_state={"health": 100},
        action={"type": "move_forward"},
        screenshot_data=b"fake_image_data"
    )
    
    metadata_path = manager.stop_recording()
    assert Path(metadata_path).exists()
```

### Integration Tests
```bash
# Test full pipeline
python scripts/test_ml_pipeline.py
```

## Monitoring & Metrics

### TensorBoard Dashboard
```bash
tensorboard --logdir data/logs/tensorboard
# Open http://localhost:6006
```

### Key Metrics to Track
- **Training**: Loss curve, action accuracy, gradient norms
- **Inference**: Latency (ms), confidence scores, action distribution
- **Episode**: Success rate, completion time, failure reasons

## Next Steps

1. **Immediate (Week 1)**:
   - [ ] Run `scripts/setup_ml_dirs.py`
   - [ ] Install ML dependencies
   - [ ] Test CaptureManager with dummy data

2. **Short-term (Month 1)**:
   - [ ] Record 5 demonstration episodes
   - [ ] Implement VisionEncoder
   - [ ] Create training script stub

3. **Long-term (Months 2-4)**:
   - [ ] Train first policy model
   - [ ] Deploy inference engine
   - [ ] Achieve 80% quest completion on validation set

## Troubleshooting

### GPU Not Detected
```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))
```

### Out of Memory
- Reduce batch size (32 → 16 → 8)
- Use gradient accumulation
- Enable mixed precision training (AMP)

### Model Not Converging
- Check data quality (visualize samples)
- Verify action space balance (avoid class imbalance)
- Try different learning rates (1e-3, 1e-4, 1e-5)

## Resources

- [PyTorch Tutorial](https://pytorch.org/tutorials/)
- [Stable-Baselines3 Docs](https://stable-baselines3.readthedocs.io/)
- [Behavioral Cloning Guide](https://spinningup.openai.com/en/latest/algorithms/bc.html)
- [Main Roadmap](GAME_AUTOMATION_ROADMAP.md)

---

*Last Updated: January 4, 2026*  
*Quick questions? Check [AI_AGENT_GUIDELINES.md](AI_AGENT_GUIDELINES.md)*
