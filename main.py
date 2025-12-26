"""Entry point for the Discord bot."""
import sys
from pathlib import Path

# Reconfigure stdout encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from bot import run_bot

if __name__ == "__main__":
    run_bot()
