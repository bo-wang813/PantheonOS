#!/usr/bin/env python3
"""
Test script for supervised learning functionality.

Tests:
1. GT notebook finding
2. Notebook source extraction
3. Grading injection to memory
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.bixbench.supervised_learn import (
    find_gt_notebook,
    extract_notebook_analysis,
    append_grading_to_memory,
    load_groundtruth_from_result,
    _format_grading,
)


def test_find_gt_notebook():
    """Test GT notebook finding."""
    print("=" * 60)
    print("TEST 1: Find GT Notebook")
    print("=" * 60)
    
    groundtruth_dir = Path("benchmarks/bixbench/groundtruth")
    
    # Test with capsule that has notebook
    capsule_id = "0923d260-fe1b-4fb4-4398-79edf546e584"
    notebook_path = find_gt_notebook(groundtruth_dir, capsule_id)
    
    if notebook_path:
        print(f"✅ Found GT notebook for {capsule_id}")
        print(f"   Path: {notebook_path}")
        print(f"   Exists: {notebook_path.exists()}")
    else:
        print(f"❌ No GT notebook found for {capsule_id}")
        return False
    
    # Test with capsule that might not have notebook
    capsule_id_no_nb = "bix-1"
    notebook_path_no = find_gt_notebook(groundtruth_dir, capsule_id_no_nb)
    print(f"\n   Capsule without notebook ({capsule_id_no_nb}): {notebook_path_no}")
    
    return True


def test_extract_notebook_analysis():
    """Test notebook source extraction."""
    print("\n" + "=" * 60)
    print("TEST 2: Extract Notebook Analysis")
    print("=" * 60)
    
    groundtruth_dir = Path("benchmarks/bixbench/groundtruth")
    capsule_id = "0923d260-fe1b-4fb4-4398-79edf546e584"
    notebook_path = find_gt_notebook(groundtruth_dir, capsule_id)
    
    if not notebook_path:
        print("❌ No notebook to test")
        return False
    
    try:
        analysis = extract_notebook_analysis(notebook_path)
        
        print(f"✅ Extracted analysis from notebook")
        print(f"   Length: {len(analysis)} chars")
        print(f"   Preview (first 500 chars):")
        print("-" * 60)
        print(analysis[:500])
        print("-" * 60)
        
        # Check for expected content
        has_analysis = "# Analysis" in analysis or "Analysis" in analysis
        has_code_block = "```" in analysis
        has_no_output = "OUTPUT:" not in analysis.upper()
        
        print(f"\n   Contains 'Analysis': {has_analysis}")
        print(f"   Contains code blocks: {has_code_block}")
        print(f"   No outputs (good): {has_no_output}")
        
        return has_analysis and has_code_block and has_no_output
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_grading_injection():
    """Test grading injection to memory."""
    print("\n" + "=" * 60)
    print("TEST 3: Grading Injection to Memory")
    print("=" * 60)
    
    # Find a real memory file
    results_dir = Path("benchmarks/bixbench/results")
    memory_files = list(results_dir.glob("*/*_memory.json"))
    
    if not memory_files:
        print("❌ No memory files found for testing")
        return False
    
    memory_file = memory_files[0]
    print(f"   Using memory file: {memory_file}")
    
    # Create mock capsule result with grading
    capsule_result = {
        "capsule_id": "test-capsule",
        "answers": {
            "q1": "0.0015",
            "q2": "gene_x"
        },
        "grading": {
            "correct": 1,
            "total": 2,
            "accuracy": 0.5,
            "questions": {
                "q1": {
                    "correct": False,
                    "score": 0.0,
                    "target": "0.0002",
                    "predicted": "0.0015"
                },
                "q2": {
                    "correct": True,
                    "score": 1.0,
                    "target": "gene_x",
                    "predicted": "gene_x"
                }
            }
        }
    }
    
    try:
        # Test Level 1: grading only
        print("\n   Testing Level 1 (grading only)...")
        supervised_path = append_grading_to_memory(
            memory_path=memory_file,
            capsule_result=capsule_result,
            inject_notebook=False,
            gt_notebook_path=None,
        )
        
        print(f"   ✅ Created: {supervised_path}")
        
        # Check content
        with open(supervised_path) as f:
            data = json.load(f)
        
        messages = data.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if last_message and last_message.get("role") == "system":
            content = last_message.get("content", "")
            print(f"   ✅ System message added")
            print(f"   Length: {len(content)} chars")
            
            # Check for expected sections
            has_grading = "## Grading Result" in content
            has_submitted = "Agent's Submitted Answers" in content
            has_ground_truth = "Ground Truth Answers" in content
            has_accuracy = "Overall Accuracy" in content
            
            print(f"   Has grading section: {has_grading}")
            print(f"   Has submitted answers: {has_submitted}")
            print(f"   Has ground truth: {has_ground_truth}")
            print(f"   Has accuracy: {has_accuracy}")
            
            print(f"\n   Preview:")
            print("-" * 60)
            print(content[:600])
            print("-" * 60)
            
            # Clean up
            supervised_path.unlink()
            print(f"\n   ✅ Cleaned up test file")
            
            return has_grading and has_submitted and has_ground_truth
        else:
            print(f"   ❌ No system message found")
            return False
            
    except Exception as e:
        print(f"❌ Injection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_level2_injection():
    """Test Level 2 (with notebook) injection."""
    print("\n" + "=" * 60)
    print("TEST 4: Level 2 Injection (with notebook)")
    print("=" * 60)
    
    # Find a memory file and GT notebook
    results_dir = Path("benchmarks/bixbench/results")
    memory_files = list(results_dir.glob("*/*_memory.json"))
    
    if not memory_files:
        print("❌ No memory files found")
        return False
    
    groundtruth_dir = Path("benchmarks/bixbench/groundtruth")
    capsule_id = "0923d260-fe1b-4fb4-4398-79edf546e584"
    gt_notebook = find_gt_notebook(groundtruth_dir, capsule_id)
    
    if not gt_notebook:
        print("❌ No GT notebook found")
        return False
    
    memory_file = memory_files[0]
    
    capsule_result = {
        "capsule_id": capsule_id,
        "answers": {"q1": "wrong_answer"},
        "grading": {
            "correct": 0,
            "total": 1,
            "accuracy": 0.0,
            "questions": {
                "q1": {
                    "correct": False,
                    "score": 0.0,
                    "target": "correct_answer",
                    "predicted": "wrong_answer"
                }
            }
        }
    }
    
    try:
        print(f"   Using memory: {memory_file.name}")
        print(f"   Using notebook: {gt_notebook.name}")
        
        supervised_path = append_grading_to_memory(
            memory_path=memory_file,
            capsule_result=capsule_result,
            inject_notebook=True,
            gt_notebook_path=gt_notebook,
        )
        
        print(f"   ✅ Created: {supervised_path}")
        
        # Check content
        with open(supervised_path) as f:
            data = json.load(f)
        
        messages = data.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if last_message and last_message.get("role") == "system":
            content = last_message.get("content", "")
            print(f"   ✅ System message added")
            print(f"   Length: {len(content)} chars")
            
            has_grading = "## Grading Result" in content
            has_reference = "## Reference Solution" in content
            has_code = "```" in content
            
            print(f"   Has grading: {has_grading}")
            print(f"   Has reference solution: {has_reference}")
            print(f"   Has code blocks: {has_code}")
            
            print(f"\n   Preview (last 800 chars):")
            print("-" * 60)
            print(content[-800:])
            print("-" * 60)
            
            # Clean up
            supervised_path.unlink()
            print(f"\n   ✅ Cleaned up test file")
            
            return has_grading and has_reference and has_code
        else:
            print(f"   ❌ No system message found")
            return False
            
    except Exception as e:
        print(f"❌ Level 2 injection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Supervised Learning Implementation")
    print("=" * 60)
    
    results = {
        "Find GT Notebook": test_find_gt_notebook(),
        "Extract Notebook Analysis": test_extract_notebook_analysis(),
        "Level 1 Grading Injection": test_grading_injection(),
        "Level 2 Notebook Injection": test_level2_injection(),
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
