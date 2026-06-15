# MagDist — Magazine Distribution Kivy App (Demo)

This is a minimal Kivy app prototype for managing magazine distribution across zones, supervisors and users.

Run locally (desktop):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

To build for Android use Buildozer (Linux):

```bash
pip install buildozer
buildozer init
# edit buildozer.spec if needed, then
buildozer -v android debug
```

Notes:
- This is a starting scaffold. It includes SQLite models, a simple nearest-neighbour route generator, and a Kivy UI demo.
- Map visualization uses `kivy_garden.mapview` if installed. Some features (notifications, advanced routing, Belgian city structure) need further data and UX work.
