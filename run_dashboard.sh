#!/bin/bash
# ──────────────────────────────────────────────────────
# Insurance AI Pipeline — Dashboard Launcher
# ──────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  🏛️  Insurance AI Pipeline — Dashboard"
echo "  ────────────────────────────────────────"
echo ""

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "  ✅ Virtual environment activated"
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "  ✅ Virtual environment activated"
fi

# Check dependencies
if ! python -c "import streamlit" 2>/dev/null; then
    echo "  ⚠️  Streamlit not found. Installing..."
    pip install streamlit plotly pandas
fi

echo "  🚀 Launching dashboard at http://localhost:8501"
echo ""

streamlit run ui/app.py \
    --server.headless true \
    --browser.gatherUsageStats false \
    --theme.primaryColor "#6366F1" \
    --theme.backgroundColor "#0F172A" \
    --theme.secondaryBackgroundColor "#1E293B" \
    --theme.textColor "#F8FAFC"
