# Game Automation & Learning Roadmap

> **Part of**: [MASTER_ROADMAP.md](MASTER_ROADMAP.md) § Phase 3.1 - Game Automation & Learning System

> **Mission**: Evolve AAS from scripted automation to autonomous game learning through imitation learning, behavioral cloning, and eventually reinforcement learning.

## Executive Summary

**Current State**: AAS has robust sensory/motor infrastructure but lacks ML training capabilities.

**Target State**: Autonomous agent that can "watch a player" and learn to replicate complex gameplay behaviors.

**Timeline**: 9-12 months to full behavioral cloning; 18+ months to RL-based optimization.

---

## Phase 1: Data Collection Infrastructure (Months 1-2)

### Goal: Build high-quality training data pipeline

### Milestones

#### 1.1 Enhanced State Capture
- **Owner**: Core team
- **Dependencies**: None
- **Tasks**:
  - [ ] Extend `StateActionRecorder` to capture full game state (not just snapshots)
  - [ ] Add screenshot capture at configurable intervals (1-5 FPS)
  - [ ] Implement frame buffering (store last N frames for temporal context)
  - [ ] Add metadata: timestamp, episode_id, game_phase (combat, exploration, quest)
  - [ ] Create `plugins/imitation_learning/capture_manager.py`

**Output Format**:
```json
{
  "episode_id": "ep_20260104_001",
  "frames": [
    {
      "timestamp": 1704326400.123,
      "screenshot_path": "data/episodes/ep_001/frame_0001.jpg",
      "game_state": {
        "player": {"health": 100, "mana": 50, "position": [x, y, z]},
        "enemies": [...],
        "ui_state": {...}
      },
      "action": {
        "type": "move_forward",
        "params": {"duration_ms": 500}
      }
    }
  ]
}
```

#### 1.2 Action Taxonomy
- **Tasks**:
  - [ ] Define comprehensive action space for Wizard101
  - [ ] Create `ActionSpace` enum: MOVE, CAST_SPELL, SELECT_TARGET, OPEN_MENU, etc.
  - [ ] Map Maelstrom commands to action primitives
  - [ ] Document action parameters and constraints
  - [ ] Create `core/managers/adapters/action_space.py`

#### 1.3 Dataset Management
- **Tasks**:
  - [ ] Create dataset versioning system (DVC or custom)
  - [ ] Implement data validation (check for corrupted screenshots, missing actions)
  - [ ] Add replay viewer (visualize recorded episodes)
  - [ ] Create train/val/test splits
  - [ ] Target: 10+ hours of expert gameplay across diverse scenarios

**Acceptance Criteria**: Record 5 complete quest walkthroughs with synchronized state-action pairs at 2 FPS.

---

## Phase 2: Vision-Based State Encoding (Months 2-4)

### Goal: Convert raw screenshots to structured representations

### Milestones

#### 2.1 Feature Extraction Pipeline
- **Dependencies**: Phase 1.1
- **Tasks**:
  - [ ] Integrate Vision Transformer (ViT) or ResNet for screenshot encoding
  - [ ] Create `plugins/imitation_learning/vision_encoder.py`
  - [ ] Fine-tune on Wizard101 UI elements (health bars, spell icons, minimap)
  - [ ] Extract embeddings: 512-dim vector per frame
  - [ ] Benchmark: OCR vs Vision model accuracy on key stats

#### 2.2 Hybrid State Representation
- **Tasks**:
  - [ ] Combine vision embeddings with structured data (health, mana, coordinates)
  - [ ] Create unified state vector: `[vision_features (512) + game_stats (50) + temporal_context (128)]`
  - [ ] Implement state normalization (scale all features to [0, 1])
  - [ ] Add state caching for inference speed

#### 2.3 Temporal Modeling
- **Tasks**:
  - [ ] Add LSTM/GRU layer to capture action sequences
  - [ ] Implement frame stacking (4-8 consecutive frames)
  - [ ] Create attention mechanism over recent history
  - [ ] Handle variable-length episodes

**Acceptance Criteria**: State encoder achieves >95% accuracy on UI element detection test set.

