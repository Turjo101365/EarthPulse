"""
Spatial ML Module: Zero-Leakage XGBoost Fire Spread Prediction
50km Spatial Block Holdout, Dynamic Spread Contours, and PR-AUC Evaluation
"""

from .spatial_split import spatial_block_split
from .model import FirePropagationModel, fire_ml_model
from .predict import FireSpreadPredictor, fire_spread_predictor

__all__ = [
    "spatial_block_split",
    "FirePropagationModel",
    "fire_ml_model",
    "FireSpreadPredictor",
    "fire_spread_predictor"
]
