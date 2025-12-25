sample_code = """\
import json
from pathlib import Path

# Dummy experiment logic
accuracy = 0.85

outputs_dir = Path("outputs")
outputs_dir.mkdir(exist_ok=True)

with open(outputs_dir / "metrics.json", "w") as f:
    json.dump({"accuracy": accuracy}, f)
"""