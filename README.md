# DevInsight AI Lite

An intelligent software issue tracker, built step by step during the field training.

This version adds offline machine learning: a classifier that suggests an issue's category. The
web application does not use it yet. That is the work of Week 6.

## Getting started

```bash
git clone https://github.com/YOUR-USERNAME/devinsight-ai-lite.git
cd devinsight-ai-lite
python -m venv .venv
source .venv/Scripts/activate    # Git Bash on Windows
pip install -r requirements.txt
```

The training tools need extra packages:

```bash
pip install -r requirements-ml.txt
```

## Train and evaluate

```bash
python -m ml.train           # compares models, evaluates, saves ml/artifacts/
python -m ml.leakage_demo    # shows how leakage inflates scores
python -m ml.predict_cli "Login page times out" "It spins for a minute"
```

Open `ml/explore_data.ipynb` in VS Code to explore the dataset. Results are in
`docs/model_evaluation.md`.
