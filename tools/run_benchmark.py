#!/usr/bin/env python3
"""
Execute skill against OWASP benchmark cases and score results.
Simpler than full eval-run harness - directly invokes model with skill instructions.
"""

import json
import re
import subprocess
import yaml
from pathlib import Path
from collections import defaultdict

# CONFIG
SKILLS = {
    "sqli-detector": "skills/sqli-detector/SKILL.md",
    "input-validation-injection": "skills/input-validation-injection/SKILL.md"
}
DATASET_DIR = "eval/_dataset/cases"
MODEL = "claude-sonnet-4@20250514"
OUTPUT_BASE = "eval/runs"

def load_skill_instructions(skill_md_path):
    """Read SKILL.md and extract instructions."""
    with open(skill_md_path) as f:
        content = f.read()

    # Strip frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    return content

def load_test_case(case_dir):
    """Load input.yaml and reference.yaml from a test case."""
    input_path = case_dir / "input.yaml"
    ref_path = case_dir / "reference.yaml"

    with open(input_path) as f:
        input_data = yaml.safe_load(f)

    with open(ref_path) as f:
        reference = yaml.safe_load(f)

    return input_data, reference

def invoke_model(skill_instructions, test_input):
    """
    Invoke Claude with skill instructions + test case.
    Uses echo + claude-code CLI for simplicity.
    """
    # Combine skill instructions + test input
    prompt = f"""{skill_instructions}

---

{test_input['prompt']}

```java
{test_input['code']}
```
"""

    # Write to temp file
    prompt_file = Path("/tmp/benchmark_prompt.txt")
    prompt_file.write_text(prompt)

    # Invoke Claude Code CLI (simplified - would need actual API call in production)
    # For now, return mock response for testing
    # TODO: Replace with actual model invocation

    return {
        "conversation": "Mock response - replace with actual model call",
        "cost_usd": 0.0,
        "duration_s": 1.0
    }

def extract_verdict(conversation):
    """Parse verdict block from conversation."""
    verdict_match = re.search(r'```verdict\s*\n(.*?)\n```', conversation, re.DOTALL | re.IGNORECASE)
    if not verdict_match:
        return None

    verdict_text = verdict_match.group(1)

    vuln_match = re.search(r'vulnerable:\s*(true|false)', verdict_text, re.IGNORECASE)
    cwe_match = re.search(r'cwe:\s*(\d+|none|null)', verdict_text, re.IGNORECASE)
    reasoning_match = re.search(r'reasoning:\s*(.+)', verdict_text, re.IGNORECASE | re.DOTALL)

    return {
        "vulnerable": vuln_match.group(1).lower() == "true" if vuln_match else None,
        "cwe": cwe_match.group(1) if cwe_match else None,
        "reasoning": reasoning_match.group(1).strip() if reasoning_match else None
    }

def judge_verdict_correct(predicted, reference):
    """Judge: Classification correctness."""
    if predicted is None:
        return False, "No verdict found"

    pred = predicted["vulnerable"]
    gold = reference["real_vulnerability"]

    if pred and gold:
        cell = "TP"
    elif pred and not gold:
        cell = "FP"
    elif not pred and gold:
        cell = "FN"
    else:
        cell = "TN"

    ok = pred == gold
    return ok, f"{cell} (pred={pred}, gold={gold}, cwe={reference.get('cwe', 'null')})"

def run_skill_evaluation(skill_name):
    """Run evaluation for one skill."""
    print(f"\n{'='*60}")
    print(f"EVALUATING: {skill_name}")
    print(f"{'='*60}\n")

    # Load skill
    skill_path = SKILLS[skill_name]
    skill_instructions = load_skill_instructions(skill_path)

    # Load dataset
    dataset_path = Path(DATASET_DIR)
    cases = sorted([d for d in dataset_path.iterdir() if d.is_dir()])

    print(f"Dataset: {len(cases)} cases")
    print(f"Model: {MODEL}\n")

    # Results
    results = []
    stats = {
        "TP": 0, "TN": 0, "FP": 0, "FN": 0,
        "correct": 0, "total": 0,
        "total_cost": 0.0, "total_duration": 0.0
    }

    # Run each case
    for case_dir in cases:
        case_id = case_dir.name
        print(f"Running {case_id}...")

        # Load case
        test_input, reference = load_test_case(case_dir)

        # Invoke model
        response = invoke_model(skill_instructions, test_input)

        # Parse verdict
        verdict = extract_verdict(response["conversation"])

        # Judge
        correct, rationale = judge_verdict_correct(verdict, reference)

        # Track stats
        cell = rationale.split()[0]  # TP/TN/FP/FN
        if cell in stats:
            stats[cell] += 1
        if correct:
            stats["correct"] += 1
        stats["total"] += 1
        stats["total_cost"] += response["cost_usd"]
        stats["total_duration"] += response["duration_s"]

        # Store result
        results.append({
            "case_id": case_id,
            "verdict": verdict,
            "reference": reference,
            "correct": correct,
            "rationale": rationale,
            "cost_usd": response["cost_usd"]
        })

        print(f"  {case_id}: {rationale}")

    # Compute metrics
    precision = stats["TP"] / (stats["TP"] + stats["FP"]) if (stats["TP"] + stats["FP"]) > 0 else 0.0
    recall = stats["TP"] / (stats["TP"] + stats["FN"]) if (stats["TP"] + stats["FN"]) > 0 else 0.0
    accuracy = stats["correct"] / stats["total"]

    # Report
    print(f"\n{'='*60}")
    print(f"RESULTS: {skill_name}")
    print(f"{'='*60}")
    print(f"Accuracy: {accuracy:.1%} ({stats['correct']}/{stats['total']})")
    print(f"Precision: {precision:.1%} (TP={stats['TP']}, FP={stats['FP']})")
    print(f"Recall: {recall:.1%} (TP={stats['TP']}, FN={stats['FN']})")
    print(f"Confusion Matrix: TP={stats['TP']}, TN={stats['TN']}, FP={stats['FP']}, FN={stats['FN']}")
    print(f"Cost: ${stats['total_cost']:.2f}")
    print(f"Duration: {stats['total_duration']:.1f}s")
    print(f"{'='*60}\n")

    return {
        "skill": skill_name,
        "cases": len(cases),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": {k: stats[k] for k in ["TP", "TN", "FP", "FN"]},
        "cost_usd": stats["total_cost"],
        "duration_s": stats["total_duration"],
        "results": results
    }

def main():
    all_results = {}

    for skill_name in SKILLS:
        result = run_skill_evaluation(skill_name)
        all_results[skill_name] = result

    # Write summary
    output_dir = Path(OUTPUT_BASE)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "benchmark_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nResults saved to {output_dir / 'benchmark_results.json'}")

if __name__ == "__main__":
    main()
