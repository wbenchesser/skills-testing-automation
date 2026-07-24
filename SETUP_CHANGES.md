# SETUP.md Changes for Smoother Evaluation Flow

## Key Issues Encountered & Fixes

### 1. **Skill Registration Required** ✅ CRITICAL
**Problem**: The eval-run harness tried to invoke `/sqli-detector` as a command, but got "Unknown command" errors because skills weren't registered in Claude Code.

**Root cause**: The harness invokes skills as slash commands, not by reading SKILL.md files directly.

**Fix added to SETUP_v2.md**:
- **New Step 1b**: Register skills before running evaluations
  ```bash
  cp -r skills/* ~/.claude/skills/
  ```
- Added to troubleshooting section
- Clarified in "What the driver prompt does" section

---

### 2. **Dataset Path Resolution Issues** ✅ CRITICAL
**Problem**: Using `dataset.path: ../_dataset/cases` failed with validator error: "dataset.path must not contain '..'"

**Root cause**: The harness resolves paths relative to the config file's directory and the validator rejects `..` paths.

**Fix added to SETUP_v2.md**:
- **New Step 2b**: Create symlinks for each skill
  ```bash
  mkdir -p eval/<skill-name>/_dataset
  ln -sf ../../_dataset/cases eval/<skill-name>/_dataset/cases
  ```
- Changed `dataset.path` from `../_dataset/cases` to `_dataset/cases`
- Added troubleshooting entry
- Updated directory tree to show symlink structure

---

### 3. **Conversation Extraction from Stdout** ✅ IMPORTANT
**Problem**: The harness judges couldn't extract conversation text from `outputs["_conversation"]`, leading to 0% pass rates on format/correctness judges.

**Root cause**: For stdout-only skills, the harness doesn't properly populate the `_conversation` field that inline check judges expect.

**Fix added to SETUP_v2.md**:
- **New Step 3.3**: Added custom extraction script requirement
- Created `tools/extract_results.py` template
- Documents parsing `stdout.log` (JSONL format) for `{"type": "result", "result": "..."}` events
- Added troubleshooting entry

---

### 4. **Output Directory Naming Mismatch** ✅ WORKAROUND
**Problem**: Scorer looked for `eval/runs/<skill>/<run-id>/cases` but execute.py created `eval/runs/<skill>-eval/<run-id>/cases`.

**Root cause**: Eval name from config (`sqli-detector-eval`) differs from skill name (`sqli-detector`), causing path construction mismatch.

**Fix added to SETUP_v2.md**:
- **New Step 3.1**: Create symlink before scoring
  ```bash
  mkdir -p eval/runs/<skill-name>
  ln -sf ../<skill-name>-eval/2026-07-24-sonnet eval/runs/<skill-name>/2026-07-24-sonnet
  ```
- Added troubleshooting entry
- Documented the path construction issue

---

### 5. **Argument Formatting for Code** ✅ CLARIFICATION
**Problem**: Initial config had just `{prompt}` but code needed to be on separate lines for proper formatting.

**Fix added to SETUP_v2.md**:
- Changed `execution.arguments` from `"{prompt}"` to `"{prompt}\n\n{code}"`
- Added comment explaining the newline separator
- This ensures code appears as a distinct block after the prompt

---

### 6. **Judge Implementation Updates** ✅ IMPROVEMENT
**Problem**: Original judges in prompt didn't handle all edge cases (missing fields, file paths, conversation extraction).

**Fix added to SETUP_v2.md**:
- Added `verdict_format` judge (validates structure before correctness)
- Updated `verdict_correct` judge with proper error handling:
  - Checks for `_case_dir` availability
  - Verifies reference.yaml exists
  - Better error messages
- Updated `reasoning_quality` judge with Jinja2 template for annotations
- All judges now handle missing/malformed data gracefully

---

### 7. **Directory Structure Documentation** ✅ CLARITY
**Problem**: Original SETUP.md didn't show where generated helper scripts live.

**Fix added to SETUP_v2.md**:
- Added `tools/` directory to tree structure
- Shows `build_dataset.py` and `extract_results.py` locations
- Clarified `eval/_dataset/cases/` is shared across all skills
- Documented symlink structure under each skill's config directory

---

## Summary of Additions to SETUP_v2.md

### New Sections
1. **Step 1b**: Skill registration process
2. **Step 2b**: Dataset path symlink creation
3. **Step 3.1**: Output directory symlink creation
4. **Step 3.3**: Custom results extraction
5. **Section 9**: Comprehensive troubleshooting guide

### Updated Content
- Directory tree shows `tools/` and symlinks
- Driver prompt includes all workaround steps
- Judge implementations are production-ready
- Execution arguments properly formatted
- All file paths relative to config directory

### New Troubleshooting Entries
1. "Unknown command: /skill-name"
2. "dataset.path must not contain '..'"
3. "No verdict block found in conversation"
4. "No cases directory" when scoring

---

## Recommended Next Steps

### For SETUP.md v3 (if needed)
1. **Upstream fixes**: Report dataset path and conversation extraction issues to agent-eval-harness maintainers
2. **Automated workarounds**: Add these symlink/registration steps to a setup script
3. **Better defaults**: Pre-configure judges in eval-analyze for benchmark evaluation use cases

### For This Repo
1. **Keep SETUP_v2.md** as the working version
2. **Archive SETUP.md** as `SETUP_v1_original.md`
3. **Add** `tools/setup_evaluation.sh` script that automates:
   - Skill registration
   - Symlink creation  
   - Directory structure verification

---

## Testing Checklist

Before considering SETUP_v2.md complete, test:
- [ ] Fresh clone → follow SETUP_v2.md → runs successfully
- [ ] Multiple skills → all get proper symlinks → no path errors
- [ ] Results extraction → parses verdicts correctly → accurate metrics
- [ ] Troubleshooting section → covers all errors we hit

---

## Cost/Time Impact of Hiccups

**Time spent on workarounds**: ~30 minutes
- 5 min: Skill registration discovery
- 10 min: Dataset path debugging  
- 10 min: Conversation extraction diagnosis
- 5 min: Symlink creation for scoring

**Without SETUP_v2.md fixes**: Future users would hit the same issues.

**With SETUP_v2.md**: These are now documented upfront, saving future time.
