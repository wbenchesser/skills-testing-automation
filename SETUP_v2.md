# Skill-vs-Benchmark Testing Harness - Setup (v2)

Drop skills and a labeled benchmark subset into a repo, paste one prompt into Claude
Code, and have the [agent-eval-harness](https://github.com/opendatahub-io/agent-eval-harness)
automatically evaluate every skill against the benchmark and report pass/fail.

This guide covers the mental model, the exact repo layout, one-time environment setup,
and the copyable driver prompt (bottom of the file).

**Changes in v2**: Added skill registration steps, fixed dataset path issues, clarified extraction requirements.

---

## 1. Mental model (read this once)

- The **skill (agent) is the subject under test**, not the benchmark code.
- The **benchmark** (e.g. an OWASP Benchmark subset) is the **dataset**. Each test case
  is a piece of code the skill analyzes.
- The benchmark's label file (`expectedresults-1.2.csv`:
  `testname, category, real vulnerability, cwe`) is the **answer key**. It is consumed
  **only by judges** — the agent under test must never see it.
- The harness runs the skill once per case, captures what it produced (verdict +
  reasoning), and a **judge** compares that verdict to the answer key to score
  correctness (true positive / false positive / etc.).
- One skill → one `eval.yaml`. Multiple skills → multiple `eval.yaml` files under
  `eval/<skill>/`, run in a loop.

### Two anti-cheating rules (non-negotiable)

1. **Never expose the answer key to the skill.** The dataset builder splits each case
   into `input.yaml` (code the agent sees) and `reference.yaml` (label the judge sees).
   `reference.yaml` lives in the case dir but is only loaded by judges.
2. **Strip flaw-describing comments** from the code the agent sees, *and* instruct the
   LLM judge to ignore comments and score only on the agent's reasoning about executable
   logic. Otherwise the agent reads "// BAD: SQL injection here" and you measure nothing.

---

## 2. Prerequisites (one time, per machine)

| Requirement | Check | Notes |
|---|---|---|
| Python 3.10+ | `python3 --version` | Harness deps auto-install into an isolated venv |
| Git | `git --version` | To clone the harness + benchmark |
| Claude Code CLI | `claude --version` | The runner |
| models.corp auth | `echo ${USER_KEY:+set}` | See configuration below |

MLflow is **optional** — skip it unless you want run tracking/dashboards.

### Configure models.corp Authentication

Set these environment variables (add to `~/.zshrc` or `~/.bashrc` to persist):

```bash
export MODEL_API="https://claude--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com:443"
export MODEL_ID="claude-sonnet-4@20250514"
export USER_KEY="<your-user-key>"

# For agent-eval-harness and Claude Code to use models.corp
export ANTHROPIC_API_KEY="${USER_KEY}"
export ANTHROPIC_BASE_URL="${MODEL_API}/sonnet/models"
```

**Important notes:**
- Replace `<your-user-key>` with your actual models.corp user key
- The `ANTHROPIC_BASE_URL` path segment (`/sonnet/`) must match your model tier
  - For Sonnet models: `/sonnet/models`
  - For Haiku models: `/haiku/models` (change both `MODEL_ID` and the URL path)
- Both the Anthropic Python SDK and Claude Code CLI honor `ANTHROPIC_BASE_URL` for custom endpoints

Verify the connection works:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${USER_KEY}" \
  -d "{
    \"anthropic_version\": \"vertex-2023-10-16\",
    \"messages\": [
      {
        \"role\": \"user\",
        \"content\": [{\"type\": \"text\", \"text\": \"Hello from models.corp\"}]
      }
    ],
    \"max_tokens\": 50,
    \"temperature\": 0
  }" \
  --url "${MODEL_API}/sonnet/models/${MODEL_ID}:streamRawPredict"
