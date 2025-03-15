import logging
import subprocess
from pathlib import Path
from typing import Any, Final
from uuid import UUID

import yaml

from bluenumbers.models import AdTypeInfo, AssignedUUID, CompanyIdentifier

REPO_URL: Final[str] = "https://bitbucket.org/bluetooth-SIG/public.git"

BLUETOOTH_SIG_UUID_BASE: Final[UUID] = UUID("00000000-0000-1000-8000-00805F9B34FB")


def get_full_uuid(short_uuid: int) -> UUID:
    """Get the full 128-bit UUID from a 16-bit UUID."""
    base_bytes = BLUETOOTH_SIG_UUID_BASE.bytes
    short_bytes = short_uuid.to_bytes(2, "little")
    return UUID(bytes=base_bytes[:12] + short_bytes + base_bytes[14:])


# Change to use a directory within the package's resources
def get_repo_dir() -> Path:
    """Get path to the Bluetooth SIG repository directory within the package."""
    return Path(__file__).parent / "resources" / "bluetooth_sig_public"


def ensure_repo_exists() -> str:
    """Ensure the Bluetooth SIG repository exists, clone it if it doesn't."""
    repo_dir = get_repo_dir()

    # Fail early if git is not installed
    try:
        subprocess.run(
            ["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        raise RuntimeError("Git is not installed. Please install git first.")

    if repo_dir.exists():
        # Repository already exists, do nothing
        logging.debug(f"Repository already exists at {repo_dir}")
    else:
        # Ensure parent directory exists
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, repo_dir], check=True)
        logging.info(f"Cloned repository to {repo_dir}")

    commit_hash = subprocess.run(
        ["git", "-C", repo_dir, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return commit_hash


def update() -> bool:
    """Update the Bluetooth SIG repository and return True if updated, False if already up-to-date."""
    repo_dir = get_repo_dir()

    # Check if repository exists, create it if not
    if not repo_dir.exists():
        ensure_repo_exists()
        return True

    # Get the current commit hash before pulling
    before_hash = subprocess.run(
        ["git", "-C", repo_dir, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Pull the latest changes
    subprocess.run(["git", "-C", repo_dir, "pull"], check=True)

    # Get the commit hash after pulling
    after_hash = subprocess.run(
        ["git", "-C", repo_dir, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Compare hashes to determine if there was an update
    updated = before_hash != after_hash

    if updated:
        global ad_types, company_identifiers, uuids
        ad_types = get_ad_types()
        company_identifiers = get_company_identifiers()
        uuids = get_uuids()
        logging.info(f"Repository updated in {repo_dir}")
    else:
        logging.debug(f"Repository already up-to-date in {repo_dir}")

    return updated


def get_company_identifiers() -> dict[int, CompanyIdentifier]:
    """Get company identifiers directly from the cloned repository."""
    repo_dir = get_repo_dir()
    company_identifier_file = (
        repo_dir / "assigned_numbers" / "company_identifiers" / "company_identifiers.yaml"
    )
    if not company_identifier_file.exists():
        ensure_repo_exists()

    company_identifier_list: list[dict[str, Any]] = yaml.safe_load(
        company_identifier_file.read_text()
    )["company_identifiers"]
    return {ci["value"]: CompanyIdentifier(**ci) for ci in company_identifier_list}


def get_uuids() -> dict[int, AssignedUUID]:
    """Get UUIDs directly from the cloned repository."""
    result = {}
    repo_dir = get_repo_dir()
    uuid_dir = repo_dir / "assigned_numbers" / "uuids"
    if not uuid_dir.exists():
        ensure_repo_exists()

    for uuid_file in uuid_dir.glob("*.yaml"):
        uuid_list = yaml.safe_load(uuid_file.read_text())["uuids"]
        result |= {
            uuid["uuid"]: AssignedUUID(
                short_uuid=uuid["uuid"],
                full_uuid=get_full_uuid(uuid["uuid"]),
                name=uuid["name"],
                id=uuid.get("id"),
                category=uuid_file.stem,
            )
            for uuid in uuid_list
        }
    return result


def get_ad_types() -> dict[int, AdTypeInfo]:
    """Get advertisement types directly from the cloned repository."""
    repo_dir = get_repo_dir()
    ad_types_file = repo_dir / "assigned_numbers" / "core" / "ad_types.yaml"
    if not ad_types_file.exists():
        ensure_repo_exists()

    ad_type_list = yaml.safe_load(ad_types_file.read_text())["ad_types"]
    return {t["value"]: AdTypeInfo(**t) for t in ad_type_list}


ad_types: dict[int, AdTypeInfo] = get_ad_types()
company_identifiers: dict[int, CompanyIdentifier] = get_company_identifiers()
uuids: dict[int, AssignedUUID] = get_uuids()
