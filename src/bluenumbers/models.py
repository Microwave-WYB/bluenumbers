from typing import NotRequired, TypedDict
from uuid import UUID


class CompanyIdentifier(TypedDict):
    value: int
    name: str


class AdType(TypedDict):
    value: int
    name: str
    reference: str


class AssignedUUID(TypedDict):
    short_uuid: int
    full_uuid: UUID
    name: str
    id: NotRequired[str]
    category: str
