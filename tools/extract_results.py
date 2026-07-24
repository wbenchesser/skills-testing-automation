#!/usr/bin/env python3
"""
Extract and analyze sqli-detector evaluation results.
Simple direct parser for the benchmark evaluation.
"""

import json
import re
import yaml
from pathlib import Path

# CONFIG
import sys
if len(sys.argv) > 1:
    skill_name = sys.argv[1]
else:
    skill_name = "sqli-detector"

RESULTS_DIR = f"eval/runs/{skill_name}-eval/2026-07-24-sonnet/cases"
DATASET_DIR = "eval/_dataset/cases"

def extract_conversation(stdout_log_path):
    """Extract final assistant response from stdout.log JSONL."""
    conversation = None

    with open(stdout_log_path) as f:
        for line in f:
            try:
                event = json.loads(line)
                # Look for result events with conversation text
                if event.get("type") == "result" and "result" in event:
                    conversation = event["result"]
            except json.JSONDecodeError:
                continue

    return conversation

def parse_verdict(conversation):
    """Parse verdict block from conversation."""
    if not conversation:
        return None

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

def main():
    results_path = Path(RESULTS_DIR)
    dataset_path = Path(DATASET_DIR)

    cases = sorted([d for d in results_path.iterdir() if d.is_dir()])

    print(f"\n{'='*80}")
    print(f"SQL INJECTION DETECTOR - EVALUATION RESULTS")
    print(f"{'='*80}\n")
    print(f"Total cases: {len(cases)}\n")

    # Stats
    stats = {
        "TP": 0, "TN": 0, "FP": 0, "FN": 0,
        "correct": 0, "total": 0,
        "format_ok": 0, "no_verdict": 0
    }

    results = []

    for case_dir in cases:
        case_id = case_dir.name

        # Load ground truth
        ref_path = dataset_path / case_id / "reference.yaml"
        with open(ref_path) as f:
            reference = yaml.safe_load(f)

        # Extract conversation
        stdout_path = case_dir / "stdout.log"
        conversation = extract_conversation(stdout_path)

        # Parse verdict
        verdict = parse_verdict(conversation)

        if verdict and verdict["vulnerable"] is not None:
            pred = verdict["vulnerable"]
            gold = reference["real_vulnerability"]

            # Confusion matrix
            if pred and gold:
                cell = "TP"
                stats["TP"] += 1
            elif pred and not gold:
                cell = "FP"
                stats["FP"] += 1
            elif not pred and gold:
                cell = "FN"
                stats["FN"] += 1
            else:
                cell = "TN"
                stats["TN"] += 1

            correct = pred == gold
            if correct:
                stats["correct"] += 1
            stats["format_ok"] += 1

            results.append({
                "case_id": case_id,
                "predicted": pred,
                "actual": gold,
                "cell": cell,
                "correct": correct,
                "reasoning": verdict["reasoning"][:100] + "..." if verdict["reasoning"] else None
            })

            print(f"{case_id}: {cell} ({'✓' if correct else '✗'})")
            print(f"  Predicted: {pred}, Actual: {gold}, CWE: {reference.get('cwe', 'null')}")
            if not correct:
                print(f"  Reasoning: {verdict['reasoning'][:150]}...")
            print()
        else:
            stats["no_verdict"] += 1
            print(f"{case_id}: NO VERDICT ✗")
            print()

        stats["total"] += 1

    # Compute metrics
    precision = stats["TP"] / (stats["TP"] + stats["FP"]) if (stats["TP"] + stats["FP"]) > 0 else 0.0
    recall = stats["TP"] / (stats["TP"] + stats["FN"]) if (stats["TP"] + stats["FN"]) > 0 else 0.0
    accuracy = stats["correct"] / stats["total"]
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Report
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Cases processed: {stats['total']}")
    print(f"Valid verdicts: {stats['format_ok']}/{stats['total']}")
    print(f"No verdict: {stats['no_verdict']}")
    print()
    print(f"Accuracy: {accuracy:.1%} ({stats['correct']}/{stats['total']})")
    print(f"Precision: {precision:.1%} (TP={stats['TP']}, FP={stats['FP']})")
    print(f"Recall: {recall:.1%} (TP={stats['TP']}, FN={stats['FN']})")
    print(f"F1 Score: {f1:.1%}")
    print()
    print(f"Confusion Matrix:")
    print(f"  True Positives (TP):  {stats['TP']}")
    print(f"  True Negatives (TN):  {stats['TN']}")
    print(f"  False Positives (FP): {stats['FP']}")
    print(f"  False Negatives (FN): {stats['FN']}")
    print(f"{'='*80}\n")

    # Worst cases
    if any(not r["correct"] for r in results):
        print("INCORRECT CLASSIFICATIONS:")
        for r in results:
            if not r["correct"]:
                print(f"  {r['case_id']}: {r['cell']} (predicted={r['predicted']}, actual={r['actual']})")
        print()

if __name__ == "__main__":
    main()
