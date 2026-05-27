from webui.studio import bootstrap, theme
from webui.studio.navigation import render_studio_app


bootstrap.boot()
theme.apply_theme()
render_studio_app()

