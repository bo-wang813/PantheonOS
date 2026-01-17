# Single Cell Benchmark

This benchmark evaluates agent performance on various single-cell analysis tasks, including data integration, cell type annotation, multimodal prediction, spatial deconvolution, and data cleaning/analysis.

## Usage

Run the benchmark using the `run_benchmark.py` script in pantheon-agents project root folder.

```bash
python benchmarks/single_cell_benchmark/run_benchmark.py [options]
```

### Arguments

- `--round <NAME>`: Name of the benchmark round. If not provided, a timestamped name (e.g., `round_20240101_120000`) is generated. use to **continue** a previous round.
- `--limit <INT>`: Limit the number of tasks to run (useful for testing).
- `--team <NAME>`: Team template to use (default: `default`).
- `--model <NAME>`: Model override (default: `gemini/gemini-3-flash-preview`).

### Examples

**Run all tasks:**
```bash
python benchmarks/single_cell_benchmark/run_benchmark.py
```

**Run first 5 tasks for testing:**
```bash
python benchmarks/single_cell_benchmark/run_benchmark.py --limit 5
```

**Run with a specific model:**
```bash
python benchmarks/single_cell_benchmark/run_benchmark.py --model "claude-3-5-sonnet"
```

## Structure

- `benchmark.jsonl`: Contains the dataset of tasks and ground truth.
- `benchmark_data/`: (Ignored in git) Contains the actual data files used by tasks.
- `results/`: (Ignored in git) specific benchmark round results.
  - `<round_name>/report.md`: Summary report.
  - `<round_name>/report.json`: JSON report.
  - `<round_name>/<task_id>.json`: Individual task results.
  - `<round_name>/<task_id>_memory.json`: Agent interaction logs.
- `workspaces/`: (Ignored in git) Agent working directories for each task.

## Utility Commands

### Regrade - Re-evaluate Results with LLM

Re-evaluate benchmark answers using LLM semantic verification for better accuracy assessment.

```bash
# Basic usage
python benchmarks/single_cell_benchmark/regrade.py --round round_gemini3_dynamic

# With custom model
python benchmarks/single_cell_benchmark/regrade.py --round round_gemini3_dynamic --model gemini/gemini-3-flash-preview
```

**Arguments:**
- `--round <NAME>`: Name of the benchmark round directory (required)
- `--model <NAME>`: LLM model for grading (default: `gemini/gemini-3-flash-preview`)

**Features:**
- Batch LLM grading for semantic equivalence
- Handles numerical tolerance and format variations (percentage/decimal conversions)
- Non-destructive: creates separate `regrade_report.json`

**Output:**
- `results/<round_name>/regrade_report.json` - Regrade results with accuracy and per-task grades

---

### Batch Learn - Build Skillbook from Results

Process memory files from a completed benchmark run to build a skillbook for offline learning.

```bash
# Basic usage (from bixbench directory)
python -m benchmarks.bixbench.batch_learn \
    --memory-dir benchmarks/single_cell_benchmark/results/round_gemini3_dynamic

# Custom output location
python -m benchmarks.bixbench.batch_learn \
    --memory-dir benchmarks/single_cell_benchmark/results/round_gemini3_dynamic \
    --output .pantheon/ace/skillbook_single_cell.json

# With quality filtering
python -m benchmarks.bixbench.batch_learn \
    --memory-dir benchmarks/single_cell_benchmark/results/round_gemini3_dynamic \
    --learning-model gemini/gemini-3-flash-preview \
    --config min_confidence_threshold=0.8 min_atomicity_score=0.95
```

**Arguments:**
- `--memory-dir <PATH>`: Directory containing memory JSON files (required)
- `--output <PATH>`: Output skillbook JSON file (default: `{memory_dir}/skillbook_batch.json`)
- `--mode <MODE>`: Learning mode - `pipeline` or `team` (default: `pipeline`)
- `--learning-model <NAME>`: Model for learning (default: from settings)
- `--config <KEY=VALUE>`: Additional config overrides

**Available Config Keys:**
- `max_tool_arg_length` - Max chars for tool arguments in compression
- `max_tool_output_length` - Max chars for tool output in compression
- `min_confidence_threshold` - Min confidence for reflection (0.0-1.0)
- `min_atomicity_score` - Min atomicity score for skills (0.0-1.0)
- `cleanup_after_learning` - Whether to cleanup learning files (true/false)

**Output:**
- Skillbook JSON file containing learned skills from the benchmark run

---

## Agent Interface

Agents must use the `submit_answer` tool to complete a task.

```python
def submit_answer(answer: str):
    """
    Submit the final answer for the task.
    Args:
        answer: The final answer. Use string representation for numbers/booleans (e.g., "1.23", "True", "Mast cells").
    """
```
