"""
Spatial Block Cross-Validation & Holdout Splitter
Eliminates spatial autocorrelation leakage by ensuring that entire
geographic blocks (e.g. 50km x 50km) are assigned strictly to either train or test.
"""

from typing import List, Dict, Any, Tuple
import math
from collections import defaultdict
import numpy as np

def spatial_block_split(
    records: List[Dict[str, Any]],
    block_km: float = 50.0,
    test_ratio: float = 0.25,
    random_state: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Partitions records into spatial blocks of approximately `block_km` x `block_km`.
    Assigns whole blocks randomly into train and test partitions.
    
    Returns:
        train_records, test_records, split_metadata
    """
    if not records:
        return [], [], {"total_blocks": 0, "train_blocks": 0, "test_blocks": 0}

    # 1 degree of latitude is ~111 km
    lat_deg_per_block = block_km / 111.0

    blocks = defaultdict(list)
    for r in records:
        lat = float(r["latitude"])
        lon = float(r["longitude"])

        # Longitudinal distance per degree shrinks with cos(lat)
        lon_deg_per_block = block_km / (111.0 * max(0.1, math.cos(math.radians(lat))))

        block_y = int(math.floor(lat / lat_deg_per_block))
        block_x = int(math.floor(lon / lon_deg_per_block))
        blocks[(block_y, block_x)].append(r)

    block_keys = list(blocks.keys())
    rng = np.random.RandomState(random_state)
    rng.shuffle(block_keys)

    n_test_blocks = max(1, int(len(block_keys) * test_ratio)) if len(block_keys) > 1 else 0
    test_block_keys = set(block_keys[:n_test_blocks])
    train_block_keys = set(block_keys[n_test_blocks:])

    train_records = []
    test_records = []

    for k in train_block_keys:
        train_records.extend(blocks[k])
    for k in test_block_keys:
        test_records.extend(blocks[k])

    metadata = {
        "block_km": block_km,
        "total_records": len(records),
        "total_blocks": len(block_keys),
        "train_blocks": len(train_block_keys),
        "test_blocks": len(test_block_keys),
        "train_records": len(train_records),
        "test_records": len(test_records),
    }

    return train_records, test_records, metadata
