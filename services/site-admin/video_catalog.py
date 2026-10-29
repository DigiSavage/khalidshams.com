"""Authored research and shooting plans, returned only after owner authorization.
No owner production records are seeded by loading this module.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
CATALOG = {**json.loads((ROOT / "video_research.json").read_text()),
           "playbook": json.loads((ROOT / "video_playbook.json").read_text()),
           "templates": json.loads((ROOT / "video_templates.json").read_text())}
