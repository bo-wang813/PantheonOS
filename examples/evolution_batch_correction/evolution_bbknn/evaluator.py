"""
Evaluator for BBKNN Algorithm Evolution.

This evaluator measures:
1. Integration quality (how well batches are mixed)
2. Biological variance preservation (how well structure is preserved)
3. Execution speed

BBKNN works by modifying the KNN graph rather than the embedding directly.
We evaluate by computing a spectral embedding from the corrected graph.
"""

import numpy as np
import pandas as pd
import time
import sys
import os
import importlib.util
from pathlib import Path
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score
from sklearn.manifold import SpectralEmbedding
from typing import Dict, Any, Tuple


def _get_data_dir() -> Path:
    """Get the shared data directory path."""
    env_data_dir = os.environ.get("BBKNN_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir)
    return Path(__file__).parent.parent / "data"


def load_tma_data(
    data_dir: Path,
    split: str = "train",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load TMA data with real cell type labels."""
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
    """Compute batch mixing score using k-nearest neighbors."""
    n_cells = X.shape[0]
    unique_batches = np.unique(batch_labels)

    expected_props = np.array([
        np.sum(batch_labels == b) / n_cells
        for b in unique_batches
    ])

    nn = NearestNeighbors(n_neighbors=min(k + 1, n_cells), algorithm="auto")
    nn.fit(X)
    _, indices = nn.kneighbors(X)

    mixing_scores = []
    for i in range(n_cells):
        neighbor_batches = batch_labels[indices[i, 1:]]
        observed_props = np.array([
            np.sum(neighbor_batches == b) / k
            for b in unique_batches
        ])
        score = 1 - np.sqrt(np.mean((observed_props - expected_props) ** 2))
        mixing_scores.append(max(0, score))

    return np.mean(mixing_scores)


def compute_bio_conservation_score(
    X_corrected: np.ndarray,
    X_original: np.ndarray,
    true_labels: np.ndarray,
) -> float:
    """Compute biological structure conservation score using silhouette score."""
    try:
        if len(np.unique(true_labels)) > 1:
            silhouette = silhouette_score(X_corrected, true_labels)
            return (silhouette + 1) / 2
        else:
            return 0.5
    except Exception:
        return 0.5


def graph_to_embedding(
    connectivities,
    n_components: int = 30,
) -> np.ndarray:
    """
    Convert a connectivity graph to an embedding using spectral embedding.

    Args:
        connectivities: Sparse connectivity matrix from BBKNN
        n_components: Number of dimensions for the embedding

    Returns:
        Embedding array (n_cells x n_components)
    """
    # Make the matrix symmetric
    conn_sym = (connectivities + connectivities.T) / 2

    # Use spectral embedding
    se = SpectralEmbedding(
        n_components=n_components,
        affinity='precomputed',
        random_state=42,
    )

    # SpectralEmbedding expects affinity matrix (similarity)
    # connectivities from BBKNN is already a similarity matrix
    embedding = se.fit_transform(conn_sym.toarray())

    return embedding


def evaluate(workspace_path: str) -> Dict[str, Any]:
    """
    Evaluate the BBKNN implementation on TMA training data.

    Args:
        workspace_path: Path to the workspace containing bbknn package

    Returns:
        Dictionary with metrics including 'combined_score'
    """
    workspace = Path(workspace_path)

    # Load the bbknn module from workspace
    bbknn_path = workspace / "bbknn"
    if not bbknn_path.exists():
        return {
            "combined_score": 0.0,
            "error": "bbknn package not found",
        }

    try:
        # Import matrix module first
        matrix_path = bbknn_path / "matrix.py"
        spec_matrix = importlib.util.spec_from_file_location(
            "bbknn.matrix", matrix_path
        )
        matrix_module = importlib.util.module_from_spec(spec_matrix)
        sys.modules["bbknn.matrix"] = matrix_module
        spec_matrix.loader.exec_module(matrix_module)

        # Import main bbknn module
        init_path = bbknn_path / "__init__.py"
        spec = importlib.util.spec_from_file_location("bbknn", init_path)
        bbknn_module = importlib.util.module_from_spec(spec)
        sys.modules["bbknn"] = bbknn_module
        spec.loader.exec_module(bbknn_module)

    except Exception as e:
        return {
            "combined_score": 0.0,
            "error": f"Failed to load bbknn: {e}",
        }

    # Load TMA training data
    data_dir = _get_data_dir()

    try:
        X_train, batch_train, celltype_train = load_tma_data(data_dir, split="train")
    except Exception as e:
        return {
            "combined_score": 0.0,
            "error": f"Failed to load TMA data: {e}",
        }

    n_cells = len(X_train)

    # Run bbknn and measure time
    try:
        start_time = time.time()

        # Use the matrix.bbknn function which works with numpy arrays
        distances, connectivities, params = matrix_module.bbknn(
            pca=X_train,
            batch_list=batch_train,
            neighbors_within_batch=3,
            n_pcs=30,
            computation='cKDTree',  # Use exact KNN (no annoy dependency)
            metric='euclidean',
        )

        execution_time = time.time() - start_time

        # Convert graph to embedding for evaluation
        X_corrected = graph_to_embedding(connectivities, n_components=30)

    except Exception as e:
        return {
            "combined_score": 0.0,
            "error": f"BBKNN execution failed: {e}",
        }

    # Compute metrics
    try:
        # Batch mixing (higher = better)
        mixing_score = compute_batch_mixing_score(X_corrected, batch_train)

        # Biological conservation using real cell type labels
        bio_score = compute_bio_conservation_score(
            X_corrected, X_train, celltype_train
        )

        # Speed score (faster = better)
        speed_score = 1.0 / (1 + execution_time)

        # Combined score
        combined_score = (
            0.45 * mixing_score +
            0.45 * bio_score +
            0.10 * speed_score
        )

        return {
            "combined_score": combined_score,
            "mixing_score": mixing_score,
            "bio_conservation_score": bio_score,
            "speed_score": speed_score,
            "execution_time": execution_time,
            "n_cells": n_cells,
            "n_batches": len(np.unique(batch_train)),
            "dataset": "tma_train",
        }

    except Exception as e:
        return {
            "combined_score": 0.1,
            "error": f"Metric computation failed: {e}",
        }


def _evaluate_on_split(workspace_path: str, split: str) -> Dict[str, Any]:
    """Evaluate on a specific data split."""
    workspace = Path(workspace_path)

    bbknn_path = workspace / "bbknn"
    if not bbknn_path.exists():
        return {
            "combined_score": 0.0,
            "error": "bbknn package not found",
        }

    try:
        matrix_path = bbknn_path / "matrix.py"
        spec_matrix = importlib.util.spec_from_file_location(
            "bbknn.matrix", matrix_path
        )
        matrix_module = importlib.util.module_from_spec(spec_matrix)
        sys.modules["bbknn.matrix"] = matrix_module
        spec_matrix.loader.exec_module(matrix_module)

    except Exception as e:
        return {
            "combined_score": 0.0,
            "error": f"Failed to load bbknn: {e}",
        }

    data_dir = _get_data_dir()

    try:
        X, batch_labels, celltype_labels = load_tma_data(data_dir, split=split)
    except Exception as e:
        return {
            "combined_score": 0.0,
            "error": f"Failed to load TMA {split} data: {e}",
        }

    try:
        start_time = time.time()

        distances, connectivities, params = matrix_module.bbknn(
            pca=X,
            batch_list=batch_labels,
            neighbors_within_batch=3,
            n_pcs=30,
            computation='cKDTree',
            metric='euclidean',
        )

        execution_time = time.time() - start_time
        X_corrected = graph_to_embedding(connectivities, n_components=30)

    except Exception as e:
        return {
            "combined_score": 0.0,
            "error": f"BBKNN execution failed: {e}",
        }

    try:
        mixing_score = compute_batch_mixing_score(X_corrected, batch_labels)
        bio_score = compute_bio_conservation_score(X_corrected, X, celltype_labels)
        speed_score = 1.0 / (1 + execution_time)

        combined_score = (
            0.45 * mixing_score +
            0.45 * bio_score +
            0.10 * speed_score
        )

        return {
            "combined_score": combined_score,
            "mixing_score": mixing_score,
            "bio_conservation_score": bio_score,
            "speed_score": speed_score,
            "execution_time": execution_time,
            "dataset": f"tma_{split}",
        }

    except Exception as e:
        return {
            "combined_score": 0.1,
            "error": f"Metric computation failed: {e}",
        }


def evaluate_on_validation(workspace_path: str) -> Dict[str, Any]:
    """Evaluate on TMA VALIDATION set."""
    return _evaluate_on_split(workspace_path, "val")


def evaluate_on_test(workspace_path: str) -> Dict[str, Any]:
    """Evaluate on TMA TEST set."""
    return _evaluate_on_split(workspace_path, "test")


if __name__ == "__main__":
    workspace = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("BBKNN Evaluator Test (TMA Data)")
    print("=" * 60)
    print(f"Workspace: {workspace}")

    print("\n" + "-" * 60)
    print("TRAINING SET Evaluation:")
    print("-" * 60)
    result = evaluate(workspace)
    for key, value in result.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        elif isinstance(value, int):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