---

## Phase 3: Behavioral Cloning - Core (Months 4-7)

### Goal: Train policy to mimic expert demonstrations

### Milestones

#### 3.1 Model Architecture
- **Dependencies**: Phase 2.1, 2.2
- **Tasks**:
  - [ ] Implement policy network: `State → Action Probabilities`
  - [ ] Architecture: `[StateEncoder → LSTM(256) → FC(128) → ActionLogits]`
  - [ ] Add auxiliary heads for value estimation (future RL)
  - [ ] Create `plugins/imitation_learning/models/policy_network.py`
  - [ ] Support PyTorch and optional TensorFlow backend

#### 3.2 Training Loop
- **Tasks**:
  - [ ] Implement supervised learning: minimize cross-entropy loss on expert actions
  - [ ] Add data augmentation (rotation, brightness, occlusion for screenshots)
  - [ ] Create training script: `scripts/train_policy.py`
  - [ ] Implement checkpointing and early stopping
  - [ ] Add TensorBoard logging (loss curves, action distribution)
  - [ ] Hyperparameters: learning_rate=1e-4, batch_size=32, epochs=50

#### 3.3 Evaluation Framework
- **Tasks**:
  - [ ] Create `evaluate_policy.py` script
  - [ ] Metrics:
    - Action accuracy (% matching expert)
    - Episode success rate (quest completion)
    - Efficiency (time to complete vs expert)
  - [ ] Implement A/B testing framework (scripted bot vs learned policy)
  - [ ] Add visualization: side-by-side expert vs agent gameplay

#### 3.4 Integration with AAS Hub
- **Tasks**:
  - [ ] Create `plugins/imitation_learning/inference_engine.py`
  - [ ] Load trained model on startup
  - [ ] Real-time inference: Game state → Model prediction → Maelstrom command
  - [ ] Add latency monitoring (<100ms per decision)
  - [ ] Implement fallback to scripted behavior on model errors

**Acceptance Criteria**: Trained policy completes "Unicorn Way" quest in Wizard101 with 80% success rate.

---

## Phase 4: Ghost Mode & Active Learning (Months 7-9)

### Goal: Human-in-the-loop refinement and edge case handling

### Milestones

#### 4.1 Ghost Mode Implementation (AAS-303)
- **Dependencies**: Phase 3.3
- **Tasks**:
  - [ ] Create "shadow execution" mode: AI suggests action, human approves/overrides
  - [ ] Build UI overlay showing model confidence and alternative actions
  - [ ] Log all corrections as high-value training data
  - [ ] Implement "ask for help" trigger when confidence < 0.3
  - [ ] Create `plugins/imitation_learning/ghost_mode.py`

#### 4.2 DAgger (Dataset Aggregation)
- **Tasks**:
  - [ ] Implement iterative training: Train → Deploy → Collect corrections → Retrain
  - [ ] Prioritize failures for human labeling
  - [ ] Create annotation tool for quick action labeling
  - [ ] Target: 5 DAgger iterations with 30min human review per cycle

#### 4.3 Error Recovery
- **Tasks**:
  - [ ] Add "reset to safe state" behavior (e.g., flee combat if health < 20%)
  - [ ] Implement episode termination conditions
  - [ ] Create failure analysis dashboard (categorize error types)
  - [ ] Add automatic episode replay for debugging

**Acceptance Criteria**: Policy reaches 90%+ success rate on training quests after DAgger refinement.

---

## Phase 5: Multi-Task & Transfer Learning (Months 9-12)

### Goal: Generalize across different game scenarios

### Milestones

#### 5.1 Task-Conditioned Policy
- **Dependencies**: Phase 3.4
- **Tasks**:
  - [ ] Extend policy input: `[State, Task_Embedding] → Action`
  - [ ] Train on multiple quest types (combat, collection, dialogue, puzzle)
  - [ ] Implement task encoder (CLIP-style text → vector)
  - [ ] Support natural language goals: "Farm Halfang 10 times"

