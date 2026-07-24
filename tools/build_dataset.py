#!/usr/bin/env python3
"""
Build evaluation dataset from OWASP Benchmark labels and code.
Strips comments from Java code and creates input.yaml (no labels) + reference.yaml (ground truth).
"""

import csv
import os
import re
import yaml
from collections import defaultdict
from pathlib import Path

# CONFIG
LABELS_CSV = "benchmark/expectedresults-1.2.csv"
BENCHMARK_DIR = "benchmark/testcode"
OUTPUT_DIR = "eval/_dataset/cases"
CASE_LIMIT = 40
BALANCE_LABELS = True

def strip_java_comments(code):
    """Remove single-line and multi-line comments from Java code."""
    # Remove multi-line comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    # Remove single-line comments
    code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
    return code

def load_labels():
    """Parse labels CSV and return list of test cases."""
    cases = []
    with open(LABELS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            testname = row['# test name'].strip()
            category = row[' category'].strip()
            real_vuln_str = row[' real vulnerability'].strip()
            cwe_str = row[' cwe'].strip()

            real_vuln = real_vuln_str.lower() == 'true'
            cwe = int(cwe_str) if cwe_str != '0' else None

            cases.append({
                'testname': testname,
                'category': category,
                'real_vulnerability': real_vuln,
                'cwe': cwe
            })
    return cases

def select_balanced_cases(cases, limit, balance):
    """Select cases with balanced labels and category diversity."""
    if not balance or len(cases) <= limit:
        return cases[:limit]

    # Group by vulnerability status and category
    by_vuln = defaultdict(list)
    for case in cases:
        key = (case['real_vulnerability'], case['category'])
        by_vuln[key].append(case)

    # Calculate target per group
    selected = []
    true_count = sum(len(v) for k, v in by_vuln.items() if k[0])
    false_count = sum(len(v) for k, v in by_vuln.items() if not k[0])

    target_true = limit // 2
    target_false = limit - target_true

    # Select from true vulnerabilities
    true_groups = [(k, v) for k, v in by_vuln.items() if k[0]]
    per_true_group = max(1, target_true // len(true_groups)) if true_groups else 0

    for key, group_cases in true_groups:
        selected.extend(group_cases[:per_true_group])
        if len(selected) >= target_true:
            break

    # Select from false vulnerabilities
    false_groups = [(k, v) for k, v in by_vuln.items() if not k[0]]
    per_false_group = max(1, target_false // len(false_groups)) if false_groups else 0

    for key, group_cases in false_groups:
        selected.extend(group_cases[:per_false_group])
        if len(selected) >= limit:
            break

    return selected[:limit]

def build_dataset():
    """Main dataset builder."""
    # Load and select cases
    all_cases = load_labels()
    selected = select_balanced_cases(all_cases, CASE_LIMIT, BALANCE_LABELS)

    # Statistics
    stats = {
        'total': len(selected),
        'real_vuln_true': sum(1 for c in selected if c['real_vulnerability']),
        'real_vuln_false': sum(1 for c in selected if not c['real_vulnerability']),
        'categories': defaultdict(int)
    }

    # Process each case
    written = 0
    skipped = []

    for case in selected:
        testname = case['testname']
        code_file = Path(BENCHMARK_DIR) / f"{testname}.java"

        if not code_file.exists():
            skipped.append(testname)
            continue

        # Read and strip comments
        code = code_file.read_text()
        code_stripped = strip_java_comments(code)

        # Create case directory
        case_dir = Path(OUTPUT_DIR) / f"case-{testname}"
        case_dir.mkdir(parents=True, exist_ok=True)

        # Write input.yaml (NO LABELS)
        input_data = {
            'prompt': (
                "Analyze the following code for security vulnerabilities. Decide whether it "
                "contains a real, exploitable vulnerability based ONLY on the executable logic "
                "(ignore comments). Respond with a fenced block:\n"
                "```verdict\n"
                "vulnerable: <true|false>\n"
                "cwe: <number or none>\n"
                "reasoning: <1-3 sentences grounded in the code's data/control flow>\n"
                "```"
            ),
            'code': code_stripped,
            'language': 'java'
        }

        with open(case_dir / 'input.yaml', 'w') as f:
            yaml.dump(input_data, f, default_flow_style=False, sort_keys=False)

        # Write reference.yaml (GROUND TRUTH - judge only)
        reference_data = {
            'real_vulnerability': case['real_vulnerability'],
            'cwe': case['cwe'],
            'category': case['category']
        }

        with open(case_dir / 'reference.yaml', 'w') as f:
            yaml.dump(reference_data, f, default_flow_style=False, sort_keys=False)

        stats['categories'][case['category']] += 1
        written += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"DATASET BUILD SUMMARY")
    print(f"{'='*60}")
    print(f"Total cases written: {written}")
    print(f"  Real vulnerabilities: {stats['real_vuln_true']} ({stats['real_vuln_true']/written*100:.1f}%)")
    print(f"  Not vulnerable: {stats['real_vuln_false']} ({stats['real_vuln_false']/written*100:.1f}%)")
    print(f"\nCategory breakdown:")
    for cat, count in sorted(stats['categories'].items()):
        print(f"  {cat}: {count}")

    if skipped:
        print(f"\nSkipped (code file not found): {len(skipped)}")
        for name in skipped[:5]:
            print(f"  - {name}")
        if len(skipped) > 5:
            print(f"  ... and {len(skipped) - 5} more")

    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    return written

if __name__ == '__main__':
    written = build_dataset()

    # Verify no label leakage
    print("Verifying no label leakage into input.yaml files...")
    leak_check = os.popen(f"grep -r 'real_vulnerability\\|cwe:' {OUTPUT_DIR}/*/input.yaml 2>/dev/null").read()

    if leak_check:
        print("⚠️  WARNING: Found potential label leakage!")
        print(leak_check)
    else:
        print("✓ No label leakage detected in input.yaml files")

    print(f"\n✓ Dataset build complete: {written} cases ready for evaluation")
