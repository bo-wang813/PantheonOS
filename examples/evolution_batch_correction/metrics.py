"""
Shared evaluation metrics for batch correction algorithm evolution.

This module provides common evaluation functions used by both Harmony and Scanorama
evaluators for measuring batch correction quality:

1. Data loading utilities for TMA datasets
2. Batch mixing score (kNN-based)
3. Biological conservation score (silhouette-based)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score
from typing import Tuple


def load_tma_data(
    data_dir: Path,
    split: str = "train",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load TMA data with real cell type labels.

    Args:
        data_dir: Directory containing the data files
        split: Which split to load ("train", "val", or "test")

    Returns:
        X: Features (n_cells x 30)
        batch_labels: Batch labels (donor)
        celltype_labels: True cell type labels
    """
    df = pd.read_csv(data_dir / f"tma_8000_{split}.csv")
    X = df.iloc[:, :30].values  # PC1-PC30
    batch_labels = df["donor"].values
    celltype_labels = df["celltype"].values

    return X, batch_labels, celltype_labels


def compute_batch_mixing_score(
    X: np.ndarray,
    batch_labels: np.ndarray,
    k: int = 50,
) -> float:
    """
    Compute batch mixing score using k-nearest neighbors.

    Measures how well different batches are mixed in the embedding.
    Higher score = better mixing.

    Args:
        X: Embedding (n_cells x n_features)
        batch_labels: Batch assignments
        k: Number of neighbors

    Returns:
        Mixing score in [0, 1]
    """
    n_cells = X.shape[0]
    unique_batches = np.unique(batch_labels)

    # Expected proportion of each batch
    expected_props = np.array([
        np.sum(batch_labels == b) / n_cells
        for b in unique_batches
    ])

    # Find k nearest neighbors
    nn = NearestNeighbors(n_neighbors=min(k + 1, n_cells), algorithm="auto")
    nn.fit(X)
    _, indices = nn.kneighbors(X)

    # For each cell, compute batch proportions in neighborhood
    mixing_scores = []
    for i in range(n_cells):
        neighbor_batches = batch_labels[indices[i, 1:]]  # Exclude self
        observed_props = np.array([
            np.sum(neighbor_batches == b) / k
            for b in unique_batches
        ])

        # Compare to expected (lower deviation = better mixing)
        score = 1 - np.sqrt(np.mean((observed_props - expected_props) ** 2))
        mixing_scores.append(max(0, score))

    return np.mean(mixing_scores)


def compute_bio_conservation_score(
    X_corrected: np.ndarray,
    X_original: np.ndarray,
    true_labels: np.ndarray,
) -> float:
    """
    Compute biological structure conservation score using silhouette score.

    Measures how well the biological clusters are separated after correction.
    Higher silhouette = better separation of cell types.

    Args:
        X_corrected: Corrected embedding
        X_original: Original embedding (unused, kept for API compatibility)
        true_labels: True biological labels (cell types)

    Returns:
        Silhouette score normalized to [0, 1]
    """
    try:
        if len(np.unique(true_labels)) > 1:
            # Compute silhouette score on corrected data
            silhouette = silhouette_score(X_corrected, true_labels)
            # Normalize from [-1, 1] to [0, 1]
            return (silhouette + 1) / 2
        else:
            return 0.5
    except Exception:
        return 0.5


def get_default_fitness_weights() -> dict:
    """
    Get default fitness weights for batch correction evaluation.

    Returns:
        Dictionary with metric weights
    """
    return {
        "mixing_score": 0.45,
        "bio_conservation_score": 0.45,
        "speed_score": 0.05,
        "convergence_score": 0.05,
    }
