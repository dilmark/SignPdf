#!/usr/bin/env bash

ROOT="$(pwd)"
OUT="exported_code.txt"

echo "===== STRUKTURA PROJEKTU =====" > "$OUT"

# --- STRUKTURA (jak tree) ---
find . \
    \( -path './.git' -o -path './.venv' -o -path './.vscode' \) -prune -o \
    \( \
        -type d -o \
        -type f \( \
            -name '*.py' -o \
            -name 'magazyn.db' -o \
            -path './utils/*' \
        \) \
    \) -print \
| sed 's|^\./||' \
| sort \
| awk -F/ '
{
    indent=""
    for (i=1; i<NF; i++) indent=indent "│   "
    print indent "├── " $NF
}
' >> "$OUT"

echo -e "\n\n===== ZAWARTOŚĆ PLIKÓW =====" >> "$OUT"

# --- TREŚĆ PLIKÓW ---
find . \
    \( -path './.git' -o -path './.venv' -o -path './.vscode' \) -prune -o \
    -type f \( \
        -name '*.py' -o \
        -name 'app_config.json' \
    \) -print \
| sort \
| while read -r file; do
    echo -e "\n# =======================================" >> "$OUT"
    echo "# FILE: ${file#./}" >> "$OUT"
    echo "# =======================================" >> "$OUT"

    sed -E '
        /^[[:space:]]*$/d
        /^[[:space:]]*#[^=]/d
    ' "$file" >> "$OUT"
done

echo "✔ Kod wyeksportowany do: $OUT"
