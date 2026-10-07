"""
NASA FIRMS Active Fire XGBoost Model Trainer
Trains XGBoost wildfire propagation classifier on real NASA FIRMS multi-sensor data:
- MODIS (Terra & Aqua, 1km)
- VIIRS (Suomi-NPP & NOAA-20, 375m)

Optimized for Apple Silicon macOS (ARM64 multi-core SIMD with tree_method='hist').
Includes hardware detection and MPS diagnostic logging.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
)

from ..harmonizer.firms_loader import load_all_firms_data
from .dataset_builder import prepare_firms_training_matrices, FEATURE_NAMES

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"
MODEL_PATH = WEIGHTS_DIR / "xgboost_firms_model.json"
METADATA_PATH = WEIGHTS_DIR / "xgboost_firms_metadata.json"


def check_hardware_acceleration() -> Dict[str, Any]:
    """
    Inspects system hardware acceleration capabilities on macOS Apple Silicon.
    Clarifies XGBoost device support vs Apple Metal Performance Shaders (MPS).
    """
    has_torch = False
    mps_available = False
    try:
        import torch
        has_torch = True
        mps_available = bool(torch.backends.mps.is_available())
    except ImportError:
        pass

    info = {
        "platform": sys.platform,
        "is_apple_silicon": sys.platform == "darwin" and os.uname().machine == "arm64",
        "mps_hardware_present": mps_available,
        "xgboost_mps_backend": False,  # XGBoost upstream has no Metal MPS kernel
        "xgboost_engine": "Apple Silicon ARM64 NEON multi-threaded CPU (tree_method='hist')",
        "torch_mps_accelerator_ready": mps_available,
    }
    return info


def train_firms_xgboost(
    max_samples_per_sensor: Optional[int] = None,
    test_ratio: float = 0.25,
    n_estimators: int = 300,
    learning_rate: float = 0.05,
    max_depth: int = 6,
    save_model: bool = True
) -> Tuple[XGBClassifier, Dict[str, Any]]:
    """
    Loads NASA FIRMS observations and trains an optimized XGBoost model.
    """
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    hw_info = check_hardware_acceleration()

    print("=" * 70)
    print("🔥 NASA FIRMS MULTI-SENSOR ACTIVE FIRE — XGBOOST TRAINING")
    print("=" * 70)
    print(f"System: macOS ARM64 | Apple Silicon: {hw_info['is_apple_silicon']}")
    print(f"Apple Metal MPS GPU available: {hw_info['mps_hardware_present']}")
    print(f"XGBoost Execution Engine: {hw_info['xgboost_engine']}")
    print("Note: Official XGBoost does not support 'device=mps' directly (only CUDA).")
    print("      Running parallel ARM64 vector execution across all cores (n_jobs=-1).")
    print("-" * 70)

    # 1. Load Data
    t0 = time.time()
    print("[1/4] Ingesting NASA FIRMS records (MODIS + VIIRS SNPP + VIIRS NOAA-20)...")
    records, ingest_stats = load_all_firms_data(
        download_if_missing=True,
        max_samples_per_sensor=max_samples_per_sensor
    )
    print(f"      Loaded {len(records):,} records from NASA FIRMS in {round(time.time() - t0, 2)}s.")
    print(f"      Breakdown: MODIS={ingest_stats['modis_count']:,} | VIIRS SNPP={ingest_stats['viirs_snpp_count']:,} | VIIRS NOAA-20={ingest_stats['viirs_noaa20_count']:,}")

    # 2. Build Dataset with Spatial Block Holdout
    t1 = time.time()
    print("[2/4] Engineering features and constructing Spatial Block Holdout split (zero leakage)...")
    X_train, y_train, X_test, y_test, meta = prepare_firms_training_matrices(
        records,
        test_ratio=test_ratio,
        block_size_deg=0.5
    )
    print(f"      Train samples: {len(X_train):,} | Test samples: {len(X_test):,}")
    print(f"      Spatial blocks: {meta['n_unique_spatial_blocks']} | High-risk positive class ratio: {round(meta['positive_class_ratio'] * 100, 2)}%")

    # Calculate class weight for imbalance
    pos_ratio = meta["positive_class_ratio"]
    scale_pos = max(1.0, (1.0 - pos_ratio) / max(0.01, pos_ratio))

    # 3. Initialize & Train Model
    t2 = time.time()
    print("[3/4] Fitting XGBoost Classifier with tree_method='hist' and n_jobs=-1...")

    model = XGBClassifier(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=round(scale_pos, 2),
        tree_method="hist",
        n_jobs=-1,
        eval_metric="aucpr",
        random_state=42
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    train_duration = round(time.time() - t2, 2)
    print(f"      Training complete in {train_duration}s!")

    # 4. Evaluation
    print("[4/4] Evaluating model performance...")
    y_pred_probs = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_probs >= 0.5).astype(int)

    precision, recall, _ = precision_recall_curve(y_test, y_pred_probs)
    pr_auc_val = round(float(auc(recall, precision)), 4)
    roc_auc_val = round(float(roc_auc_score(y_test, y_pred_probs)), 4)
    acc = round(float(accuracy_score(y_test, y_pred)), 4)
    f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Feature Importances
    feat_importances = {
        name: round(float(imp), 4)
        for name, imp in sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: x[1], reverse=True)
    }

    report = {
        "status": "SUCCESS",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": hw_info,
        "dataset": {
            "total_records": len(records),
            "ingest_stats": ingest_stats,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "spatial_blocks": meta["n_unique_spatial_blocks"],
            "positive_class_ratio": meta["positive_class_ratio"],
        },
        "hyperparameters": {
            "n_estimators": n_estimators,
            "learning_rate": learning_rate,
            "max_depth": max_depth,
            "scale_pos_weight": round(scale_pos, 2),
            "tree_method": "hist",
            "n_jobs": -1,
        },
        "metrics": {
            "pr_auc": pr_auc_val,
            "roc_auc": roc_auc_val,
            "accuracy": acc,
            "f1_score": f1,
            "confusion_matrix": cm,
            "train_duration_sec": train_duration,
        },
        "feature_importances": feat_importances,
    }

    print("-" * 70)
    print(f"🎯 Validation PR-AUC  : {pr_auc_val}")
    print(f"🎯 Validation ROC-AUC : {roc_auc_val}")
    print(f"🎯 Accuracy          : {acc * 100:.2f}% | F1-Score: {f1}")
    print("Top Feature Importances:")
    for feat, imp in list(feat_importances.items())[:6]:
        print(f"   • {feat:<15}: {imp:.4f}")
    print("=" * 70)

    # Save artifacts
    if save_model:
        model.save_model(str(MODEL_PATH))
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"💾 Model saved to: {MODEL_PATH}")
        print(f"📊 Metadata saved to: {METADATA_PATH}")

    return model, report


if __name__ == "__main__":
    max_samples = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        max_samples = int(sys.argv[1])
    train_firms_xgboost(max_samples_per_sensor=max_samples)
