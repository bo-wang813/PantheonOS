"""
Batch learning script for Single Cell Benchmark.

Simplified version of BixBench batch_learn.py for tasks with single answers.

Usage:
    # Unsupervised
    python -m benchmarks.single_cell_benchmark.batch_learn --memory-dir results/round_xxx
    
    # Supervised (Level 1 only - no notebooks available)
    python -m benchmarks.single_cell_benchmark.batch_learn \
        --memory-dir results/round_xxx \
        --supervised
"""
import argparse
import asyncio
import json
from pathlib import Path
from typing import List, Optional

from pantheon.utils.log import setup_file_logging, logger


async def batch_learn(
    memory_dir: str,
    output_skillbook: str | None = None,
    learning_model: str | None = None,
    log_level: str = "INFO",
    cooldown_seconds: int = 10,
    supervised: bool = False,
    **config_overrides,
):
    """
    Batch learn from all memory files in a directory.
    
    Args:
        memory_dir: Directory containing memory JSON files and report.json
        output_skillbook: Path to output skillbook
        learning_model: Model for learning
        log_level: Log level
        cooldown_seconds: Cooldown between tasks
        supervised: Enable supervised learning (with ground truth)
        **config_overrides: Additional config overrides
    """
    from pantheon.internal.learning.skillbook import Skillbook
    from pantheon.internal.learning.reflector import Reflector
    from pantheon.internal.learning.skill_manager import SkillManager
    from pantheon.internal.learning.pipeline import LearningPipeline, LearningInput
    from pantheon.settings import get_settings
    
    # Setup logging
    log_file = setup_file_logging(
        log_dir=Path(".pantheon/logs/benchmark"),
        level=log_level,
        session_name="batch_learning_sc",
    )
    print(f"📝 Logs: {log_file}")
    
    memory_path = Path(memory_dir)
    if not memory_path.exists():
        print(f"❌ Memory directory not found: {memory_dir}")
        return
    
    # Auto-organize outputs based on supervised flag
    if supervised:
        learning_subdir = "learning/supervised"
        level_name = "supervised"
        print(f"📁 Supervised learning: outputs → {memory_dir}/learning/supervised/")
    else:
        learning_subdir = "learning/unsupervised"
        level_name = "unsupervised"
        print(f"📁 Unsupervised learning: outputs → {memory_dir}/learning/unsupervised/")
    
    learning_dir = memory_path / learning_subdir
    learning_dir.mkdir(parents=True, exist_ok=True)
    
    # Auto-set skillbook path if not specified
    if output_skillbook is None:
        output_skillbook = str(learning_dir / f"skillbook_{level_name}.json")
    
    # Find memory files
    memory_files = list(memory_path.glob("**/*_memory.json"))
    if not memory_files:
        print(f"❌ No memory files found in: {memory_dir}")
        return
    
    print(f"📂 Found {len(memory_files)} memory files")
    print(f"🔧 Learning mode: {'Supervised (Level 1)' if supervised else 'Unsupervised (Level 0)'}")
    
    # Supervised learning setup
    results_data = None
    if supervised:
        # Load report.json for ground truth - search in priority order
        report_file = None
        for pattern in ["regrade_report.json", "report.json", "*_regrade.json"]:
            matches = list(memory_path.glob(pattern))
            if matches:
                report_file = matches[0]
                break
        
        if report_file:
            print(f"📊 Loading results from: {report_file.name}")
            with open(report_file) as f:
                report_data = json.load(f)
                results_data = {r["id"]: r for r in report_data.get("results", [])}
        else:
            # CRITICAL: User requested supervised but no grading data found
            print(f"\n❌ ERROR: Supervised learning requested but no grading data found!")
            print(f"   Expected files in {memory_path}:")
            print(f"   - regrade_report.json (preferred)")
            print(f"   - report.json (standard)")
            print(f"   - *_regrade.json (legacy)")
            print(f"\n   Found files:")
            for f in sorted(memory_path.glob("*.json"))[:10]:
                print(f"   - {f.name}")
            print(f"\n💡 Solutions:")
            print(f"   1. Ensure the results directory contains grading data")
            print(f"   2. Run without --supervised for unsupervised learning")
            print(f"   3. Run benchmark first to generate report.json")
            raise FileNotFoundError(
                f"No grading data found in {memory_path} for supervised learning. "
                f"Cannot proceed with --supervised flag."
            )
    
    # Initialize skillbook
    output_path = Path(output_skillbook)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    skillbook = Skillbook(skillbook_path=str(output_path))
    
    # Build learning config
    settings = get_settings()
    learning_config = settings.get_learning_config().copy()
    
    if learning_model is not None:
        learning_config["learning_model"] = learning_model
    
    # Set trajectory output directory to learning subdirectory
    learning_config["trajectory_output_dir"] = str(learning_dir)
    
    learning_config.update(config_overrides)
    
    # Initialize learning components
    reflector = Reflector(
        model=learning_config.get("learning_model", "gemini/gemini-3-flash-preview"),
        learning_config=learning_config,
    )
    skill_manager = SkillManager(
        model=learning_config.get("learning_model", "gemini/gemini-3-flash-preview"),
        learning_config=learning_config,
    )
    
    # Create pipeline
    batch_learning_dir = str(learning_dir / ".batch_learning")
    pipeline = LearningPipeline(
        skillbook=skillbook,
        reflector=reflector,
        skill_manager=skill_manager,
        learning_dir=batch_learning_dir,
        cleanup_after_learning=learning_config.get("cleanup_after_learning", False),
        min_confidence_threshold=learning_config.get("min_confidence_threshold", 0.5),
        min_atomicity_score=learning_config.get("min_atomicity_score", 0.85),
        mode="pipeline",  # Single cell uses pipeline mode only
    )
    
    await pipeline.start()
    
    print(f"\n🎓 Starting batch learning...")
    print(f"📝 Output skillbook: {output_path}")
    
    # Process each memory file
    processed = 0
    errors = 0
    
    for i, memory_file in enumerate(memory_files, 1):
        try:
            print(f"\n[{i}/{len(memory_files)}] 📄 Processing: {memory_file.name}")
            
            # Extract task ID from filename (format: {task_id}_memory.json)
            task_id = memory_file.stem.replace("_memory", "")
            
            # Supervised learning: augment memory with grading
            actual_memory_file = memory_file
            if supervised and results_data:
                try:
                    from benchmarks.common.supervised_learn import append_grading_to_memory_simple
                    
                    task_result = results_data.get(task_id)
                    if task_result:
                        actual_memory_file = append_grading_to_memory_simple(
                            memory_path=memory_file,
                            task_result=task_result,
                        )
                        print(f"  ✓ Augmented memory with grading")
                    else:
                        print(f"  ⚠️  No result found for {task_id}")
                except Exception as e:
                    print(f"  ⚠️  Failed to augment memory: {e}")
                    logger.exception(f"Supervised learning error for {task_id}")
            
            # Create learning input
            learning_input = LearningInput(
                turn_id=actual_memory_file.stem,
                agent_name="global",
                details_path=str(actual_memory_file),
                chat_id=task_id,
            )
            
            # Submit to pipeline
            pipeline.submit(learning_input)
            print(f"  ✓ Submitted for learning")
            
            # Wait for queue to drain
            wait_count = 0
            max_wait = 60
            while not pipeline._queue.empty() and wait_count < max_wait:
                await asyncio.sleep(0.5)
                wait_count += 1
            
            if pipeline._queue.empty():
                print(f"  ✅ Learning complete")
                processed += 1
                await asyncio.sleep(cooldown_seconds)
            else:
                print(f"  ⚠️ Timeout waiting for queue")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            logger.exception(f"Error processing {memory_file}")
            errors += 1
    
    # Final wait to ensure all processing is complete
    print(f"\n⏳ Final check - ensuring all tasks are complete...")
    print(f"   Queue size: {pipeline._queue.qsize()}")
    
    # Wait until queue is truly empty (no time limit, but report progress)
    wait_count = 0
    last_size = pipeline._queue.qsize()
    
    while not pipeline._queue.empty():
        await asyncio.sleep(5)
        wait_count += 5
        current_size = pipeline._queue.qsize()
        
        # Report progress every 30s or when queue size changes
        if wait_count % 30 == 0 or current_size != last_size:
            print(f"   Queue size: {current_size}, waited {wait_count}s")
            last_size = current_size
    
    print(f"   ✓ All tasks processed (waited {wait_count}s total)")
    
    
    # Stop pipeline
    await pipeline.stop()
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"✅ Batch learning complete!")
    print(f"   Processed: {processed}/{len(memory_files)}")
    print(f"   Errors: {errors}")
    print(f"   Skillbook: {output_path}")
    
    # Print skillbook stats
    summary = skillbook.stats()
    print(f"\n📊 Skillbook Summary:")
    print(f"   Total skills: {summary.get('total_skills', 0)}")
    print(f"   Active skills: {summary.get('active_skills', 0)}")
    
    return {
        "processed": processed,
        "errors": errors,
        "skillbook_path": str(output_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Batch learn from Single Cell Benchmark memory files"
    )
    
    parser.add_argument(
        "--memory-dir",
        required=True,
        help="Directory containing memory JSON files and report.json",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output skillbook JSON file path",
    )
    parser.add_argument(
        "--learning-model",
        type=str,
        default=None,
        help="Model for learning",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
        help="Log level",
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=10,
        help="Seconds to wait between learning tasks",
    )
    parser.add_argument(
        "--supervised",
        action="store_true",
        help="Enable supervised learning (with ground truth from report.json)",
    )
    parser.add_argument(
        "--config",
        nargs="*",
        metavar="KEY=VALUE",
        help="Additional learning config overrides",
    )
    
    args = parser.parse_args()
    
    # Parse config overrides
    config_overrides = {}
    if args.config:
        for item in args.config:
            if "=" not in item:
                print(f"⚠️  Warning: Ignoring invalid config format '{item}'")
                continue
            key, value = item.split("=", 1)
            try:
                if value.lower() in ("true", "false"):
                    config_overrides[key] = value.lower() == "true"
                elif value.isdigit():
                    config_overrides[key] = int(value)
                elif value.replace(".", "", 1).isdigit():
                    config_overrides[key] = float(value)
                else:
                    config_overrides[key] = value
            except:
                config_overrides[key] = value
    
    asyncio.run(batch_learn(
        memory_dir=args.memory_dir,
        output_skillbook=args.output,
        learning_model=args.learning_model,
        log_level=args.log_level,
        cooldown_seconds=args.cooldown,
        supervised=args.supervised,
        **config_overrides,
    ))


if __name__ == "__main__":
    main()
