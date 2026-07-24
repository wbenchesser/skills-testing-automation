#!/usr/bin/env python3
"""Extract conversation text from stdout.log for stdout-only skills."""
import json
import sys
from pathlib import Path

def extract_conversation_from_stdout(stdout_file):
    """Extract result field from JSON events in stdout.log."""
    conversation_parts = []

    with open(stdout_file) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                # Look for result field in events
                if "result" in event:
                    result_text = event.get("result", "")
                    if result_text and result_text not in conversation_parts:
                        conversation_parts.append(result_text)
            except json.JSONDecodeError:
                # Not JSON, skip
                continue

    return "\n\n".join(conversation_parts)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <cases_directory>")
        sys.exit(1)

    cases_dir = Path(sys.argv[1])

    for case_dir in sorted(cases_dir.iterdir()):
        if not case_dir.is_dir():
            continue

        stdout_file = case_dir / "stdout.log"
        if not stdout_file.exists():
            print(f"WARNING: No stdout.log in {case_dir.name}")
            continue

        conversation = extract_conversation_from_stdout(stdout_file)

        # Write to conversation.txt
        output_file = case_dir / "conversation.txt"
        with open(output_file, 'w') as f:
            f.write(conversation)

        print(f"{case_dir.name}: extracted {len(conversation)} chars")

if __name__ == '__main__':
    main()
