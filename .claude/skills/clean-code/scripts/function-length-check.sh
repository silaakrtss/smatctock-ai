#!/bin/bash
# Function/Method Length Checker - Language Agnostic
# Usage: function-length-check.sh <source-path> [max-lines]
#
# Checks function/method lengths across common languages.
# Reports functions exceeding the maximum line count (default: 20).

SOURCE_PATH="${1:-.}"
MAX_LINES="${2:-20}"

echo "=== Function Length Check ==="
echo "Path: $SOURCE_PATH"
echo "Max allowed: $MAX_LINES lines"
echo ""

VIOLATIONS=0
TOTAL_FUNCTIONS=0

check_java_kotlin() {
    local file="$1"
    local in_function=0
    local func_name=""
    local func_start=0
    local brace_count=0
    local line_num=0

    while IFS= read -r line; do
        ((line_num++))

        if [[ $in_function -eq 0 ]]; then
            if echo "$line" | grep -qE '^\s*(public|private|protected|internal|override|open|abstract|static|final|synchronized|fun)\s+.*\{' ; then
                func_name=$(echo "$line" | sed -E 's/.*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*/\1/')
                func_start=$line_num
                in_function=1
                brace_count=1
            fi
        else
            local opens=$(echo "$line" | tr -cd '{' | wc -c)
            local closes=$(echo "$line" | tr -cd '}' | wc -c)
            brace_count=$((brace_count + opens - closes))

            if [[ $brace_count -le 0 ]]; then
                local func_length=$((line_num - func_start + 1))
                ((TOTAL_FUNCTIONS++))
                if [[ $func_length -gt $MAX_LINES ]]; then
                    echo "  WARN: $file:$func_start - $func_name() = $func_length lines (max: $MAX_LINES)"
                    ((VIOLATIONS++))
                fi
                in_function=0
            fi
        fi
    done < "$file"
}

check_python() {
    local file="$1"
    local func_name=""
    local func_start=0
    local func_indent=-1
    local line_num=0
    local last_content_line=0

    while IFS= read -r line; do
        ((line_num++))

        local current_indent=${#line}
        current_indent=$((current_indent - ${#line##*( )}))
        local trimmed="${line#"${line%%[![:space:]]*}"}"

        if echo "$trimmed" | grep -qE '^def\s+[a-zA-Z_]'; then
            if [[ $func_indent -ge 0 ]]; then
                local func_length=$((last_content_line - func_start + 1))
                ((TOTAL_FUNCTIONS++))
                if [[ $func_length -gt $MAX_LINES ]]; then
                    echo "  WARN: $file:$func_start - $func_name() = $func_length lines (max: $MAX_LINES)"
                    ((VIOLATIONS++))
                fi
            fi
            func_name=$(echo "$trimmed" | sed -E 's/def\s+([a-zA-Z_][a-zA-Z0-9_]*).*/\1/')
            func_start=$line_num
            func_indent=$current_indent
        fi

        if [[ -n "$trimmed" && ! "$trimmed" =~ ^# ]]; then
            last_content_line=$line_num
        fi
    done < "$file"

    if [[ $func_indent -ge 0 ]]; then
        local func_length=$((last_content_line - func_start + 1))
        ((TOTAL_FUNCTIONS++))
        if [[ $func_length -gt $MAX_LINES ]]; then
            echo "  WARN: $file:$func_start - $func_name() = $func_length lines (max: $MAX_LINES)"
            ((VIOLATIONS++))
        fi
    fi
}

check_ts_js() {
    local file="$1"
    local in_function=0
    local func_name=""
    local func_start=0
    local brace_count=0
    local line_num=0

    while IFS= read -r line; do
        ((line_num++))

        if [[ $in_function -eq 0 ]]; then
            if echo "$line" | grep -qE '(function\s+[a-zA-Z_]|=>\s*\{|(async\s+)?[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*\)\s*(:\s*\w+)?\s*\{)'; then
                func_name=$(echo "$line" | grep -oE '[a-zA-Z_][a-zA-Z0-9_]*\s*\(' | head -1 | sed 's/\s*($//')
                func_start=$line_num
                in_function=1
                brace_count=$(echo "$line" | tr -cd '{' | wc -c)
                brace_count=$((brace_count - $(echo "$line" | tr -cd '}' | wc -c)))
                if [[ $brace_count -le 0 ]]; then
                    in_function=0
                fi
            fi
        else
            local opens=$(echo "$line" | tr -cd '{' | wc -c)
            local closes=$(echo "$line" | tr -cd '}' | wc -c)
            brace_count=$((brace_count + opens - closes))

            if [[ $brace_count -le 0 ]]; then
                local func_length=$((line_num - func_start + 1))
                ((TOTAL_FUNCTIONS++))
                if [[ $func_length -gt $MAX_LINES ]]; then
                    echo "  WARN: $file:$func_start - ${func_name:-anonymous}() = $func_length lines (max: $MAX_LINES)"
                    ((VIOLATIONS++))
                fi
                in_function=0
            fi
        fi
    done < "$file"
}

# Find and check files
while IFS= read -r file; do
    case "$file" in
        *.java|*.kt)
            check_java_kotlin "$file"
            ;;
        *.py)
            check_python "$file"
            ;;
        *.ts|*.tsx|*.js|*.jsx)
            check_ts_js "$file"
            ;;
    esac
done < <(find "$SOURCE_PATH" -type f \( -name "*.java" -o -name "*.kt" -o -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) ! -path "*/node_modules/*" ! -path "*/target/*" ! -path "*/.git/*" ! -path "*/build/*" ! -path "*/dist/*" ! -path "*/__pycache__/*")

echo ""
echo "=== Summary ==="
echo "Functions checked: $TOTAL_FUNCTIONS"
echo "Violations (>$MAX_LINES lines): $VIOLATIONS"

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "STATUS: WARN - $VIOLATIONS function(s) exceed $MAX_LINES lines"
    exit 1
else
    echo "STATUS: OK - All functions within limit"
    exit 0
fi