#### 5.2 Curriculum Learning
- **Tasks**:
  - [ ] Order training tasks by difficulty: Tutorial → Early quests → Boss fights
  - [ ] Implement progressive training (unlock harder tasks as performance improves)
  - [ ] Add skill prerequisites (learn "target enemy" before "cast AOE spell")

#### 5.3 Meta-Learning (Optional)
- **Tasks**:
  - [ ] Implement MAML or Reptile for fast adaptation to new quests
  - [ ] Fine-tune on 5-10 demonstrations of unseen quest
  - [ ] Benchmark few-shot learning performance

**Acceptance Criteria**: Policy generalizes to 3 unseen quests with <10 demonstrations per quest.

---

## Phase 6: Reinforcement Learning Optimization (Months 12-18)

### Goal: Surpass human performance through self-play

### Milestones

#### 6.1 Reward Engineering
- **Tasks**:
  - [ ] Define reward signals:
    - Quest progress: +100 per objective
    - Efficiency: +10 per enemy defeated, -1 per second elapsed
    - Survival: -50 for death/potion use
  - [ ] Implement reward shaping (intermediate checkpoints)
  - [ ] Add intrinsic motivation (curiosity bonus for exploring)

#### 6.2 PPO/SAC Training
- **Dependencies**: Phase 3.1 (value head)
- **Tasks**:
  - [ ] Integrate Stable-Baselines3 or RLlib
  - [ ] Implement PPO with behavioral cloning pre-training
  - [ ] Add exploration strategies (epsilon-greedy → entropy bonus)
  - [ ] Create self-play environment (agent vs scripted opponents)
  - [ ] Hyperparameters: gamma=0.99, lambda=0.95, clip=0.2

#### 6.3 Distributed Training
- **Tasks**:
  - [ ] Set up multi-GPU training (data parallel)
  - [ ] Implement experience replay buffer
  - [ ] Add asynchronous environment rollouts
  - [ ] Target: 1M steps per hour

#### 6.4 Safety & Constraints
- **Tasks**:
  - [ ] Add hard constraints (never drop equipped items, never trade away currency)
  - [ ] Implement reward clipping and KL divergence penalties
  - [ ] Create "safe exploration" boundaries

**Acceptance Criteria**: RL policy completes Dragonspyre quests 20% faster than human baseline.

---

## Infrastructure & Tooling

### Required Tech Stack

#### ML Frameworks
- **PyTorch** (primary): Model training and inference
- **Stable-Baselines3**: RL algorithms
- **HuggingFace Transformers**: Pre-trained vision models
- **Optuna**: Hyperparameter tuning

#### Data Management
- **DVC**: Dataset versioning
- **MLflow**: Experiment tracking
- **TensorBoard**: Visualization
- **OpenCV**: Image preprocessing

#### Integration
- **gRPC**: Low-latency AAS ↔ Maelstrom communication
- **Redis**: State caching for multi-process training
- **Docker**: Reproducible training environments

### Hardware Requirements

#### Minimum (Phase 1-4)
- GPU: RTX 3060 (12GB VRAM)
- RAM: 32GB
- Storage: 500GB SSD (for datasets)

#### Recommended (Phase 5-6)
- GPU: RTX 4090 or A100 (80GB VRAM for large models)
- Multi-GPU: 2-4x RTX 4080 for distributed training
- Storage: 2TB NVMe SSD

---

## Integration with Existing AAS Roadmap

### Cross-References

| AAS Roadmap Item | Game Learning Dependency |
|------------------|--------------------------|
| **AAS-207**: Multi-Modal Knowledge Graph | Phase 2.1 (Vision encoder feeds into KG) |
| **AAS-208**: Agentic Self-Healing | Phase 4.3 (Error recovery patterns) |
| **AAS-211**: Automated Task Decomposition | Phase 5.1 (Task-conditioned policy) |
| **AAS-303**: Behavioral Cloning (Ghost Mode) | Phase 4.1 (Core ghost mode) |
| **AAS-304**: Federated Learning Mesh | Phase 6.3 (Distributed training) |

### Modified Timelines

Original **AAS-303** was Phase 5 (autonomy). With this roadmap:
- **Move to Phase 3** (months 4-7) as priority feature
- Blocks downstream items (AAS-301: Swarm Orchestration needs trained agents)

