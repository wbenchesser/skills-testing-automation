#!/usr/bin/env python3
"""Manual scoring for sqli-detector evaluation."""
import re
import yaml
from pathlib import Path
from collections import defaultdict

def score_verdict_format(conversation):
    """Check if verdict block is properly formatted."""
    verdict_match = re.search(r'```verdict\s*\n(.*?)\n```', conversation, re.DOTALL | re.IGNORECASE)
    if not verdict_match:
        return False, "No verdict block found"

    verdict_text = verdict_match.group(1)
    has_vulnerable = re.search(r'vulnerable:\s*(true|false)', verdict_text, re.IGNORECASE)
    has_cwe = re.search(r'cwe:\s*(\d+|none|null)', verdict_text, re.IGNORECASE)
    has_reasoning = re.search(r'reasoning:\s*(.+)', verdict_text, re.IGNORECASE | re.DOTALL)

    if not has_vulnerable:
        return False, "Missing 'vulnerable' field"
    if not has_cwe:
        return False, "Missing 'cwe' field"
    if not has_reasoning:
        return False, "Missing 'reasoning' field"
    return True, "Verdict block properly formatted"

def score_verdict_correct(conversation, reference):
    """Compare verdict against ground truth."""
    verdict_match = re.search(r'```verdict\s*\n(.*?)\n```', conversation, re.DOTALL | re.IGNORECASE)
    if not verdict_match:
        return False, "No parseable verdict"

    verdict_text = verdict_match.group(1)
    vuln_match = re.search(r'vulnerable:\s*(true|false)', verdict_text, re.IGNORECASE)
    if not vuln_match:
        return False, "No vulnerable field found"

    pred = vuln_match.group(1).lower() == "true"
    gold = bool(reference.get("real_vulnerability", False))

    if pred and gold:
        cell = "TP"
    elif pred and not gold:
        cell = "FP"
    elif not pred and gold:
        cell = "FN"
    else:
        cell = "TN"

    ok = pred == gold
    cwe = reference.get("cwe", "null")
    return ok, f"{cell} (pred={pred}, gold={gold}, cwe={cwe})"

def main():
    cases_dir = Path("eval/runs/sqli-detector-benchmark/2026-07-24-sonnet/cases")
    dataset_dir = Path("eval/_dataset/cases")

    results = {
        "verdict_format": [],
        "verdict_correct": []
    }

    confusion = {"TP": 0, "TN": 0, "FP": 0, "FN": 0}

    for case_dir in sorted(cases_dir.iterdir()):
        if not case_dir.is_dir():
            continue

        case_name = case_dir.name

        # Load conversation
        conv_file = case_dir / "conversation.txt"
        if not conv_file.exists():
            print(f"SKIP {case_name}: no conversation.txt")
            continue
        conversation = conv_file.read_text()

        # Load reference
        ref_file = dataset_dir / case_name / "reference.yaml"
        if not ref_file.exists():
            print(f"SKIP {case_name}: no reference.yaml")
            continue
        with open(ref_file) as f:
            reference = yaml.safe_load(f)

        # Score format
        format_ok, format_msg = score_verdict_format(conversation)
        results["verdict_format"].append(format_ok)

        # Score correctness
        correct_ok, correct_msg = score_verdict_correct(conversation, reference)
        results["verdict_correct"].append(correct_ok)

        # Update confusion matrix
        if "TP" in correct_msg:
            confusion["TP"] += 1
        elif "TN" in correct_msg:
            confusion["TN"] += 1
        elif "FP" in correct_msg:
            confusion["FP"] += 1
        elif "FN" in correct_msg:
            confusion["FN"] += 1

        status = "✓" if (format_ok and correct_ok) else "✗"
        print(f"{status} {case_name}: format={format_ok}, {correct_msg}")

    # Calculate metrics
    verdict_format_pass = sum(results["verdict_format"]) / len(results["verdict_format"])
    verdict_correct_pass = sum(results["verdict_correct"]) / len(results["verdict_correct"])

    tp = confusion["TP"]
    tn = confusion["TN"]
    fp = confusion["FP"]
    fn = confusion["FN"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn)

    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Cases: {len(results['verdict_format'])}")
    print(f"\nJudges:")
    print(f"  verdict_format: {verdict_format_pass:.1%} pass rate (threshold: 100%)")
    print(f"  verdict_correct: {verdict_correct_pass:.1%} pass rate (threshold: 70%)")
    print(f"\nConfusion Matrix:")
    print(f"  TP={tp}  FP={fp}")
    print(f"  FN={fn}  TN={tn}")
    print(f"\nMetrics:")
    print(f"  Accuracy:  {accuracy:.1%}")
    print(f"  Precision: {precision:.1%}")
    print(f"  Recall:    {recall:.1%}")
    print(f"\nThresholds:")
    status_format = "PASS" if verdict_format_pass >= 1.0 else "FAIL"
    status_correct = "PASS" if verdict_correct_pass >= 0.7 else "FAIL"
    print(f"  verdict_format: {status_format}")
    print(f"  verdict_correct: {status_correct}")

    overall = "PASS" if (verdict_format_pass >= 1.0 and verdict_correct_pass >= 0.7) else "FAIL"
    print(f"\nOVERALL: {overall}")

if __name__ == '__main__':
    main()
