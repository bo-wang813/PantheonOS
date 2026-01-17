import logging
from pathlib import Path
import sys
import re
import asyncio
import json
import argparse

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from pantheon.agent import Agent
from pantheon.utils.log import temporary_log_level

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("regrade")

async def regrade_run(run_dir_name: str, model: str = "gemini/gemini-3-flash-preview"):
    base_dir = Path(__file__).parent.resolve()
    results_dir = base_dir / "results" / run_dir_name

    if not results_dir.exists():
        # Try finding it just by name in case full path wasn't given
        possible_dir = base_dir / "results" / run_dir_name
        if possible_dir.exists():
            results_dir = possible_dir
        else:
             logger.error(f"Run directory not found: {results_dir}")
             return

    report_path = results_dir / "report.json"
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        return

    logger.info(f"Loading report from: {report_path}")
    with open(report_path, 'r') as f:
        report = json.load(f)

    results = report.get('results', [])
    if not results:
        logger.warning("No results found in report.")
        return

    logger.info(f"Found {len(results)} tasks to regrade.")

    # Build prompt
    grading_prompt = """You are a precise grader for a bioinformatics benchmark. Your task is to compare predicted answers with target answers and determine if they are semantically equivalent.

## GRADING RULES:

### For NUMERICAL answers:
1. **Percentage vs Decimal**: 35% equals 0.35 equals 35.0
   - Example: Predicted "35.3414" vs Target "35%" → CORRECT (35.3414 ≈ 35)
   - Example: Predicted "0.35" vs Target "35%" → CORRECT (0.35 = 35%)
   - Example: Predicted "0.3534" vs Target "35%" → CORRECT (0.3534 = 35.34%)
   - Example: Predicted "35.0" vs Target "0.35" → CORRECT (35% = 0.35)

2. **Decimal Precision**: Ignore trailing zeros and minor precision differences
   - Example: Predicted "1.670" vs Target "1.67" → CORRECT
   - Example: Predicted "4.0017" vs Target "4.0" → CORRECT (0.04% difference)

3. **Scientific Notation**: Different formats of same value are equivalent
   - Example: Predicted "0.000019" vs Target "1.9E-5" → CORRECT
   - Example: Predicted "2E-04" vs Target "0.0002" → CORRECT

4. **Tolerance / Range**: 
   - If a 'Tolerance' or specific range is provided for a question, YOU MUST USE IT.
   - If acceptable range is (1.5, 1.6) and predicted is 1.55 → CORRECT.
   - If tolerance is +/- 5% and predicted is within that margin of target → CORRECT.
   - If NO specific tolerance is given, default to ~5% relative error.

### For TEXT/STRING answers:
- Must match exactly (case-insensitive, ignoring whitespace)
- Example: Predicted "1-50, >100" vs Target "1-50" → INCORRECT (extra content)

### For EMPTY answers:
- Predicted "" or "NO ANSWER" → INCORRECT

## EXAMPLES:
✓ CORRECT: Predicted="35.3414", Target="35%" (35.3414 ≈ 35)
✓ CORRECT: Predicted="4.0017", Target="4.0" (0.04% error)
✓ CORRECT: Predicted="0.0501", Target="0.05" (2% error)
✓ CORRECT: Predicted="1500", Target="1450", Tolerance="+/- 50" (1500 is within 1450 +/- 50)
✗ INCORRECT: Predicted="0.0045", Target="(0.43,0.45)" (0.0045 not in range, likely scale mismatch)
✗ INCORRECT: Predicted="1-50, >100", Target="1-50" (extra content)

Questions to grade:
"""

    tasks_to_grade = []
    
    for i, res in enumerate(results, 1):
        task_id = res.get('id')
        question = res.get('task')
        target = res.get('ground_truth')
        predicted = res.get('agent_answer')
        tolerance = res.get('tolerance', 'None provided')
        
        # Only grade completed tasks or those with answers
        if not predicted and res.get('status') != 'completed':
             continue

        tasks_to_grade.append(res)
        
        grading_prompt += f"""
---
[{i}] Question ID: {task_id}
Question: {question}
Target Answer: {target}
Tolerance/Range: {tolerance}
Predicted Answer: {predicted}
"""

    grading_prompt += """

IMPORTANT: Output ONLY a valid JSON object mapping question_id to grade.
Use "correct" or "incorrect" as values.
Example: {"task_1": "correct", "task_2": "incorrect"}

Output:"""

    logger.info(f"Using model: {model} for grading...")

    # Create grading agent
    grading_agent = Agent(
        name="SingleCellGrader",
        model=model,
        instructions="You are a precise answer grader. Compare predicted and target answers for semantic equivalence, respecting provided tolerances.",
    )

    # Run agent
    try:
        with temporary_log_level("WARNING"):
            response = await grading_agent.run(grading_prompt)
            
        response_text = response.content if hasattr(response, "content") else str(response)
        response_text = response_text.strip()
        
        # Extract JSON
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            grades = json.loads(json_match.group())
        else:
            grades = json.loads(response_text)
            
    except Exception as e:
        logger.error(f"Grading failed: {e}")
        return

    # Process results
    total_correct = 0
    total_graded = 0
    
    # Create regrade report
    regrade_results = []
    
    for res in results:
        task_id = res.get('id')
        
        # Default to original status if not graded (e.g. failed task)
        is_original_correct = False # We verify this if needed, but here we just want new grades
        # Actually standard report doesn't have 'correct' boolean, we are verifying now.
        
        llm_grade = grades.get(task_id, "incorrect").lower()
        is_correct = llm_grade == "correct"
        
        if task_id in grades:
             total_graded += 1
             if is_correct:
                 total_correct += 1
        
        regrade_entry = {
            "id": task_id,
            "task": res.get('task'),
            "ground_truth": res.get('ground_truth'),
            "agent_answer": res.get('agent_answer'),
            "tolerance": res.get('tolerance'),
            "grade": llm_grade
        }
        regrade_results.append(regrade_entry)

    acc = total_correct / total_graded if total_graded > 0 else 0
    
    logger.info(f"="*50)
    logger.info(f"REGRADE RESULTS")
    logger.info(f"="*50)
    logger.info(f"Total Tasks: {len(results)}")
    logger.info(f"Graded Tasks: {total_graded}")
    logger.info(f"Correct: {total_correct}")
    logger.info(f"Accuracy: {acc:.1%}")
    logger.info(f"="*50)

    # Save regrade report
    regrade_file = results_dir / "regrade_report.json"
    output_data = {
        "original_report": str(report_path),
        "grading_model": model,
        "total_tasks": len(results),
        "graded_count": total_graded,
        "correct_count": total_correct,
        "accuracy": acc,
        "results": regrade_results
    }
    
    with open(regrade_file, 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Saved regrade report to: {regrade_file}")


async def main():
    parser = argparse.ArgumentParser(description="Single Cell Benchmark Regrader")
    parser.add_argument("--round", required=True, help="Name of the benchmark round directory (e.g., round_20260113_XX)")
    parser.add_argument("--model", default="gemini/gemini-3-flash-preview", help="Model to use for grading")
    
    args = parser.parse_args()
    
    await regrade_run(args.round, args.model)

if __name__ == "__main__":
    asyncio.run(main())