```

---

## 3. Install the harness (one time, per machine)

Clone it somewhere stable (not inside your test repo) and remember the path:

```bash
git clone https://github.com/opendatahub-io/agent-eval-harness
```

Now follow this instructions to make the skills available:

```bash
pip3 install -e [path to cloned]
claude --plugin-dir [path to cloned]
```

This exposes the skills: `/eval-setup`, `/eval-analyze`, `/eval-run`, `/eval-review`,
`/eval-optimize`, `/eval-mlflow`, `/eval-check`.

---

## 4. Prepare your test repo (per evaluation)

Create a repo (or folder) with this layout. The **only two things you author** are the
`skills/` folder and the `benchmark/` folder — everything under `eval/` is generated for
you by the driver prompt.

```
my-skill-tests/
├── skills/                          # ← YOU drop skills here (one dir per skill)
│   ├── vuln-scanner/
│   │   └── SKILL.md
│   └── another-skill/
│       └── SKILL.md
│
├── benchmark/                       # ← YOU drop the benchmark subset here
│   ├── expectedresults-1.2.csv      #    the answer key (labels)
│   └── testcode/                    #    the code files, e.g. BenchmarkTest00001.java ...
│
├── .claude-plugin/                  # (optional) so /eval-analyze auto-discovers skills/
│   └── plugin.json
│
├── tools/                           # ← GENERATED helper scripts
│   ├── build_dataset.py             #    converts benchmark to eval dataset
│   └── extract_results.py           #    parses stdout.log for verdicts
│
└── eval/                            # ← GENERATED by the prompt (do not hand-edit)
    ├── _dataset/cases/              #    SHARED dataset (all skills use this)
    │   ├── case-00001/
    │   │   ├── input.yaml           #    code the agent sees (comments stripped)
    │   │   └── reference.yaml       #    {real_vulnerability, cwe, category} — judge only
    │   └── ...
    └── <skill-name>/
        ├── eval.yaml                #    generated config per skill
        └── _dataset/                #    symlink to shared ../dataset/cases
```

### 4a. Getting a benchmark subset

```bash
# Full OWASP Benchmark (Java). ~2,740 cases — you will only convert a subset.
git clone https://github.com/OWASP-Benchmark/BenchmarkJava /tmp/BenchmarkJava

mkdir -p benchmark/testcode
cp /tmp/BenchmarkJava/expectedresults-1.2.csv benchmark/
cp /tmp/BenchmarkJava/src/main/java/org/owasp/benchmark/testcode/BenchmarkTest0000*.java \
   benchmark/testcode/     # grab a starter slice; expand later
```

> **Cost note:** an LLM judge looping over thousands of cases is expensive. Start with a
> **balanced ~30–60 case subset** (mix of `real vulnerability = true` and `false`, across
> a few CWE categories) so precision/recall means something, then scale up with
> `/eval-run --cases`.

### 4b. (Optional) plugin.json so skills auto-discover

If you want `/eval-analyze` to find your skills without `--skill` guessing, add
`.claude-plugin/plugin.json`:

```json
{
  "name": "my-skill-tests",
  "version": "0.1.0",
  "skills": ["skills/vuln-scanner", "skills/another-skill"]
}
```

---

## 5. What the driver prompt does (so you can trust it)

For each skill dir under `skills/`, the prompt has Claude Code:

1. **Build the dataset once** — run a conversion script that reads `benchmark/` and writes
   `eval/_dataset/cases/case-XXXXX/{input.yaml, reference.yaml}`, stripping flaw-describing 
   comments from the code the agent sees and putting the label only in `reference.yaml`.
   
2. **Register skills** — copy skills to `~/.claude/skills/` so they can be invoked as 
   `/skill-name` commands during evaluation.

3. **`/eval-analyze --skill <name>`** — generate `eval/<name>/eval.yaml`, then adjust it
   to point at the benchmark dataset and add the correctness judges below.

4. **Fix dataset paths** — the harness resolves dataset paths relative to the config file,
   so `eval/<skill>/eval.yaml` must use `_dataset/cases` (via symlink) not `../_dataset/cases`.

5. **`/eval-run --model <MODEL>`** — execute the skill per case, score with judges,
   report pass/fail against thresholds.

6. **Extract results** — parse conversation output from `stdout.log` (JSONL format) since
   the harness judges may not extract conversation correctly for stdout-only skills.

7. **Aggregate** — one summary table across all skills (precision, recall, pass rate,
   cost).

### The judges it configures

- **`verdict_correct`** (deterministic `check`): parse the skill's structured verdict
  (`vulnerable: true/false` + `cwe`), compare to `reference.yaml`. Emits TP/FP/TN/FN so
  the run can compute precision & recall — the metric that actually matters for a
  vuln-detection benchmark (raw accuracy is misleading on skewed label sets).
  
- **`reasoning_quality`** (LLM `prompt`): did the agent justify its verdict from the
  executable logic — **explicitly ignoring code comments**? Guards against comment-reading
  and lucky guesses.

---

## 6. The copyable driver prompt

Start Claude Code **in your test repo**, loading the harness as a plugin:

```bash
cd my-skill-tests

