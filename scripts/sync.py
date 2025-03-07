# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "bluenumbers",
#     "pyyaml",
# ]
#
# [tool.uv.sources]
# bluenumbers = { path = "../" }
# ///

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import yaml

from bluenumbers.models import AdType, AssignedUUID, CompanyIdentifier

# Fail early if git is not installed on module import
try:
    subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except (subprocess.SubprocessError, FileNotFoundError):
    raise RuntimeError("Git is not installed. Please install git first.")


REPO_URL: str = "https://bitbucket.org/bluetooth-SIG/public.git"
REPO_DIR: Path = Path("./.bluetooth_sig_public")


def sync_data(repo_url: str = REPO_URL) -> str:
    if REPO_DIR.exists():
        try:
            subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)
            logging.info(f"Pulled repository in {REPO_DIR}")
        except subprocess.CalledProcessError:
            logging.warning("Git pull failed. Fallback to current commit.")
    else:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, REPO_DIR], check=True)
        logging.info(f"Cloned repository to {REPO_DIR}")
    commit_hash = subprocess.run(
        ["git", "-C", REPO_DIR, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return commit_hash


def get_company_identifiers() -> dict[int, CompanyIdentifier]:
    company_identifier_file = (
        REPO_DIR / "assigned_numbers" / "company_identifiers" / "company_identifiers.yaml"
    )
    if not company_identifier_file.exists():
        sync_data()
    company_identifier_list: list[dict[str, Any]] = yaml.safe_load(
        company_identifier_file.read_text()
    )["company_identifiers"]
    return {ci["value"]: CompanyIdentifier(**ci) for ci in company_identifier_list}


def get_uuids() -> dict[int, AssignedUUID]:
    result = {}
    uuid_dir = REPO_DIR / "assigned_numbers" / "uuids"
    if not uuid_dir.exists():
        sync_data()
    for uuid_file in uuid_dir.glob("*.yaml"):
        uuid_list = yaml.safe_load(uuid_file.read_text())["uuids"]
        result |= {
            uuid["uuid"]: AssignedUUID(
                short_uuid=uuid["uuid"],
                name=uuid["name"],
                id=uuid.get("id"),
                category=uuid_file.stem,
            )
            for uuid in uuid_list
        }
    return result


def get_ad_types() -> dict[int, AdType]:
    ad_types_file = REPO_DIR / "assigned_numbers" / "core" / "ad_types.yaml"
    if not ad_types_file.exists():
        sync_data()
    ad_type_list = yaml.safe_load(ad_types_file.read_text())["ad_types"]
    return {t["value"]: AdType(**t) for t in ad_type_list}


if __name__ == "__main__":
    company_identifiers = get_company_identifiers()
    uuids = get_uuids()
    ad_types = get_ad_types()

    # write to files
    resources = Path("src/bluenumbers/resources")
    (resources / "company_identifiers.json").write_text(json.dumps(company_identifiers, indent=2))
    (resources / "uuids.json").write_text(json.dumps(uuids, indent=2))
    (resources / "ad_types.json").write_text(json.dumps(ad_types, indent=2))
