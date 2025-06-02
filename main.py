"""Entry point – launches the game selector."""
import pathlib, sys
from ui.launcher import launch_selector

BASE = pathlib.Path(__file__).parent
DATA_DIR = BASE / "data"
GAMES_DIR = DATA_DIR / "games"
IMAGES_DIR = DATA_DIR / "images"
for d in (DATA_DIR, GAMES_DIR, IMAGES_DIR):
    d.mkdir(exist_ok=True)

if __name__ == "__main__":
    sys.exit(launch_selector(GAMES_DIR, IMAGES_DIR))
