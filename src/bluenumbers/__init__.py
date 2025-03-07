import logging

from bluenumbers.bluetooth_sig_loader import ad_types, company_identifiers, update, uuids
from bluenumbers.models import AdType, AssignedUUID, CompanyIdentifier

logging.basicConfig(level=logging.INFO)


def _check_repo_init():
    from bluenumbers.bluetooth_sig_loader import ensure_repo_exists, get_repo_dir

    repo_dir = get_repo_dir()
    if not repo_dir.exists():
        logging.info("Bluetooth SIG repository not found. Initializing on first import...")
        try:
            ensure_repo_exists()
            logging.info("Bluetooth SIG repository initialized successfully.")
        except Exception as e:
            logging.warning(f"Failed to initialize Bluetooth SIG repository: {e}")
            logging.warning(
                "Some functions may not work correctly. Run bluenumbers.bluetooth_sig_loader.ensure_repo_exists() manually."
            )


_check_repo_init()


__all__ = [
    "ad_types",
    "company_identifiers",
    "uuids",
    "AssignedUUID",
    "CompanyIdentifier",
    "AdType",
    "update",
]
