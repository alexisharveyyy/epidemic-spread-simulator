"""Single shared `Jinja2Templates` instance.

Both `main.py` (for the home page) and `routers/pages.py` (for the
remaining template pages) import from this module so the same
template environment, cache, and globals are used everywhere.
"""

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
