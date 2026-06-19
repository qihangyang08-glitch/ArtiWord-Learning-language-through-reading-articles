#!/bin/bash
echo "============================================"
echo "  Word-Lerning (English) - One-Click Install"
echo "============================================"
echo ""

# --- Check Python ---
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "[ERROR] Python not found. Please install Python 3.7+ first."
    exit 1
fi
echo "[OK] Python found"
python3 --version 2>/dev/null || python --version

# --- Detect version root ---
VERSION_ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "[INFO] Version root: $VERSION_ROOT"

# --- Find Claude Code user skills directory ---
USER_SKILLS="${HOME}/.claude/skills"
if [ ! -d "$USER_SKILLS" ]; then
    echo "[INFO] Creating user skills directory: $USER_SKILLS"
    mkdir -p "$USER_SKILLS"
fi

# --- Check language configuration ---
echo ""
echo "[CONFIG] Checking language configuration..."
SRC_SKILLS="${VERSION_ROOT}/.claude/skills"
if [ ! -f "${VERSION_ROOT}/config.json" ]; then
    echo "  [WARN] No config found. Running configure.py..."
    python3 "${VERSION_ROOT}/configure.py" || python "${VERSION_ROOT}/configure.py"
fi
if [ ! -f "${SRC_SKILLS}/init-wordlist.md" ]; then
    echo "  [WARN] Skill files not generated. Running configure.py..."
    python3 "${VERSION_ROOT}/configure.py" || python "${VERSION_ROOT}/configure.py"
fi
echo "  [OK] Skills ready"

# --- Copy skill files ---
echo ""
echo "[INSTALL] Copying skills to user directory..."

for skill in init-wordlist.md generate-article.md; do
    skill_name="${skill%.md}"
    if [ -f "${SRC_SKILLS}/${skill}" ]; then
        mkdir -p "${USER_SKILLS}/${skill_name}"
        cp "${SRC_SKILLS}/${skill}" "${USER_SKILLS}/${skill_name}/SKILL.md"
        echo "  [OK] ${skill_name}"
    else
        echo "  [FAIL] ${skill} not found"
    fi
done

# --- Create data directories ---
echo ""
echo "[INFO] Ensuring data directories exist..."
mkdir -p "${VERSION_ROOT}/data"
mkdir -p "${VERSION_ROOT}/articles"

# --- Make scripts executable ---
echo "[INFO] Setting script permissions..."
chmod +x "${VERSION_ROOT}/tools/extract-words.py" 2>/dev/null || true
chmod +x "${VERSION_ROOT}/tools/count-words.py" 2>/dev/null || true
chmod +x "${VERSION_ROOT}/tools/check-similarity.py" 2>/dev/null || true
chmod +x "${VERSION_ROOT}/serve.sh" 2>/dev/null || true

# --- Verify installation ---
echo ""
echo "============================================"
echo "  Verification"
echo "============================================"

ERRORS=0

for f in \
    tools/word-triage/index.html \
    tools/word-triage/regex-config.txt \
    tools/extract-words.py \
    tools/count-words.py \
    tools/check-similarity.py; do
    if [ -f "${VERSION_ROOT}/${f}" ]; then
        echo "[OK] ${f}"
    else
        echo "[FAIL] ${f} missing"
        ERRORS=$((ERRORS + 1))
    fi
done

for skill in init-wordlist generate-article; do
    if [ -f "${USER_SKILLS}/${skill}/SKILL.md" ]; then
        echo "[OK] User skill: ${skill}"
    else
        echo "[FAIL] User skill not installed: ${skill}"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "============================================"
    echo "  Installation SUCCESSFUL!"
    echo "============================================"
    echo ""
    echo "  Skills installed to: ${USER_SKILLS}"
    echo ""
    echo "  To start:"
    echo "    1. Run: bash serve.sh (from the en/ directory)"
    echo "    2. Open Claude Code and type: /init-wordlist"
    echo ""
else
    echo "============================================"
    echo "  Installation completed with ${ERRORS} warning(s)."
    echo "============================================"
fi
