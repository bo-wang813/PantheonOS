"""
BixBench Supervised Learning - Memory augmentation for supervised learning.

This module provides utilities to augment memory logs with grading information
and ground truth data to enable supervised learning.
"""
import json
from pathlib import Path
from typing import Optional

from pantheon.utils.log import logger



def append_grading_to_memory(
    memory_path: Path,
    capsule_result: dict,
    inject_notebook: bool = False,
    gt_notebook_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Append grading information to memory for supervised learning.
    
    Args:
        memory_path: Path to original memory JSON file
        capsule_result: Capsule result dict with 'answers' and 'grading'
        inject_notebook: Whether to inject GT notebook (Level 2)
        gt_notebook_path: Path to GT notebook (if exists)
        output_dir: Optional output directory for supervised memory file.
                   If None, saves to same directory as memory_path.
        
    Returns:
        Path to supervised memory file (*.supervised.json)
    """
    with open(memory_path, 'r') as f:
        data = json.load(f)
    
    submitted = capsule_result.get("answers", {})
    grading = capsule_result.get("grading", {})
    
    # Extract groundtruth from grading
    groundtruth = load_groundtruth_from_result(capsule_result, memory_path.parent)

    
    # Level 1: Grading information
    content = f"""## Grading Result

**Agent's Submitted Answers:**
{json.dumps(submitted, indent=2)}

**Ground Truth Answers:**
{json.dumps(groundtruth, indent=2)}

**Per-Question Grading:**
{_format_grading(grading)}

**Overall Accuracy:** {grading.get('correct', 0)}/{grading.get('total', 0)} ({grading.get('accuracy', 0):.1%})
"""
    
    # Level 2: Add GT Notebook (if exists)
    if inject_notebook:
        if gt_notebook_path and gt_notebook_path.exists():
            notebook_content = extract_notebook_analysis(gt_notebook_path)
            content += f"""

## Reference Solution (from expert notebook)

{notebook_content}
"""
        else:
            # Graceful degradation: Not all capsules have GT notebooks
            # This is expected - only warn, don't error
            capsule_id = capsule_result.get("capsule_id", "unknown")
            logger.warning(
                f"Level 2 requested but no GT notebook found for {capsule_id}. "
                f"Falling back to Level 1 (grading only). "
                f"This is normal for capsules without expert notebooks."
            )

    
    data["messages"].append({"role": "user", "content": content})
    
    # Save supervised memory
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        supervised_path = output_dir / f"{memory_path.stem}.supervised.json"
    else:
        supervised_path = memory_path.with_suffix(".supervised.json")
    
    with open(supervised_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return supervised_path


def load_groundtruth_from_result(capsule_result: dict, memory_dir: Path = None) -> dict:
    """
    Extract groundtruth from capsule result's grading.
    
    Args:
        capsule_result: Capsule result dict with grading information
        memory_dir: Optional directory containing bix-*-q*.json files for fallback
        
    Returns:
        Dict of question_id -> target_answer
    """
    grading = capsule_result.get("grading", {})
    questions = grading.get("questions", {})
    targets = {}
    
    # Try to get targets from summary.json grading
    for qid, q in questions.items():
        target = q.get("target", "")
        if target:
            targets[qid] = target
    
    # Fallback: If summary.json doesn't have targets, load from question files
    if not any(targets.values()) and memory_dir:
        capsule_id = capsule_result.get("capsule_id", "")
        if capsule_id:
            # Find all question files for this capsule
            q_files = list(memory_dir.glob(f"{capsule_id}-q*.json"))
            for qf in q_files:
                try:
                    with open(qf) as f:
                        q_data = json.load(f)
                    qid = q_data.get("question_id", qf.stem)
                    target = q_data.get("target") or q_data.get("ideal", "")
                    if target and qid in questions:
                        targets[qid] = target
                except Exception as e:
                    logger.warning(f"Failed to load target from {qf.name}: {e}")
    
    # Ensure all question IDs have a target (even if empty string)
    for qid in questions:
        if qid not in targets:
            targets[qid] = ""
    
    # CRITICAL VALIDATION: In supervised learning, ALL questions must have targets
    # If any target is missing/empty, this indicates a data integrity issue
    missing_targets = [qid for qid, target in targets.items() if not target]
    
    if missing_targets:
        capsule_id = capsule_result.get("capsule_id", "unknown")
        error_msg = (
            f"❌ SUPERVISED LEARNING ERROR: Missing ground truth targets for {capsule_id}\n"
            f"   Questions without targets: {missing_targets}\n"
            f"   Checked:\n"
            f"     1. summary.json grading.questions[qid].target\n"
        )
        if memory_dir:
            error_msg += f"     2. {capsule_id}-q*.json files in {memory_dir}\n"
        error_msg += (
            f"\n   💡 All questions MUST have ground truth in supervised mode.\n"
            f"      This likely indicates incomplete benchmark data or recovery issues."
        )
        raise ValueError(error_msg)
    
    return targets




def find_gt_notebook(groundtruth_dir: Path, capsule_id: str, memory_dir: Path = None) -> Optional[Path]:
    """
    Find GT notebook for a capsule.
    
    Args:
        groundtruth_dir: Path to groundtruth directory
        capsule_id: Capsule ID (e.g., 'bix-1')
        memory_dir: Optional directory containing question files for UUID lookup
        
    Returns:
        Path to GT notebook if exists, None otherwise
    """
    # Try direct match first (for capsules with simple naming)
    capsule_dir = groundtruth_dir / capsule_id
    if capsule_dir.exists():
        notebooks = list(capsule_dir.glob("**/*_executed.ipynb"))
        if notebooks:
            return notebooks[0]
    
    # Fallback: Find capsule_uuid from question files
    if memory_dir:
        q_files = list(memory_dir.glob(f"{capsule_id}-q*.json"))
        if q_files:
            try:
                with open(q_files[0]) as f:
                    q_data = json.load(f)
                capsule_uuid = q_data.get("capsule_uuid")
                
                if capsule_uuid:
                    # Try UUID-based directory
                    uuid_dir = groundtruth_dir / capsule_uuid
                    if uuid_dir.exists():
                        notebooks = list(uuid_dir.glob("**/*_executed.ipynb"))
                        if notebooks:
                            return notebooks[0]
            except Exception as e:
                logger.warning(f"Failed to extract capsule_uuid from {q_files[0].name}: {e}")
    
    return None



def extract_notebook_analysis(notebook_path: Path) -> str:
    """
    Extract analysis section from GT notebook, skipping template.
    
    Only extracts cell sources (no outputs) to avoid overfitting.
    
    Args:
        notebook_path: Path to executed notebook
        
    Returns:
        Formatted analysis content
    """
    import json
    
    with open(notebook_path, 'r') as f:
        nb = json.load(f)
    
    cells = nb.get("cells", [])
    
    # Find "# Analysis" marker
    analysis_start = 0
    for i, cell in enumerate(cells):
        source = _get_cell_source(cell)
        if "# Analysis" in source:
            analysis_start = i
            break
    
    # Extract cells from Analysis onwards (only source, no output)
    result_parts = []
    
    for cell in cells[analysis_start:]:
        source = _get_cell_source(cell)  # Only read source
        
        # Skip empty cells and template cells
        if not source.strip() or source.startswith("## Please"):
            continue
        
        # Format cell
        if cell["cell_type"] == "code":
            # Detect language (R uses %%R marker or library() calls)
            lang = "r" if source.startswith("%%R") or "library(" in source else "python"
            formatted = f"```{lang}\n{source}\n```"
        else:
            formatted = source
        
        result_parts.append(formatted)
    
    return "\n\n".join(result_parts)


def _get_cell_source(cell: dict) -> str:
    """Extract cell source code."""
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return source


def _format_grading(grading: dict) -> str:
    """
    Format per-question grading results.
    
    Args:
        grading: Grading dict with 'questions' field
        
    Returns:
        Formatted grading string
    """
    questions = grading.get("questions", {})
    lines = []
    
    for qid, q in questions.items():
        status = "✓" if q.get("correct") else "✗"
        if q.get("correct"):
            lines.append(f"- {qid}: {status}")
        else:
            target = q.get("target", "?")
            predicted = q.get("predicted", "?")
            lines.append(f"- {qid}: {status} (submitted: {predicted}, target: {target})")
    
    return "\n".join(lines)