---

## Success Metrics

### Phase 1-2 (Foundation)
- [ ] 20+ hours of labeled gameplay data
- [ ] Vision encoder: 95%+ accuracy on UI detection
- [ ] Data pipeline: <5% corrupted frames

### Phase 3-4 (Behavioral Cloning)
- [ ] Quest completion rate: 80% → 90% (DAgger)
- [ ] Action accuracy: 85% match with expert
- [ ] Inference latency: <100ms per decision

### Phase 5-6 (Advanced)
- [ ] Transfer learning: 3+ unseen quests with <10 demos
- [ ] RL optimization: 20% efficiency improvement over human
- [ ] Safety: Zero critical errors (item loss, unintended trades) in 100 test episodes

---

## Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Poor vision encoder accuracy on Wizard101 UI | Medium | High | Fine-tune on game-specific dataset; fallback to OCR |
| Overfitting to training quests | High | Medium | Data augmentation, curriculum learning, DAgger |
| Model drift after game updates | Medium | Medium | Automated retraining pipeline, version detection |
| Latency >100ms per decision | Low | High | Model quantization, TensorRT optimization |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Insufficient training data | Medium | High | Recruit beta testers for data collection |
| GPU resource constraints | Medium | Medium | Cloud training (AWS/GCP), gradual scaling |
| Player detection/ban by KingsIsle | Low | Critical | Respect ToS, add random delays, human-like behavior |

---

## Quick Start: First 30 Days

### Week 1: Environment Setup
```bash
# Install ML dependencies
pip install torch torchvision stable-baselines3 tensorboard opencv-python

# Create data directories
mkdir -p data/{episodes,models,logs}

# Initialize DVC
dvc init
```

### Week 2: Data Collection
```python
# Start recording session
from plugins.imitation_learning.recorder import StateActionRecorder

recorder = StateActionRecorder(session_name="unicorn_way_quest")
recorder.start_recording()
# Play game manually
recorder.stop_recording("data/episodes/unicorn_way_001.json")
```

### Week 3: Vision Encoder
```python
# Test vision pipeline
from plugins.imitation_learning.vision_encoder import VisionEncoder

encoder = VisionEncoder(model="resnet50")
embedding = encoder.encode_screenshot("data/episodes/.../frame_001.jpg")
print(embedding.shape)  # (512,)
```

### Week 4: First Model
```python
# Train simple policy
python scripts/train_policy.py \
  --data_dir data/episodes \
  --model_dir data/models/policy_v1 \
  --epochs 10 \
  --batch_size 16
```

---

## Next Steps

1. **Review & Approval**: Get stakeholder sign-off on phases 1-4 (core BC)
2. **Resource Allocation**: Secure GPU access (local or cloud)
3. **Kick-off**: Create Linear epic "Game Learning" with sub-tasks from Phase 1
4. **Team Formation**: Assign ML engineer + game automation expert

---

## Appendix: Alternative Approaches

### Option 1: Imitation Learning (Chosen)
- **Pros**: Sample efficient, interpretable, fast deployment
- **Cons**: Limited to human performance ceiling

### Option 2: Pure RL (Not Chosen)
- **Pros**: Can surpass human performance
- **Cons**: Requires 10-100x more compute, unstable training, safety risks

### Option 3: Hybrid (Future)
- **Pros**: Best of both worlds
- **Cons**: Complex, requires both pipelines

---

## References

1. [AAS ROADMAP.md](ROADMAP.md) - Main project roadmap
2. [Behavioral Cloning: Ross et al. 2010](https://arxiv.org/abs/1011.0686)
3. [DAgger: Ross et al. 2011](https://arxiv.org/abs/1011.0686)
4. [Vision Transformers: Dosovitskiy et al. 2020](https://arxiv.org/abs/2010.11929)
5. [PPO: Schulman et al. 2017](https://arxiv.org/abs/1707.06347)

---

*Last Updated: January 4, 2026*  
*Maintained by: AAS Core Team*  
*Status: Draft - Pending Approval*
