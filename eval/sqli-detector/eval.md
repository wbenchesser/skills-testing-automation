---
skill: sqli-detector
analyzed_at: 2026-07-24
skill_hash: 5d55ae681feb
---

# SQL Injection Detector Skill Analysis

## Purpose

Analyze Java code for SQL injection vulnerabilities, distinguishing between safe parameterized queries and vulnerable string concatenation patterns.

## Pipeline Flow

This is a direct, single-level skill with no sub-skills:

1. Skill receives prompt containing both instructions and Java servlet code
2. LLM analyzes code following rules in SKILL.md
3. LLM identifies SQL query construction patterns (concatenation vs parameterization)
4. LLM traces data flow from untrusted sources (`request.getParameter`) to SQL queries
5. LLM outputs structured verdict block in conversation text

## Inputs

Each test case provides three fields in `input.yaml`:
- `prompt`: Instructions to analyze code and return verdict in specific format
- `code`: Java servlet code (comments stripped) to analyze
- `language`: Always "java" for this dataset

No companion files required — skill operates entirely on data in the prompt.

## Outputs

**Stdout-only skill** — produces conversation text, not file artifacts.

Expected output format:
```verdict
vulnerable: <true|false>
cwe: <89 if SQL injection found, otherwise none>
reasoning: <1-3 sentences explaining the analysis>
```

Judges must use `{{ conversation }}` template variable to access this output.

## Quality Criteria

### Good Output
- Correctly identifies vulnerable patterns (string concatenation: `"SELECT * FROM users WHERE username = '" + param + "'"`)
- Correctly identifies safe patterns (PreparedStatement with `?` placeholders and `setString()`)
- Reasoning cites specific code evidence: "User input from request.getParameter flows directly into SQL via string concatenation"
- CWE 89 assigned only when SQL injection is present

### Bad Output
- Misses vulnerable concatenation (false negative)
- Flags safe PreparedStatement usage (false positive)
- Generic reasoning without code-specific evidence
- Reasoning based on comments rather than executable logic

## Evaluation Focus

1. **Classification accuracy** (most critical): True positive and true negative rates
2. **Reasoning grounding**: Does explanation cite actual code patterns vs generic principles?
3. **Data flow analysis**: Does it correctly trace user input to SQL execution?
4. **Pattern recognition**: Distinguishes Statement.executeQuery(concatenated) from PreparedStatement

## No External Dependencies

- No AskUserQuestion calls
- No MCP tools or external APIs
- No filesystem reads/writes
- Completely self-contained and headless-compatible
