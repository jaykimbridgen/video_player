"""``python -m video_player`` 진입점."""

from __future__ import annotations

import sys

from video_player.cli import main

if __name__ == "__main__":
    sys.exit(main())
