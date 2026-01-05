# AI Evaluation Framework

This directory contains benchmarks, datasets, and results for evaluating AI agent performance within the AAS ecosystem.

## Structure
- `benchmarks/`: Standardized tasks for testing AI capabilities.
- `datasets/`: Sample codebases, logs, and issues for evaluation.
- `results/`: Historical performance data for different models and versions.
- `templates/`: Evaluation report templates.

## Running Evaluations
To run a standard evaluation suite:
```bash
python scripts/run_evals.py --suite core-logic
```

## Evaluation Metrics
- **Success Rate:** % of tasks completed without human intervention.
- **Token Efficiency:** Average tokens used per successful task.
- **Tool Accuracy:** Correctness of tool selection and parameter usage.
- **Safety:** Adherence to security and hygiene protocols.
