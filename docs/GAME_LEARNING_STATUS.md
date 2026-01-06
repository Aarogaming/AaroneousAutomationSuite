# Game Learning: Project Status

> **TL;DR**: AAS can record gameplay but cannot yet "learn." This document tracks progress toward autonomous game learning.

## Current Capabilities ✅

### Data Collection (40% Complete)
- ✅ Basic state-action recorder ([recorder.py](../plugins/imitation_learning/recorder.py))
- ✅ OCR pipeline in Maelstrom (health/mana/gold extraction)
- ✅ Vision API integration ([vision_adapter.py](../plugins/ai_assistant/vision_adapter.py))
- ✅ gRPC bridge for state streaming ([server.py](../core/ipc/server.py))
- ❌ **Missing**: Frame buffering, screenshot capture, metadata tracking

### Perception (30% Complete)
- ✅ GPT-4o vision analysis
- ✅ Structured game state (GameAdapter)
- ❌ **Missing**: Vision encoder (ViT/ResNet), temporal modeling (LSTM)

### Action Execution (80% Complete)
- ✅ Maelstrom command routing
- ✅ Pre-built bots (Halfang, Bazaar, DanceBot)
- ✅ Script library system
- ❌ **Missing**: Unified action space definition

## What's Missing ❌

### Critical Gaps (0% Complete)
1. **Training Pipeline**: No PyTorch/TensorFlow integration
2. **Model Architecture**: No policy network implementation
3. **Inference Engine**: No real-time prediction system
4. **Evaluation Framework**: No metrics or testing harness

### Roadmap Items Not Started
- Phase 1: Enhanced state capture (Months 1-2)
- Phase 2: Vision-based encoding (Months 2-4)
- Phase 3: Behavioral cloning (Months 4-7)
- Phase 4: Ghost mode & DAgger (Months 7-9)
- Phase 5: Multi-task learning (Months 9-12)
- Phase 6: Reinforcement learning (Months 12-18)

## Quick Reference

| Capability | Status | File(s) | Next Action |
|------------|--------|---------|-------------|
| **Record demonstrations** | 🟡 Partial | `recorder.py` | Enhance with `CaptureManager` |
| **Extract game state** | ✅ Working | Maelstrom OCR | Add vision encoder |
| **Vision analysis** | ✅ Working | `vision_adapter.py` | Fine-tune on Wizard101 UI |
| **Train ML model** | ❌ Not Started | N/A | Create `train_policy.py` |
| **Deploy model** | ❌ Not Started | N/A | Create `inference_engine.py` |
| **Evaluate policy** | ❌ Not Started | N/A | Create `evaluate_policy.py` |

## Time to "Learn to Play"

**Estimated Timeline**: 9-12 months

### Breakdown
- **Months 1-2**: Data collection infrastructure (Phase 1)
- **Months 2-4**: Vision encoding (Phase 2)
- **Months 4-7**: First working policy (Phase 3)
- **Months 7-9**: Human-in-the-loop refinement (Phase 4)
- **Months 9-12**: Generalization (Phase 5)
- **Months 12+**: RL optimization (Phase 6)

### Blockers
1. **GPU Access**: Need RTX 3060+ for training
2. **Training Data**: Require 10+ hours of expert gameplay
3. **Engineering Resources**: ML engineer required for Phases 2-3

## Key Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| **[MASTER_ROADMAP.md](MASTER_ROADMAP.md)** | **Unified timeline (2026-2027+)** | **Everyone - Start here!** |
| [GAME_AUTOMATION_ROADMAP.md](GAME_AUTOMATION_ROADMAP.md) | Full 6-phase plan with milestones | Project leads, ML engineers |
| [GAME_LEARNING_INTEGRATION.md](GAME_LEARNING_INTEGRATION.md) | Developer integration guide | Engineers implementing features |
| [GAME_LEARNING_STATUS.md](GAME_LEARNING_STATUS.md) | This file - status tracker | Everyone |
| [ROADMAP.md](ROADMAP.md) | High-level 5-phase summary | Stakeholders |

## Phase Priorities

### Phase 1 (Immediate - Months 1-2)
**Goal**: Build robust data collection pipeline

**Why First?**
- Foundation for all ML work
- Can start collecting data while building models
- Low risk, high value

