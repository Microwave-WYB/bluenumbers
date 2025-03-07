from typing import Final, NotRequired, TypedDict
from uuid import UUID


class CompanyIdentifier(TypedDict):
    value: int
    name: str


class AdType(TypedDict):
    value: int
    name: str
    reference: str


BLUETOOTH_SIG_UUID_BASE: Final[UUID] = UUID("00000000-0000-1000-8000-00805F9B34FB")


def get_full_uuid(short_uuid: int) -> UUID:
    base_bytes = BLUETOOTH_SIG_UUID_BASE.bytes
    short_bytes = short_uuid.to_bytes(2, "little")
    return UUID(bytes=base_bytes[:12] + short_bytes + base_bytes[14:])


class AssignedUUID(TypedDict):
    short_uuid: int
    name: str
    id: NotRequired[str]
    category: str
