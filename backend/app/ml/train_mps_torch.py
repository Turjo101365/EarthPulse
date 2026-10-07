"""
Apple Silicon MPS (Metal Performance Shaders) GPU Deep Learning Trainer
Trains a PyTorch Wildfire Risk & Propagation Neural Network directly on
Mac GPU ('mps:0') using the exact same NASA FIRMS harmonized dataset.

Compares Apple Metal MPS GPU performance vs CPU execution.
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, f1_score, accuracy_score

from ..harmonizer.firms_loader import load_all_firms_data
from .dataset_builder import prepare_firms_training_matrices, FEATURE_NAMES

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"
TORCH_MODEL_PATH = WEIGHTS_DIR / "mps_firms_model.pt"
TORCH_METADATA_PATH = WEIGHTS_DIR / "mps_firms_metadata.json"


class WildfireMPSNet(nn.Module):
    """Deep Neural Network optimized for Apple Silicon MPS execution."""
    def __init__(self, input_dim: int = 11, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.SiLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.SiLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_dim // 2, 16),
            nn.SiLU(),
            nn.Linear(16, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def train_firms_mps(
    max_samples_per_sensor: Optional[int] = None,
    epochs: int = 15,
    batch_size: int = 512,
    learning_rate: float = 0.003,
    save_model: bool = True
) -> Tuple[nn.Module, Dict[str, Any]]:
    """
    Trains PyTorch model on Apple Silicon MPS ('mps:0') GPU using real NASA FIRMS data.
    """
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    if not torch.backends.mps.is_available():
        device = torch.device("cpu")
        device_name = "CPU (MPS not available)"
    else:
        device = torch.device("mps")
        device_name = "Apple Metal Performance Shaders (MPS:0)"

    print("=" * 70)
    print("⚡ APPLE SILICON MPS (METAL PERFORMANCE SHADERS) GPU TRAINING")
    print("=" * 70)
    print(f"Device: {device_name}")
    print(f"PyTorch Version: {torch.__version__}")
    print("-" * 70)

    # 1. Load Data
    t0 = time.time()
    print("[1/4] Loading NASA FIRMS feeds (MODIS & VIIRS)...")
    records, ingest_stats = load_all_firms_data(
        download_if_missing=True,
        max_samples_per_sensor=max_samples_per_sensor
    )
    print(f"      Loaded {len(records):,} records in {round(time.time() - t0, 2)}s.")

    # 2. Build Matrices & Standardize
    print("[2/4] Preparing features and standardizing for MPS Neural Network...")
    X_train_raw, y_train_raw, X_test_raw, y_test_raw, meta = prepare_firms_training_matrices(records)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw).astype(np.float32)
    X_test = scaler.transform(X_test_raw).astype(np.float32)

    # Convert to PyTorch Tensors
    train_dataset = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train_raw.astype(np.float32)))
    test_dataset = TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_test_raw.astype(np.float32)))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size * 2, shuffle=False)

    # 3. Model on MPS Device
    print(f"[3/4] Initializing WildfireMPSNet and placing weights on {device}...")
    model = WildfireMPSNet(input_dim=X_train.shape[1]).to(device)

    # Calculate pos_weight for BCEWithLogitsLoss
    pos_weight = torch.tensor([(1.0 - meta["positive_class_ratio"]) / max(0.01, meta["positive_class_ratio"])], device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    t_train_start = time.time()
    epoch_losses = []

    model.train()
    for epoch in range(1, epochs + 1):
        running_loss = 0.0
        n_batches = 0
        for bx, by in train_loader:
            bx = bx.to(device)
            by = by.to(device)

            optimizer.zero_grad()
            logits = model(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            n_batches += 1

        avg_loss = round(running_loss / max(1, n_batches), 4)
        epoch_losses.append(avg_loss)
        if epoch % 3 == 0 or epoch == epochs:
            print(f"      Epoch [{epoch:>2}/{epochs}] — MPS Loss: {avg_loss:.4f}")

    train_duration = round(time.time() - t_train_start, 2)
    print(f"      Completed {epochs} epochs on Apple MPS in {train_duration}s!")

    # 4. Evaluation on MPS
    print("[4/4] Evaluating MPS model on holdout test partition...")
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for bx, by in test_loader:
            bx = bx.to(device)
            logits = model(bx)
            probs = torch.sigmoid(logits).cpu().numpy()
            all_preds.extend(probs.tolist())
            all_targets.extend(by.numpy().tolist())

    y_test = np.array(all_targets)
    y_pred_probs = np.array(all_preds)
    y_pred = (y_pred_probs >= 0.5).astype(int)

    precision, recall, _ = precision_recall_curve(y_test, y_pred_probs)
    pr_auc_val = round(float(auc(recall, precision)), 4)
    roc_auc_val = round(float(roc_auc_score(y_test, y_pred_probs)), 4)
    acc = round(float(accuracy_score(y_test, y_pred)), 4)
    f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)

    report = {
        "status": "SUCCESS",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "device": str(device),
        "device_name": device_name,
        "is_mps": str(device) == "mps",
        "dataset": {
            "total_records": len(records),
            "ingest_stats": ingest_stats,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        },
        "training": {
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "train_duration_sec": train_duration,
            "loss_history": epoch_losses,
        },
        "metrics": {
            "pr_auc": pr_auc_val,
            "roc_auc": roc_auc_val,
            "accuracy": acc,
            "f1_score": f1,
        }
    }

    print("-" * 70)
    print(f"🚀 Apple MPS GPU PR-AUC  : {pr_auc_val}")
    print(f"🚀 Apple MPS GPU ROC-AUC : {roc_auc_val}")
    print(f"🚀 Accuracy             : {acc * 100:.2f}% | F1-Score: {f1}")
    print("=" * 70)

    if save_model:
        torch.save({
            "model_state_dict": model.state_dict(),
            "scaler_mean": scaler.mean_.tolist(),
            "scaler_scale": scaler.scale_.tolist(),
            "feature_names": FEATURE_NAMES,
            "metrics": report["metrics"],
        }, str(TORCH_MODEL_PATH))
        with open(TORCH_METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"💾 PyTorch MPS weights saved to: {TORCH_MODEL_PATH}")

    return model, report


if __name__ == "__main__":
    max_samples = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        max_samples = int(sys.argv[1])
    train_firms_mps(max_samples_per_sensor=max_samples)
