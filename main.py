"""Application entry-point."""
import pathlib
from ui.main_window import run_app

BASE = pathlib.Path(__file__).parent
DATA_DIR = BASE / "data"
IMAGES_DIR = DATA_DIR / "images"
for d in (DATA_DIR, IMAGES_DIR):
    d.mkdir(exist_ok=True)

if __name__ == "__main__":
    run_app(DATA_DIR, IMAGES_DIR)