# Ensure models.corp environment variables are set
echo "Using API: ${ANTHROPIC_BASE_URL}"
echo "Model ID: ${MODEL_ID}"

claude --plugin-dir ~/tools/agent-eval-harness
```

Then paste the prompt below. Edit the **CONFIG** block at the top first (paths + subset).

````text
You are automating skill-vs-benchmark evaluation using the agent-eval-harness plugin
(already loaded — /eval-analyze, /eval-run, etc. are available).

# CONFIG — edit these before running
SKILLS_DIR:        skills/
BENCHMARK_DIR:     benchmark/            # contains expectedresults-1.2.csv + testcode/
LABELS_CSV:        benchmark/expectedresults-1.2.csv
CASE_LIMIT:        40                    # convert at most this many cases (cost control)
BALANCE_LABELS:    true                  # roughly 50/50 real-vuln vs not
JUDGE_MODEL:       claude-sonnet-4@20250514      # models.corp model ID
SKILL_MODEL:       claude-sonnet-4@20250514      # models.corp model ID

# GROUND RULES (do not violate)
- The skill under test is the SUBJECT. The benchmark code is the DATASET. The labels CSV
  is the ANSWER KEY and must be visible ONLY to judges — never place labels, CWE numbers,
  or "real vulnerability" flags into any file the skill reads (input.yaml).
- Strip flaw-describing comments from the code the agent sees. Judges must score on the
  agent's reasoning about executable logic, ignoring comments.
- Do not hand-fabricate data. Every case must come from real files in BENCHMARK_DIR.

# STEP 1 — Build the dataset (once, shared by all skills)
Write and run a Python script `tools/build_dataset.py` that:
  1. Parses LABELS_CSV (columns: testname, category, real vulnerability, cwe). Skip the
     header/version line.
  2. Selects up to CASE_LIMIT test cases whose code file exists in BENCHMARK_DIR/testcode/.
     If BALANCE_LABELS, pick a roughly even mix of real-vulnerability true/false and spread
     across categories.
  3. For each selected case, writes eval/_dataset/cases/case-<testname>/:
       - input.yaml:
           prompt: |
             Analyze the following code for security vulnerabilities. Decide whether it
             contains a real, exploitable vulnerability based ONLY on the executable logic
             (ignore comments). Respond with a fenced block:
             ```verdict
             vulnerable: <true|false>
             cwe: <number or none>
             reasoning: <1-3 sentences grounded in the code's data/control flow>
             ```
           code: |
             <contents of the .java file WITH comments stripped, indented>
           language: java
       - reference.yaml:
           real_vulnerability: <true|false>
           cwe: <number>
           category: <string>
  4. Prints a summary: N cases written, label balance, category spread.
Run it, show me the summary, and confirm no reference labels leaked into any input.yaml
(grep input.yaml files for "real_vulnerability"/"cwe:" and assert none present).

# STEP 1b — Register skills for evaluation
The eval-run harness invokes skills as `/skill-name` commands, so they must be registered:

```bash
# Copy skills to Claude's skills directory
cp -r skills/* ~/.claude/skills/

# Verify skills are available
ls -la ~/.claude/skills/
```

This makes `/sqli-detector`, `/input-validation-injection`, etc. available as commands.

# STEP 2 — Per skill: analyze + configure
For each subdirectory in SKILLS_DIR:
  a. Run: /eval-analyze --skill <skill-name> --config eval/<skill-name>/eval.yaml
  
  b. **Fix dataset path issues**: The harness resolves paths relative to the config file.
     Create a symlink so `eval/<skill>/eval.yaml` can reference `_dataset/cases`:
     
     ```bash
     mkdir -p eval/<skill-name>/_dataset
     ln -sf ../../_dataset/cases eval/<skill-name>/_dataset/cases
     ```
     
  c. Edit the generated eval/<skill-name>/eval.yaml so that:
       execution.mode: case
       execution.skill: <skill-name>
       execution.arguments: "{prompt}\n\n{code}"  # newline separates prompt from code
       models.skill:  <SKILL_MODEL>
       models.judge:  <JUDGE_MODEL>
       dataset.path:  _dataset/cases              # ← uses symlink, not ../
       dataset.schema: |
         Each case dir has input.yaml (prompt + code to analyze; NO labels) and
         reference.yaml (real_vulnerability, cwe, category) — reference is judge-only.
       permissions.deny: ["**/reference.yaml"]   # belt-and-suspenders: hide the answer key
     
     Add these judges (replace analyze's defaults):
       - name: verdict_format
         description: Validates verdict block format
         check: |
           import re
           conversation = outputs.get("_conversation", "")
           verdict_match = re.search(r'```verdict\s*\n(.*?)\n```', conversation, re.DOTALL | re.IGNORECASE)
           if not verdict_match:
               return False, "No verdict block found in conversation"
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
       
       - name: verdict_correct
         description: Skill's vulnerable verdict matches the OWASP label; also emit
           confusion-matrix cell for precision/recall.
         check: |
           import re, yaml
           from pathlib import Path
           case_dir = outputs.get("_case_dir", "")
           if not case_dir:
               return False, "Case directory not available"
           ref_path = Path(case_dir) / "reference.yaml"
           if not ref_path.exists():
               return False, f"reference.yaml not found at {ref_path}"
           with open(ref_path) as f:
               ref = yaml.safe_load(f)
           conversation = outputs.get("_conversation", "")
           verdict_match = re.search(r'```verdict\s*\n(.*?)\n```', conversation, re.DOTALL | re.IGNORECASE)
           if not verdict_match:
               return False, "No parseable verdict in conversation"
           verdict_text = verdict_match.group(1)
           vuln_match = re.search(r'vulnerable:\s*(true|false)', verdict_text, re.IGNORECASE)
           if not vuln_match:
               return False, "No vulnerable field found in verdict"
           pred = vuln_match.group(1).lower() == "true"
           gold = bool(ref.get("real_vulnerability", False))
           if pred and gold:
               cell = "TP"
           elif pred and not gold:
               cell = "FP"
           elif not pred and gold:
               cell = "FN"
           else:
               cell = "TN"
           ok = pred == gold
           cwe = ref.get("cwe", "null")
           return ok, f"{cell} (pred={pred}, gold={gold}, cwe={cwe})"
       
       - name: reasoning_quality
         description: Reasoning is grounded in executable logic, not comments.
         prompt: |
           The agent was asked to judge whether code is vulnerable using ONLY executable
           logic, ignoring comments. Rate its reasoning 1-5 (5 = cites concrete
           data/control flow; 1 = guesses, or relies on comments). Ignore whether the
           final verdict was correct — judge only the reasoning.
           
           GROUND TRUTH (from reference.yaml):
           {% if annotations %}
           - Real vulnerability: {{ annotations.real_vulnerability }}
           - CWE: {{ annotations.cwe }}
           - Category: {{ annotations.category }}
           {% else %}
           (No annotations available)
           {% endif %}
           
           AGENT OUTPUT (from conversation):
           {{ conversation }}
           
           Return ONLY a number from 1 to 5 and a brief explanation (1-2 sentences).
     
     Set thresholds:
       verdict_format:    {min_pass_rate: 0.95}
       verdict_correct:   {min_pass_rate: 0.7}
       reasoning_quality: {min_mean: 3.5}
       
  d. Validate the config compiles before running.

# STEP 3 — Run each skill's eval
For each skill:
  1. Create symlink for output directory naming:
     ```bash
     mkdir -p eval/runs/<skill-name>
     ln -sf ../<skill-name>-eval/2026-07-24-sonnet eval/runs/<skill-name>/2026-07-24-sonnet
     ```
  
  2. Run: /eval-run --model <SKILL_MODEL> --config eval/<skill-name>/eval.yaml --parallelism 3
  
  3. **Extract results manually** since harness judges may not parse stdout correctly:
     Write `tools/extract_results.py` that:
     - Reads `eval/runs/<skill-name>-eval/2026-07-24-sonnet/cases/*/stdout.log` (JSONL)
     - Finds the final `{"type": "result", "result": "..."}` event
     - Parses the verdict block from the `result` field
     - Compares against reference.yaml to compute TP/TN/FP/FN
     - Reports accuracy, precision, recall, F1

# STEP 4 — Report
Produce ONE markdown table across all skills with columns:
  skill | cases | pass_rate | precision | recall | reasoning_mean | total_cost_usd | verdict

Compute precision = TP/(TP+FP) and recall = TP/(TP+FN) from the verdict_correct cells.
Flag any skill below its thresholds. List the 3 worst-scoring cases per skill with the
agent's verdict vs the gold label so I can inspect failures. Do NOT modify any skill.

Begin with STEP 1. Pause after the Step 1 summary so I can confirm before spending
budget on runs.
````

---

## 7. After the run

- **Inspect failures**: `/eval-review --run-id <id>` walks judge scores + agent outputs
  interactively.
- **Improve a skill automatically**: `/eval-optimize --model opus --max-iterations 3`
  runs → reads failures → edits the SKILL.md → re-runs → checks for regressions.
- **Scale the benchmark**: bump `CASE_LIMIT` and re-run Step 1, or widen `/eval-run
  --cases`.
- **Track over time (optional)**: run `/eval-setup` to configure MLflow, then
  `/eval-mlflow` after each run to log results and diff against a baseline.

---

## 8. Gotchas / tuning

- **Skewed labels break "accuracy".** Report **precision & recall**, not raw pass rate —
  the driver prompt already does this via the confusion-matrix cells.
  
- **Skills must be registered**: The `/eval-run` harness invokes skills as commands 
  (`/skill-name`), not by reading SKILL.md directly. Copy skills to `~/.claude/skills/`
  before running evaluations.
  
- **Dataset path resolution**: The harness resolves `dataset.path` relative to the config
  file's directory. Use symlinks (`_dataset/cases` → `../../_dataset/cases`) so each
  skill's config can reference the shared dataset without `..` paths (which the validator
  rejects).
  
