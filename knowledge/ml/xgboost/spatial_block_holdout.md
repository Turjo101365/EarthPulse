---
source: EarthPulse Machine Learning Engineering Spec
title: Zero-Leakage Spatial Block Holdout ML and XGBoost Engine
category: machine_learning
dataset: ML_XGBOOST
satellite: Multi-Sensor
date: 2024-03-05
chunk_index: 0
---

# Zero-Leakage Spatial Block Holdout ML and XGBoost Engine

## The Problem of Spatial Autocorrelation Leakage
In wildfire geospatial machine learning, traditional random K-Fold cross-validation suffers from severe data leakage. According to Tobler's First Law of Geography, spatial coordinates near an active fire share almost identical fuel moisture, vegetation density, and wind vectors. 
When training and test samples are split randomly, the model 'memorizes' test point outcomes from immediate neighbors, producing artificially inflated metrics (ROC-AUC > 0.96) that collapse in real-world deployment on unseen regions.

## EarthPulse Spatial Block Holdout Strategy
EarthPulse enforces **Spatial Block Holdout**:
- The geographic domain is partitioned into contiguous 50 km × 50 km spatial grid blocks.
- Entire blocks are assigned to either the training set or test set without geographic overlap.
- This forces the model to generalize fire spread dynamics to completely unseen terrain.

## Model Architecture
- Algorithm: XGBoost Classifier with ARM64 histogram tree-building engine (`hist`).
- Hardware Acceleration: Apple Metal Performance Shaders (MPS) PyTorch GPU training.
- Class Weighting: `scale_pos_weight = 14.2` to counter severe wildfire sparsity (less than 2% of pixels are active fires).
- Evaluation Metric: PR-AUC (Precision-Recall AUC = 0.84), which penalizes false alarms in skewed data far more reliably than ROC-AUC.
