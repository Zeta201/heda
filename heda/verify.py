import hashlib
import json
from pathlib import Path
from datetime import datetime
import subprocess

from heda.check import ClaimCheckError, check_claims

class VerificationError(Exception):
    pass

def hash_files(path: Path) -> str:
    """Compute SHA-256 of all files under `path`, sorted by name."""
    sha = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if file.is_file():
            sha.update(file.read_bytes())
    return sha.hexdigest()

def verify_experiment() -> None:
    # 1. Run the experiment (build + run Docker)
    try:
        subprocess.run(["heda", "run"], check=True)
    except subprocess.CalledProcessError:
        raise VerificationError("Experiment execution failed")

    # 2. Check claims
    try:
        check_claims()
        claims_passed = True
    except ClaimCheckError:
        claims_passed = False

    # 3. Compute hashes
    input_hash = hash_files(Path("data"))  # or any input dir
    output_hash = hash_files(Path("outputs"))

    # 4. Build verification object
    verification = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_hash": input_hash,
        "output_hash": output_hash,
        "claims_passed": claims_passed,
    }

    # 5. Save verification.json
    verification_path = Path("verification.json")
    with open(verification_path, "w") as f:
        json.dump(verification, f, indent=2)

    print(f"✔ Verification saved: {verification_path.resolve()}")

    # 6. Exit non-zero if claims failed
    if not claims_passed:
        raise VerificationError("Some claims failed. See outputs/verification.json")
