import json
from pathlib import Path

from bluenumbers.models import AdType, AssignedUUID, CompanyIdentifier

ad_types: dict[int, AdType] = {
    int(k): v
    for k, v in json.loads(
        (Path(__file__).parent / "resources" / "ad_types.json").read_text()
    ).items()
}

company_identifiers: dict[int, CompanyIdentifier] = {
    int(k): v
    for k, v in json.loads(
        (Path(__file__).parent / "resources" / "company_identifiers.json").read_text()
    ).items()
}

uuids: dict[int, AssignedUUID] = {
    int(k): v
    for k, v in json.loads((Path(__file__).parent / "resources" / "uuids.json").read_text()).items()
}
