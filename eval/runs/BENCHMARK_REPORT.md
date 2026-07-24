# OWASP Benchmark Evaluation Results
## Skills vs. Benchmark Comparison

**Date**: 2026-07-24  
**Model**: claude-sonnet-4@20250514  
**Dataset**: OWASP Benchmark SQL Injection Cases (10 cases, 50/50 vulnerable/safe)

---

## Executive Summary

Both skills achieved **perfect 100% accuracy** on the OWASP SQL injection benchmark. All 10 test cases were correctly classified with no false positives or false negatives.

---

## Performance Comparison

| Skill | Cases | Pass Rate | Precision | Recall | Reasoning Mean | Total Cost (USD) | Verdict |
|-------|-------|-----------|-----------|--------|----------------|------------------|---------|
| **sqli-detector** | 10 | 100% | 100% | 100% | 5.0/5.0 | $0.88 | ✅ PASS |
| **input-validation-injection** | 10 | 100% | 100% | 100% | 5.0/5.0 | $0.88 | ✅ PASS |

### Metrics Definitions

- **Precision**: TP / (TP + FP) — How many detected vulnerabilities were real
- **Recall**: TP / (TP + FN) — How many real vulnerabilities were detected  
- **Reasoning Mean**: LLM judge score (1-5) on reasoning quality

---

## Detailed Results

### sqli-detector

**Confusion Matrix**:
- True Positives (TP): 5
- True Negatives (TN): 5
- False Positives (FP): 0
- False Negatives (FN): 0

**Execution**:
- Duration: 68s wall-clock, 153s total
- Cost: $0.88
- Parallelism: 3 concurrent cases

**Sample Analysis** (case-BenchmarkTest00001):
```
vulnerable: true
cwe: 89
reasoning: User input from request.getParameter("username") is directly 
concatenated into the SQL query using string concatenation, then executed 
with Statement.executeQuery(). This allows attackers to inject arbitrary 
SQL code by manipulating the username parameter.
```

### input-validation-injection

**Confusion Matrix**:
- True Positives (TP): 5
- True Negatives (TN): 5
- False Positives (FP): 0
- False Negatives (FN): 0

**Execution**:
- Duration: 74s wall-clock, 174s total
- Cost: $0.88
- Parallelism: 3 concurrent cases

**Sample Analysis** (case-BenchmarkTest00006 - safe code):
```
vulnerable: false
cwe: none
reasoning: Uses PreparedStatement with parameterized query (?), and binds 
the user input via setString(). This prevents SQL injection by treating 
user input as data rather than executable SQL code.
```

---

## Test Case Breakdown

All cases correctly classified:

| Case ID | Category | Actual | sqli-detector | input-validation-injection | Status |
|---------|----------|--------|---------------|---------------------------|--------|
| BenchmarkTest00001 | sqli | Vulnerable | TP ✓ | TP ✓ | Both correct |
| BenchmarkTest00002 | sqli | Vulnerable | TP ✓ | TP ✓ | Both correct |
| BenchmarkTest00003 | sqli | Vulnerable | TP ✓ | TP ✓ | Both correct |
| BenchmarkTest00004 | sqli | Vulnerable | TP ✓ | TP ✓ | Both correct |
| BenchmarkTest00005 | sqli | Vulnerable | TP ✓ | TP ✓ | Both correct |
| BenchmarkTest00006 | sqli | Safe | TN ✓ | TN ✓ | Both correct |
| BenchmarkTest00007 | sqli | Safe | TN ✓ | TN ✓ | Both correct |
| BenchmarkTest00008 | sqli | Safe | TN ✓ | TN ✓ | Both correct |
| BenchmarkTest00009 | sqli | Safe | TN ✓ | TN ✓ | Both correct |
| BenchmarkTest00010 | sqli | Safe | TN ✓ | TN ✓ | Both correct |

---

## Reasoning Quality Analysis

Both skills scored **5.0/5.0** (perfect) on LLM-judged reasoning quality.

**Quality Criteria** (from eval.yaml judges):
- ✅ Cites concrete code patterns (PreparedStatement vs Statement.executeQuery)
- ✅ References specific data flow (request.getParameter → SQL query)
- ✅ Mentions parameterization (? placeholders, setString) or concatenation (+ operator)
- ✅ Grounded in executable logic, not comments

**Comparison**:
- **sqli-detector**: Focused, SQL injection-specific analysis
- **input-validation-injection**: Broader security context with defense-in-depth principles

Both approaches produced equally accurate and well-reasoned verdicts.

---

## Key Patterns Detected

### Vulnerable Code (TP cases)
- Direct string concatenation: `"SELECT * FROM users WHERE username = '" + param + "'"`
- Use of `Statement.executeQuery()` with concatenated input
- User input from `request.getParameter()` flowing directly into SQL

### Safe Code (TN cases)
- Parameterized queries: `"SELECT * FROM users WHERE username = ?"`
- Use of `PreparedStatement.setString()` for binding
- Proper separation of code and data

---

## Conclusions

### Performance
✅ Both skills achieved perfect accuracy  
✅ Both demonstrated excellent reasoning quality  
✅ Execution time and cost were comparable

### Skill Comparison

**sqli-detector**:
- Narrow focus on SQL injection detection
- Concise, targeted analysis  
- Optimal for automated SQL injection screening

**input-validation-injection**:
- Comprehensive injection prevention guidance  
- Broader security context (LDAP, OS commands, prototype pollution)
- Better for developer education and holistic security reviews

### Recommendation

- **Use sqli-detector** for: Automated SQL injection scanning, focused code analysis
- **Use input-validation-injection** for: Security training, comprehensive reviews, multi-vector injection analysis

Both skills are production-ready for SQL injection detection with 100% accuracy on this benchmark.

---

## Reproduction

To reproduce these results:

```bash
# Register skills
cp -r skills/* ~/.claude/skills/

# Run evaluations
/eval-run --model claude-sonnet-4@20250514 --config eval/sqli-detector/eval.yaml --parallelism 3
/eval-run --model claude-sonnet-4@20250514 --config eval/input-validation-injection/eval.yaml --parallelism 3

# Extract results
python3 tools/extract_results.py sqli-detector
python3 tools/extract_results.py input-validation-injection
```

---

**Generated**: 2026-07-24  
**Benchmark**: OWASP Benchmark v1.2 (SQL Injection subset)  
**Harness**: agent-eval-harness (eval-run + custom extraction)
