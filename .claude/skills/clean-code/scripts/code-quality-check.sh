#!/bin/bash
# Code Quality Check - Language Agnostic
# Usage: code-quality-check.sh <source-path>
#
# Performs 6 quality checks based on Clean Code principles.

SOURCE_PATH="${1:-.}"
ISSUES=0

echo "=== Clean Code Quality Check ==="
echo "Path: $SOURCE_PATH"
echo "Date: $(date '+%Y-%m-%d %H:%M')"
echo ""

# --- Check 1: Magic Numbers (G25) ---
echo "--- Check 1: Magic Numbers (G25) ---"
MAGIC=$(grep -rn '[^a-zA-Z0-9_"'\'']\b[0-9]\{2,\}\b[^a-zA-Z0-9_"'\'']' "$SOURCE_PATH" \
    --include="*.java" --include="*.py" --include="*.ts" --include="*.js" --include="*.kt" --include="*.go" \
    -c 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
if [[ $MAGIC -gt 0 ]]; then
    echo "  WARN: $MAGIC potential magic numbers found"
    echo "  Tip: Replace with named constants (G25)"
    ((ISSUES++))
else
    echo "  OK: No magic numbers detected"
fi
echo ""

# --- Check 2: Commented-Out Code (C5) ---
echo "--- Check 2: Commented-Out Code (C5) ---"
COMMENTED=$(grep -rn '^\s*//\s*\(public\|private\|protected\|class\|import\|return\|if\|for\|while\|try\)' "$SOURCE_PATH" \
    --include="*.java" --include="*.kt" --include="*.ts" --include="*.js" \
    -c 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
COMMENTED_PY=$(grep -rn '^\s*#\s*\(def\|class\|import\|return\|if\|for\|while\|try\)' "$SOURCE_PATH" \
    --include="*.py" \
    -c 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
COMMENTED=$((COMMENTED + COMMENTED_PY))
if [[ $COMMENTED -gt 0 ]]; then
    echo "  WARN: $COMMENTED potential commented-out code blocks"
    echo "  Tip: Delete commented code — VCS remembers (C5)"
    ((ISSUES++))
else
    echo "  OK: No commented-out code detected"
fi
echo ""

# --- Check 3: TODO without Ticket ---
echo "--- Check 3: TODO without Ticket ---"
TODO_NO_TICKET=$(grep -rn 'TODO' "$SOURCE_PATH" \
    --include="*.java" --include="*.py" --include="*.ts" --include="*.js" --include="*.kt" --include="*.go" \
    2>/dev/null | grep -v -iE '(JIRA|ISSUE|TICKET|#[0-9]|[A-Z]+-[0-9]+)' | wc -l)
if [[ $TODO_NO_TICKET -gt 0 ]]; then
    echo "  WARN: $TODO_NO_TICKET TODO(s) without ticket reference"
    echo "  Tip: Add ticket number: // TODO: JIRA-123"
    ((ISSUES++))
else
    echo "  OK: All TODOs have ticket references (or none found)"
fi
echo ""

# --- Check 4: Long Files (>200 lines) ---
echo "--- Check 4: Long Files (>200 lines, SRP) ---"
LONG_FILES=0
while IFS= read -r file; do
    lines=$(wc -l < "$file")
    if [[ $lines -gt 200 ]]; then
        echo "  WARN: $file = $lines lines"
        ((LONG_FILES++))
    fi
done < <(find "$SOURCE_PATH" -type f \( -name "*.java" -o -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.kt" -o -name "*.go" \) ! -path "*/node_modules/*" ! -path "*/target/*" ! -path "*/.git/*" ! -path "*/build/*" ! -path "*/dist/*" ! -name "*Test*" ! -name "*test_*" ! -name "*.spec.*")
if [[ $LONG_FILES -gt 0 ]]; then
    echo "  WARN: $LONG_FILES file(s) exceed 200 lines — consider SRP (Ch10)"
    ((ISSUES++))
else
    echo "  OK: All source files within 200 lines"
fi
echo ""

# --- Check 5: Null Returns ---
echo "--- Check 5: Null Returns (Ch7) ---"
NULL_RETURNS=$(grep -rn 'return null' "$SOURCE_PATH" \
    --include="*.java" --include="*.kt" --include="*.ts" --include="*.js" \
    -c 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
NULL_RETURNS_PY=$(grep -rn 'return None' "$SOURCE_PATH" \
    --include="*.py" \
    -c 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
NULL_RETURNS=$((NULL_RETURNS + NULL_RETURNS_PY))
if [[ $NULL_RETURNS -gt 0 ]]; then
    echo "  WARN: $NULL_RETURNS null/None returns found"
    echo "  Tip: Use Optional/Result type instead (Ch7)"
    ((ISSUES++))
else
    echo "  OK: No null returns detected"
fi
echo ""

# --- Check 6: Console Output ---
echo "--- Check 6: Console Output ---"
CONSOLE=$(grep -rn 'System\.out\.\|console\.log\|print(' "$SOURCE_PATH" \
    --include="*.java" --include="*.ts" --include="*.js" --include="*.py" \
    -c 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
if [[ $CONSOLE -gt 0 ]]; then
    echo "  WARN: $CONSOLE console output statements found"
    echo "  Tip: Use a proper logger"
    ((ISSUES++))
else
    echo "  OK: No console output detected"
fi
echo ""

# --- Summary ---
echo "=== Summary ==="
echo "Checks run: 6"
echo "Issues found: $ISSUES"

if [[ $ISSUES -gt 0 ]]; then
    echo "STATUS: WARN - $ISSUES check(s) need attention"
    exit 1
else
    echo "STATUS: OK - All checks passed"
    exit 0
fi