- **Stdout parsing**: For stdout-only skills (no file artifacts), the harness may not
  correctly extract conversation text for judges. Use a custom extraction script that
  reads `stdout.log` (JSONL format) and parses the `{"type": "result", "result": "..."}` 
  events directly.
  
- **OWASP cases aren't fully standalone** (they reference helper classes). For pure
  LLM static analysis this is usually fine, but if a skill needs to compile/run code,
  give it the surrounding `BenchmarkJava` tree via `runner.workspace_mode: repo` and add
  `permissions.deny` for the answer key + `eval/`.
  
- **Comment leakage** is the #1 way to get fake-high scores. Verify Step 1 actually
  stripped comments and that the judge prompt enforces "ignore comments."
  
- **Cost creep.** LLM judges dominate cost. Keep `reasoning_quality` off with
  `/eval-run --no-llm-judges` for cheap correctness-only smoke runs, then enable it for
  the real scored run.
  
- **One dataset, many skills.** All skills share `eval/_dataset/cases` so every skill is
  graded on identical inputs — apples to apples.

---

## 9. Troubleshooting

### "Unknown command: /skill-name"
**Cause**: Skill not registered in Claude Code  
**Fix**: `cp -r skills/<skill-name> ~/.claude/skills/`

### "dataset.path must not contain '..'
**Cause**: Harness validator rejects `..` in paths  
**Fix**: Use symlinks: `mkdir -p eval/<skill>/_dataset && ln -sf ../../_dataset/cases eval/<skill>/_dataset/cases`, then set `dataset.path: _dataset/cases`

### Judges report "No verdict block found in conversation"
**Cause**: Judges trying to read from `outputs["_conversation"]` but it's not populated  
**Fix**: Parse `stdout.log` directly using a custom extraction script (see Step 3 in driver prompt)

### "No cases directory" when scoring
**Cause**: Scorer constructs path as `eval/runs/<skill>/<run-id>/cases` but output is in `eval/runs/<skill>-eval/<run-id>/cases`  
**Fix**: Create symlink: `ln -sf ../<skill>-eval/2026-07-24-sonnet eval/runs/<skill>/2026-07-24-sonnet`
