---
skill: input-validation-injection
analyzed_at: 2026-07-24
skill_hash: 73c2faf281ee
---

# Input Validation and Injection Defense Skill Analysis

## Purpose

Comprehensive security guidance for preventing injection vulnerabilities across SQL, LDAP, OS commands, prototype pollution, and general input validation. Applied to OWASP benchmark for SQL injection detection comparison.

## Pipeline Flow

Knowledge-based skill providing defensive coding patterns and validation strategies:

1. Skill receives code to analyze for injection vulnerabilities
2. LLM applies comprehensive guidance from SKILL.md covering:
   - Core validation strategy (positive validation, parameterization)
   - SQL injection prevention (PreparedStatement usage)
   - LDAP, OS command, prototype pollution defenses
   - Implementation checklist and test plan
3. LLM analyzes code against safe patterns
4. LLM outputs structured verdict and guidance

## Inputs

Each test case provides three fields in `input.yaml`:
- `prompt`: Instructions to analyze code and return verdict
- `code`: Java servlet code (comments stripped) to analyze
- `language`: Always "java" for this dataset

The skill applies its broad injection prevention framework specifically to SQL injection cases in the benchmark.

## Outputs

**Stdout-only skill** — produces conversation text with analysis and guidance.

Expected output format (for benchmark comparison):
```verdict
vulnerable: <true|false>
cwe: <89 if SQL injection found, otherwise none>
reasoning: <explanation applying comprehensive guidance>
```

The reasoning should reflect the skill's broader security perspective:
- Validation strategy (parameterization vs concatenation)
- Safe pattern recommendations (PreparedStatement)
- Defense-in-depth principles
- Specific code pattern analysis

Judges must use `{{ conversation }}` template variable to access this output.

## Quality Criteria

### Good Output
- Correctly classifies vulnerable vs safe code
- Reasoning references comprehensive guidance (validation strategy, parameterization, safe APIs)
- Applies defense-in-depth thinking
- Cites specific code patterns from the skill's examples
- May provide additional context beyond simple detection (e.g., least privilege, escaping limitations)

### Bad Output
- Incorrect classification (misses vulnerabilities or false alarms)
- Generic reasoning without applying the skill's comprehensive framework
- No reference to safe patterns or validation strategies
- Missing guidance on defensive coding

## Comparison with sqli-detector

- **sqli-detector**: Narrow SQL injection analyzer
- **input-validation-injection**: Comprehensive security guidance framework applied to SQL injection cases

Both skills tested on the same benchmark to compare:
1. Detection accuracy (precision/recall)
2. Reasoning quality and depth
3. Practical guidance value

## Evaluation Focus

1. **Classification accuracy**: Same as sqli-detector (TP/TN/FP/FN rates)
2. **Reasoning depth**: Does it apply comprehensive guidance vs narrow pattern matching?
3. **Guidance value**: Does output help developers understand defense-in-depth?
4. **Pattern application**: References PreparedStatement, validation strategy, safe APIs

## No External Dependencies

- No AskUserQuestion calls
- No MCP tools or external APIs
- No filesystem reads/writes
- Completely self-contained and headless-compatible
