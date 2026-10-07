---
source: EarthPulse ML Metrics Guide
title: Model Evaluation: PR-AUC vs ROC-AUC in Severe Wildfire Class Imbalance
category: machine_learning
dataset: ML_EVALUATION
satellite: Multi-Sensor
date: 2024-03-05
chunk_index: 0
---

# Model Evaluation: PR-AUC vs ROC-AUC in Severe Wildfire Class Imbalance

## Why ROC-AUC is Misleading for Wildfire Modeling
Wildfires are extremely rare spatio-temporal events: across 1,000,000 spatial pixels, perhaps only 500 are actively burning (0.05% positive class prevalence).
The Receiver Operating Characteristic (ROC) curve plots True Positive Rate vs False Positive Rate:
FPR = FP / (FP + TN)
Because the number of True Negatives (TN) is immense, even tens of thousands of False Positive false alarms will result in an FPR close to 0.0, yielding a deceptively high ROC-AUC of 0.95+ while flooding firefighters with false alarms.

## Precision-Recall Curve (PR-AUC)
The Precision-Recall curve focuses strictly on the minority positive class:
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
Any false alarm directly reduces precision. EarthPulse achieves a rigorous **PR-AUC of 0.84** under 50km spatial block holdout validation, ensuring that high-risk alert zones are actionable and reliable.
