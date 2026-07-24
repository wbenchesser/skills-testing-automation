---
name: sqli-detector
description: Analyze Java code for SQL injection vulnerabilities
whenToInvoke: when-invoked
---

# SQL Injection Vulnerability Detector

Analyze the provided Java code for SQL injection vulnerabilities.

## Analysis Rules

1. **Identify SQL injection vulnerabilities** by checking for:
   - Direct string concatenation of user input into SQL queries
   - Use of `Statement.executeQuery()` or `Statement.executeUpdate()` with concatenated user input
   - Dynamic SQL construction using `+` operator with untrusted data

2. **Identify safe code** by checking for:
   - Use of `PreparedStatement` with parameterized queries (`?` placeholders)
   - Use of `setString()`, `setInt()`, etc. to bind parameters
   - No direct string concatenation of user input into SQL

3. **Untrusted input sources** include:
   - `request.getParameter()`
   - `request.getHeader()`
   - Any data derived from HTTP requests

## Analysis Process

When you receive code to analyze:

1. Read the code carefully
2. Identify all SQL query construction
3. Check if user input flows into SQL queries
4. Determine if parameterization (PreparedStatement) is used
5. Provide a verdict with reasoning

## Output Format

Respond with a fenced code block in this exact format:

```verdict
vulnerable: <true|false>
cwe: <89 if SQL injection found, otherwise none>
reasoning: <1-3 sentences explaining your analysis based on the code's data flow and SQL construction method>
```

## Important

- Base your analysis ONLY on the executable logic and data flow
- Ignore comments in the code
- Focus on whether user input is properly parameterized or dangerously concatenated