**Deliverables**:
- Enhanced `CaptureManager`
- 10+ hours of recorded gameplay
- Validated dataset with train/val splits

**Owner**: Core team  
**Status**: 🔴 Not Started  
**Blockers**: None - can start immediately

### Phase 3 (Critical Path - Months 4-7)
**Goal**: Train first behavioral cloning policy

**Why Critical?**
- Proof of concept for "learning"
- Validates entire data → model → inference pipeline
- Gates all downstream work (Phases 4-6)

**Deliverables**:
- Trained policy network
- Inference engine integrated with Hub
- 80%+ success rate on validation quests

**Owner**: ML engineer (TBD)  
**Status**: 🔴 Blocked by Phases 1-2  
**Blockers**: Need data collection + vision encoder

## Success Metrics

### Phase 1-2 (Foundation)
- [ ] 20+ hours of labeled gameplay across 5+ quest types
- [ ] Vision encoder: 95%+ UI detection accuracy
- [ ] <5% data corruption rate

### Phase 3-4 (Core BC)
- [ ] Policy: 80% → 90% quest completion (post-DAgger)
- [ ] Action accuracy: 85%+ match with expert
- [ ] Inference latency: <100ms per decision

### Phase 5-6 (Advanced)
- [ ] Transfer: Generalize to 3+ unseen quests
- [ ] RL: 20%+ efficiency improvement over human
- [ ] Safety: Zero critical errors in 100 test episodes

## Getting Started

### For Contributors

**If you want to help with data collection (Phase 1)**:
1. Review [GAME_LEARNING_INTEGRATION.md](GAME_LEARNING_INTEGRATION.md) § Phase 1
2. Install dependencies: `pip install opencv-python pillow`
3. Run: `python scripts/setup_ml_dirs.py`
4. Start recording: Use enhanced `CaptureManager`

**If you want to implement ML models (Phase 3)**:
1. Ensure GPU access (RTX 3060+)
2. Install ML stack: `pip install torch stable-baselines3 tensorboard`
3. Review architecture in [GAME_AUTOMATION_ROADMAP.md](GAME_AUTOMATION_ROADMAP.md) § 3.1
4. Start with simple policy network

**If you're a project lead**:
1. Review full [GAME_AUTOMATION_ROADMAP.md](GAME_AUTOMATION_ROADMAP.md)
2. Allocate resources (GPU, engineer time)
3. Create Linear epic with Phase 1 tasks
4. Set milestone: "First trained policy" (Month 7)

## FAQ

### Q: Can't we just use LLMs (GPT-4) to play the game?
**A**: LLM-based planning is possible but expensive and slow (200ms+ latency). Behavioral cloning creates a fast, specialized policy (50ms) that's cheaper at scale. Phase 6 explores hybrid approaches.

### Q: Why not just script everything?
**A**: Scripting breaks when UI changes or unexpected events occur. Learned policies generalize better and can adapt to novel situations.

### Q: What about OpenAI's Gym/Universe?
**A**: Universe is deprecated. We're building a custom environment wrapping Maelstrom's game state. Future: Multi-game adapter (Minecraft, Roblox).

### Q: How much will training cost?
**A**: Phase 3 (BC): ~$50-100 in GPU time (local RTX 3060). Phase 6 (RL): ~$500-1000 (cloud A100). Most expensive: human labeling time (50-100 hours).

## Related Work

- **OpenAI Hide and Seek**: Multi-agent RL in simulated environment
- **DeepMind AlphaStar**: StarCraft II mastery via imitation + RL
- **MineRL Competition**: Minecraft behavioral cloning dataset
- **VPT (Video Pre-Training)**: Learning from video demonstrations

## Updates

| Date | Update | Impact |
|------|--------|--------|
| 2026-01-04 | Roadmap created | Initial planning complete |
| TBD | Phase 1 kickoff | Data collection begins |
| TBD | First model trained | Proof of concept |
| TBD | Ghost mode deployed | Human-AI collaboration |

---

*Last Updated: January 4, 2026*  
*Next Review: Monthly or after phase completion*  
*Questions? See [AI_AGENT_GUIDELINES.md](AI_AGENT_GUIDELINES.md)*
