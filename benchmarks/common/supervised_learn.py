"""
Common supervised learning utilities for benchmarks.

Shared logic for memory augmentation with grading information.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any


def append_grading_to_memory_simple(
    memory_path: Path,
    task_result: dict,
    groundtruth_key: str = "ground_truth",
    answer_key: str = "agent_answer",
) -> Path:
    """
    Append grading information to memory (simple version for single-answer tasks).
    
    Args:
        memory_path: Path to original memory JSON file
        task_result: Task result dict with answer and ground truth
        groundtruth_key: Key for ground truth in task_result
        answer_key: Key for agent answer in task_result
        
    Returns:
        Path to supervised memory file (*.supervised.json)
    """
    with open(memory_path, 'r') as f:
        data = json.load(f)
    
    # Extract values
    submitted = task_result.get(answer_key, "")
    ground_truth = task_result.get(groundtruth_key, "")
    tolerance = task_result.get("tolerance", 0.0)
    
    # Calculate correctness
    is_correct = _check_correctness(submitted, ground_truth, tolerance)
    
    # Format grading message
    content = f"""## Grading Result

**Agent's Submitted Answer:**
{submitted}

**Ground Truth Answer:**
{ground_truth}

**Tolerance:**
{tolerance if tolerance else "N/A"}

**Result:**
{'✓ CORRECT' if is_correct else '✗ INCORRECT'}
"""
    
    data["messages"].append({"role": "user", "content": content})
    
    # Save supervised memory
    supervised_path = memory_path.with_suffix(".supervised.json")
    with open(supervised_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return supervised_path


def _check_correctness(
    submitted: Any,
    ground_truth: Any,
    tolerance: float = 0.0
) -> bool:
    """
    Check if submitted answer matches ground truth.
    
    Args:
        submitted: Submitted answer
        ground_truth: Ground truth answer
        tolerance: Tolerance for numerical comparison
        
    Returns:
        True if correct, False otherwise
    """
    # Try numerical comparison
    try:
        submitted_val = float(str(submitted).strip())
        gt_val = float(ground_truth)
        
        if tolerance > 0:
            return abs(submitted_val - gt_val) <= abs(gt_val * tolerance)
        else:
            return abs(submitted_val - gt_val) < 1e-6
    except (ValueError, TypeError):
        pass
    
    # String comparison
    return str(submitted).strip().lower() == str(ground_truth).strip().lower()


def load_groundtruth_from_report(report_path: Path) -> Dict[str, Any]:
    """
    Load groundtruth data from report.json.
    
    Args:
        report_path: Path to report.json
        
    Returns:
        Dict mapping task_id -> task_result
    """
    with open(report_path) as f:
        data = json.load(f)
    
    results = data.get("results", [])
    return {r["id"]: r for r in results}
