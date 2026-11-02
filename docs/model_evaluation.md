# Model evaluation

## Summary

| Item | Value |
|---|---|
| Task | Suggest one of five categories for an issue report |
| Model | Logistic regression on TF-IDF features of words and word pairs |
| Library | scikit-learn 1.9.1 |
| Data | 800 prepared, labeled, non-sensitive reports |
| Split | 640 training, 160 test, stratified, random state 42 |
| Test accuracy | 0.894 |
| Test macro F1 | 0.907 |
| Baseline accuracy | 0.375 |
| Baseline macro F1 | 0.109 |

Macro F1 is the main measure, because the categories are imbalanced and a rare category matters
as much as a common one. The baseline always answers the largest category. Its accuracy shows why
accuracy alone would mislead.

## Choosing a model: five-fold cross-validation on the training data

| Candidate | Macro F1 | Std | Accuracy |
|---|---|---|---|
| baseline_most_frequent | 0.109 | 0.000 | 0.375 |
| naive_bayes | 0.682 | 0.051 | 0.739 |
| logistic_regression | 0.884 | 0.032 | 0.883 |
| linear_svm | 0.879 | 0.031 | 0.878 |

Logistic regression was chosen for deployment. It scores as well as the best candidate, and it
gives a probability for each category, which the application shows as a confidence value.

## Results on the test set, used once

| Category | Precision | Recall | F1 | Reports |
|---|---|---|---|---|
| bug | 0.883 | 0.883 | 0.883 | 60 |
| documentation | 0.909 | 1.000 | 0.952 | 20 |
| feature | 0.868 | 0.825 | 0.846 | 40 |
| performance | 1.000 | 0.950 | 0.974 | 20 |
| security | 0.857 | 0.900 | 0.878 | 20 |

## Confusion matrix (rows are the true category)

| | bug | docu | feat | perf | secu |
|---|---|---|---|---|---|
| bug | 53 | 2 | 5 | 0 | 0 |
| documentation | 0 | 20 | 0 | 0 | 0 |
| feature | 4 | 0 | 33 | 0 | 3 |
| performance | 1 | 0 | 0 | 19 | 0 |
| security | 2 | 0 | 0 | 0 | 18 |

## Error analysis

Every mistake is listed in `ml/artifacts/misclassified.csv`. Read them before trusting the numbers.

## Limits

- The model sees words, not meaning. A report that avoids the usual vocabulary can be misclassified.
- The data was prepared for this training. Results on another team's reports will be lower until the
  model is retrained on their data.
- The model suggests and a person decides. Both the suggestion and the decision are stored, so
  agreement can be measured over time.

## How to reproduce

```bash
pip install -r requirements-ml.txt
python -m ml.train
```
