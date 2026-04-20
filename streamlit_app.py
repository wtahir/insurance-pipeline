"""
Streamlit Cloud entrypoint.

Set this as the Main file path in Streamlit Cloud settings:
    streamlit_app.py
"""

import sys
import os

# Ensure the project root is on sys.path so all imports resolve
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Run ui/app.py via exec so Streamlit re-evaluates it on every
# rerun (avoids the module-cache blank-page issue with plain imports)
_app_path = os.path.join(_root, "ui", "app.py")
exec(open(_app_path).read())  # noqa: S102
