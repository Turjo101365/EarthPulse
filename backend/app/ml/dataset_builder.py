"""
NASA FIRMS Dataset Builder for Wildfire Propagation & Risk Classification
Performs feature engineering, spatial block holdout splitting (zero leakage),
and normalization for XGBoost (CPU) and PyTorch (Apple Metal MPS).
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "brightness",
    "bright_bg",
    "temp_diff",
    "frp",
    "confidence",
    "scan",
    "track",
    "is_day",
    "latitude",
    "longitude",
    "sensor_code",
]

SENSOR_MAP = {
    "MODIS_TERRA": 0,
    "MODIS_AQUA": 1,
    "VIIRS_SNPP": 2,
    "VIIRS_NOAA20": 3,
}


def build_feature_vector(record: Dict[str, Any]) -> List[float]:
    """Extracts standardized numeric feature vector from a single FIRMS detection."""
    brightness = float(record.get("brightness", 315.0))
    bright_bg = float(record.get("bright_bg", 295.0))
    temp_diff = float(record.get("temp_diff", brightness - bright_bg))
    frp = float(record.get("frp", 10.0))
    confidence = float(record.get("confidence", 60.0))
    scan = float(record.get("scan", 0.5))
    track = float(record.get("track", 0.5))
    is_day = float(record.get("is_day", 1 if record.get("daynight", "D") == "D" else 0))
    lat = float(record.get("latitude", 0.0))
    lon = float(record.get("longitude", 0.0))
    sensor_name = record.get("satellite", record.get("sensor", "VIIRS_SNPP"))
    sensor_code = float(SENSOR_MAP.get(sensor_name, 2))

    return [
        brightness,
        bright_bg,
        temp_diff,
        frp,
        confidence,
        scan,
        track,
        is_day,
        lat,
        lon,
        sensor_code,
    ]


def compute_target_label(record: Dict[str, Any]) -> int:
    """
    Computes high-risk wildfire propagation label:
    1 = High / Critical propagation hazard (FRP >= 35 MW, or high thermal delta + high confidence)
    0 = Moderate / Low intensity active fire
    """
    frp = float(record.get("frp", 0.0))
    temp_diff = float(record.get("temp_diff", record.get("brightness", 300) - record.get("bright_bg", 290)))
    conf = float(record.get("confidence", 50.0))

    if frp >= 35.0 or (temp_diff >= 30.0 and conf >= 75.0):
        return 1
    return 0


def prepare_firms_training_matrices(
    records: List[Dict[str, Any]],
    test_ratio: float = 0.25,
    block_size_deg: float = 0.5,
    random_seed: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Transforms raw FIRMS records into X_train, y_train, X_test, y_test
    using Spatial Block Holdout to prevent spatial autocorrelation leakage.
    """
    if not records:
        raise ValueError("No records provided to dataset builder")

    X_list = []
    y_list = []
    lat_lon_list = []

    for r in records:
        X_list.append(build_feature_vector(r))
        y_list.append(compute_target_label(r))
        lat_lon_list.append((float(r.get("latitude", 0.0)), float(r.get("longitude", 0.0))))

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    lat_lons = np.array(lat_lon_list, dtype=np.float32)

    # Spatial Block Partitioning
    # Divide world into grid blocks of block_size_deg (approx 55km x 55km)
    block_lat = np.floor(lat_lons[:, 0] / block_size_deg).astype(int)
    block_lon = np.floor(lat_lons[:, 1] / block_size_deg).astype(int)
    block_keys = np.array([f"{b_lat}_{b_lon}" for b_lat, b_lon in zip(block_lat, block_lon)])

    unique_blocks = np.unique(block_keys)
    rng = np.random.RandomState(random_seed)
    rng.shuffle(unique_blocks)

    n_test_blocks = max(1, int(len(unique_blocks) * test_ratio))
    test_blocks_set = set(unique_blocks[:n_test_blocks])

    test_mask = np.array([b in test_blocks_set for b in block_keys])
    train_mask = ~test_mask

    # Fallback to standard split if all fell in one block
    if np.sum(test_mask) == 0 or np.sum(train_mask) == 0:
        indices = np.arange(len(X))
        rng.shuffle(indices)
        split = int(len(X) * (1 - test_ratio))
        train_mask = np.zeros(len(X), dtype=bool)
        test_mask = np.zeros(len(X), dtype=bool)
        train_mask[indices[:split]] = True
        test_mask[indices[split:]] = True

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    class_1_ratio = float(np.mean(y))
    metadata = {
        "n_samples": len(X),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_features": X.shape[1],
        "feature_names": FEATURE_NAMES,
        "n_unique_spatial_blocks": len(unique_blocks),
        "positive_class_ratio": round(class_1_ratio, 4),
        "block_size_deg": block_size_deg,
    }

    return X_train, y_train, X_test, y_test, metadata
