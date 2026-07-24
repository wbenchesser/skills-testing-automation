---
skill: sqli-detector
analyzed_at: 2026-07-24T00:00:00Z
skill_hash: 5d55ae681feb
---

# sqli-detector Skill Analysis

## Purpose

Analyze Java code to detect SQL injection vulnerabilities by identifying unsafe string concatenation of user input into SQL queries.

## Pipeline

The sqli-detector skill is a single-level, stdout-only analysis skill:

1. **Input Reception**: Receives Java source code + analysis instructions
2. **Pattern Detection**: Identifies SQL injection anti-patterns:
   - Direct string concatenation of user input into SQL queries
   - Use of `Statement.executeQuery/executeUpdate` with concatenated input
   - Dynamic SQL construction using `+` operator with untrusted data
3. **Safe Pattern Recognition**: Recognizes secure implementations:
   - `PreparedStatement` with parameterized queries (`?` placeholders)
   - Use of `setString()`, `setInt()` for parameter binding
4. **Data Flow Analysis**: Traces untrusted input sources:
   - `request.getParameter()`
   - `request.getHeader()`
   - Other HTTP request-derived data
5. **Verdict Generation**: Outputs structured verdict block in conversation

## Input Structure

Each test case provides (via `input.yaml`):
- `prompt`: Analysis instructions specifying to use only executable logic
- `code`: Java source code with comments stripped (prevents answer leakage)
- `language`: Always "java"

## Output Structure

**STDOUT-ONLY**: No file artifacts. Produces conversational text with:

```verdict
vulnerable: <true|false>
cwe: <89 if SQL injection, otherwise none>
reasoning: <1-3 sentences grounded in code's data flow>
```

Judges must use `{{ conversation }}` template variable, NOT `{{ outputs }}` for files.

## Quality Criteria

### Good Output
- Correctly identifies string concatenation of user input in SQL
- Distinguishes PreparedStatement (safe) from Statement+concatenation (unsafe)
- Reasoning cites specific variable names, method calls, data flow
- Ignores comments completely
- Correct CWE-89 assignment for SQL injection

### Bad Output
- False positives/negatives on vulnerability detection
- Reasoning based on comments rather than executable logic
- Vague claims without code references
- Malformed verdict block
- Incorrect or missing CWE

## Evaluation Strategy

1. **Format Validation** (`verdict_format` judge): Ensure verdict block parseable
2. **Detection Accuracy** (`verdict_correct` judge): Compare against OWASP Benchmark ground truth, compute TP/TN/FP/FN for precision/recall
3. **Reasoning Quality** (`reasoning_quality` LLM judge): Score 1-5 based on code-grounded analysis vs superficial patterns

## Edge Cases

- Multi-hop data flow (parameter → variable → variable → SQL)
- Mixed safe/unsafe patterns in same file
- Input validation that doesn't prevent SQL injection
- Boundary cases (concatenating literals vs user input)

## No External Dependencies

- No sub-skills invoked
- No file system writes
- No MCP tools or API calls
- No AskUserQuestion interactions
- No companion files required

Ideal for headless evaluation with no mocking needed.
