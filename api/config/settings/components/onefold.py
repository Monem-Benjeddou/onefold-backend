"""
Settings for the Onefold learning platform apps (learning, projects, verification).
"""

import os
from pathlib import Path

# Content-as-code root; contains a `paths/` directory. See content/README.md.
LEARNING_CONTENT_DIR = Path(
    os.getenv("LEARNING_CONTENT_DIR", Path(__file__).resolve().parents[4] / "content")
)

# The path new builders are enrolled in.
LEARNING_DEFAULT_PATH = os.getenv("LEARNING_DEFAULT_PATH", "ship-your-first-product")

# "Check my work" requests allowed per builder per minute.
VERIFICATION_CHECKS_PER_MINUTE = int(os.getenv("VERIFICATION_CHECKS_PER_MINUTE", "10"))
