import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from webui.studio import bootstrap, theme
from webui.studio.navigation import render_studio_app


bootstrap.boot()
theme.apply_theme()
render_studio_app()
