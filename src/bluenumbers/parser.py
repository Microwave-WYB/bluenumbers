import base64
from collections.abc import Iterator
from enum import IntEnum, IntFlag
from typing import Literal, cast
from uuid import UUID

from pydantic import BaseModel, ValidationError, computed_field, field_serializer, field_validator

import bluenumbers


class AdType(IntEnum):
    FLAGS = 0x01
    INCOMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS = 0x02
    COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS = 0x03
    INCOMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS = 0x04
    COMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS = 0x05
    INCOMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS = 0x06
    COMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS = 0x07
    SHORTENED_LOCAL_NAME = 0x08
    COMPLETE_LOCAL_NAME = 0x09
    TX_POWER_LEVEL = 0x0A
    CLASS_OF_DEVICE = 0x0D
    SIMPLE_PAIRING_HASH_C_192 = 0x0E
    SIMPLE_PAIRING_RANDOMIZER_R_192 = 0x0F
    DEVICE_ID = 0x10
    SECURITY_MANAGER_TK_VALUE = 0x10
    SECURITY_MANAGER_OUT_OF_BAND_FLAGS = 0x11
    PERIPHERAL_CONNECTION_INTERVAL_RANGE = 0x12
    LIST_OF_16_BIT_SERVICE_SOLICITATION_UUIDS = 0x14
    LIST_OF_128_BIT_SERVICE_SOLICITATION_UUIDS = 0x15
    SERVICE_DATA_16_BIT_UUID = 0x16
    PUBLIC_TARGET_ADDRESS = 0x17
    RANDOM_TARGET_ADDRESS = 0x18
    APPEARANCE = 0x19
    ADVERTISING_INTERVAL = 0x1A
    LE_BLUETOOTH_DEVICE_ADDRESS = 0x1B
    LE_ROLE = 0x1C
    SIMPLE_PAIRING_HASH_C_256 = 0x1D
    SIMPLE_PAIRING_RANDOMIZER_R_256 = 0x1E
    LIST_OF_32_BIT_SERVICE_SOLICITATION_UUIDS = 0x1F
    SERVICE_DATA_32_BIT_UUID = 0x20
    SERVICE_DATA_128_BIT_UUID = 0x21
    LE_SECURE_CONNECTIONS_CONFIRMATION_VALUE = 0x22
    LE_SECURE_CONNECTIONS_RANDOM_VALUE = 0x23
    URI = 0x24
    INDOOR_POSITIONING = 0x25
    TRANSPORT_DISCOVERY_DATA = 0x26
    LE_SUPPORTED_FEATURES = 0x27
    CHANNEL_MAP_UPDATE_INDICATION = 0x28
    PB_ADV = 0x29
    MESH_MESSAGE = 0x2A
    MESH_BEACON = 0x2B
    BIGINFO = 0x2C
    BROADCAST_CODE = 0x2D
    RESOLVABLE_SET_IDENTIFIER = 0x2E
    ADVERTISING_INTERVAL_LONG = 0x2F
    BROADCAST_NAME = 0x30
    ENCRYPTED_ADVERTISING_DATA = 0x31
    PERIODIC_ADVERTISING_RESPONSE_TIMING_INFORMATION = 0x32
    ELECTRONIC_SHELF_LABEL = 0x34
    _3D_INFORMATION_DATA = 0x3D
    MANUFACTURER_SPECIFIC_DATA = 0xFF


class Flags(IntFlag):
    LE_LIMITED_DISCOVERABLE_MODE = 0b00000001
    LE_GENERAL_DISCOVERABLE_MODE = 0b00000010
    BR_EDR_NOT_SUPPORTED = 0b00000100
    SIMULTANEOUS_LE_AND_BR_EDR_TO_SAME_DEVICE_CAPABLE_CONTROLLER = 0b00001000
    SIMULTANEOUS_LE_AND_BR_EDR_TO_SAME_DEVICE_CAPABLE_HOST = 0b00010000


def get_full_uuid(short_uuid: int, bit_length: int) -> UUID:
    """
    >>> get_full_uuid(0xaaaa, 16)
    UUID('0000aaaa-0000-1000-8000-00805f9b34fb')
    >>> get_full_uuid(0xaaaaaaaa, 32)
    UUID('aaaaaaaa-0000-1000-8000-00805f9b34fb')
    """
    base_uuid = "00000000-0000-1000-8000-00805F9B34FB"
    match bit_length:
        case 16:
            return UUID(f"{base_uuid[:4]}{short_uuid:04X}-{base_uuid[9:]}")
        case 32:
            return UUID(f"{short_uuid:08X}-{base_uuid[8:]}")
        case 128:
            return UUID(int=short_uuid)
        case _:
            raise ValueError("Invalid bit length. Must be 16, 32, or 128.")


def decode_flags(value: bytes) -> Flags:
    return Flags(int.from_bytes(value, "little"))


def decode_uuid_list(
    ad_type: Literal[
        AdType.INCOMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
        AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
        AdType.INCOMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
        AdType.COMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
        AdType.INCOMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
        AdType.COMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
        AdType.LIST_OF_16_BIT_SERVICE_SOLICITATION_UUIDS,
        AdType.LIST_OF_32_BIT_SERVICE_SOLICITATION_UUIDS,
        AdType.LIST_OF_128_BIT_SERVICE_SOLICITATION_UUIDS,
    ],
    value: bytes,
) -> list[str]:
    uuids = []
    uuid_length = {
        AdType.INCOMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS: 16,
        AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS: 16,
        AdType.INCOMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS: 32,
        AdType.COMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS: 32,
        AdType.INCOMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS: 128,
        AdType.COMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS: 128,
        AdType.LIST_OF_16_BIT_SERVICE_SOLICITATION_UUIDS: 16,
        AdType.LIST_OF_32_BIT_SERVICE_SOLICITATION_UUIDS: 32,
        AdType.LIST_OF_128_BIT_SERVICE_SOLICITATION_UUIDS: 128,
    }[ad_type]
    for i in range(0, len(value), uuid_length // 8):
        uuid = int.from_bytes(value[i : i + uuid_length // 8], "little")
        uuids.append(str(get_full_uuid(uuid, uuid_length)))
    return uuids


class ServiceData(BaseModel):
    uuid: str
    data: bytes

    @field_serializer("data")
    def serialize_data(self, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    @field_validator("data", mode="before")
    def validate_data(cls, data: bytes | str) -> bytes:
        match data:
            case str(v):
                return base64.b64decode(v)
            case bytes(v):
                return v
            case _:
                raise ValidationError("data must be a string or bytes")


def decode_service_data(
    ad_type: Literal[
        AdType.SERVICE_DATA_16_BIT_UUID,
        AdType.SERVICE_DATA_32_BIT_UUID,
        AdType.SERVICE_DATA_128_BIT_UUID,
    ],
    value: bytes,
) -> ServiceData:
    uuid_length = {
        AdType.SERVICE_DATA_16_BIT_UUID: 16,
        AdType.SERVICE_DATA_32_BIT_UUID: 32,
        AdType.SERVICE_DATA_128_BIT_UUID: 128,
    }[ad_type]
    uuid = get_full_uuid(int.from_bytes(value[: uuid_length // 8], "little"), uuid_length)
    data = value[uuid_length // 8 :]
    return ServiceData(uuid=str(uuid), data=data)


class ManufacturerData(BaseModel):
    company_identifier: int
    data: bytes

    @computed_field
    def company_name(self) -> str | None:
        return bluenumbers.company_identifiers.get(self.company_identifier, {}).get("name")

    @field_serializer("data")
    def serialize_data(self, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    @field_validator("data", mode="before")
    def validate_data(cls, data: bytes | str) -> bytes:
        match data:
            case str(v):
                return base64.b64decode(v)
            case bytes(v):
                return v
            case _:
                raise ValidationError("data must be a string or bytes")


def decode_manufacturer_data(value: bytes) -> ManufacturerData:
    company_identifier = int.from_bytes(value[:2], "little")
    data = value[2:]
    return ManufacturerData(company_identifier=company_identifier, data=data)


def decode_str(value: bytes) -> str:
    return value.decode("utf-8")


type DecodedAdValue = Flags | list[str] | ServiceData | ManufacturerData | str


def decode_ad_struct(ad_type: AdType | int, value: bytes) -> DecodedAdValue | None:
    if ad_type not in AdType:
        return None
    ad_type = AdType(ad_type)
    match ad_type:
        case AdType.FLAGS:
            return decode_flags(value)
        case (
            AdType.INCOMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS
            | AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS
            | AdType.INCOMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS
            | AdType.COMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS
            | AdType.INCOMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS
            | AdType.COMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS
            | AdType.LIST_OF_16_BIT_SERVICE_SOLICITATION_UUIDS
            | AdType.LIST_OF_32_BIT_SERVICE_SOLICITATION_UUIDS
            | AdType.LIST_OF_128_BIT_SERVICE_SOLICITATION_UUIDS
        ):
            return decode_uuid_list(ad_type, value)
        case (
            AdType.SERVICE_DATA_16_BIT_UUID
            | AdType.SERVICE_DATA_32_BIT_UUID
            | AdType.SERVICE_DATA_128_BIT_UUID
        ):
            return decode_service_data(ad_type, value)
        case AdType.MANUFACTURER_SPECIFIC_DATA:
            return decode_manufacturer_data(value)
        case AdType.SHORTENED_LOCAL_NAME, AdType.COMPLETE_LOCAL_NAME, AdType.URI:
            return decode_str(value)
        case _:
            return None


class AdStruct(BaseModel):
    length: int
    ad_type: AdType | int
    value: bytes

    @computed_field
    def decoded(self) -> DecodedAdValue | None:
        return decode_ad_struct(self.ad_type, self.value)

    @computed_field
    def ad_type_name(self) -> str | None:
        try:
            return AdType(self.ad_type).name
        except ValueError:
            return None

    @field_serializer("value")
    def serialize_value(self, value: bytes) -> str:
        return base64.b64encode(value).decode("utf-8")

    @field_validator("value", mode="before")
    def validate_value(cls, value: bytes | str) -> bytes:
        match value:
            case str(v):
                return base64.b64decode(v)
            case bytes(v):
                return v
            case _:
                raise ValidationError("value must be a string or bytes")

    def __bytes__(self) -> bytes:
        return bytes([self.length, self.ad_type]) + self.value


class AdPacket(BaseModel):
    ad_structs: list[AdStruct]

    @classmethod
    def from_bytes(cls, data: bytes) -> "AdPacket":
        def iterate_ad_structures(data: bytes) -> Iterator["AdStruct"]:
            """
            Parse the first advertisement structure from the given data.
            """
            if not data:
                return

            length = data[0]
            if not length:
                return

            ad_type = data[1]
            value = data[2 : length + 1]
            yield AdStruct(length=length, ad_type=ad_type, value=value)
            yield from iterate_ad_structures(data[length + 1 :])

        return cls(ad_structs=list(iterate_ad_structures(data)))

    @property
    def uuids(self) -> list[UUID]:
        uuids: list[UUID] = []
        for ad_type in (
            AdType.INCOMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
            AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
            AdType.INCOMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
            AdType.COMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
            AdType.INCOMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
            AdType.COMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
            AdType.LIST_OF_16_BIT_SERVICE_SOLICITATION_UUIDS,
            AdType.LIST_OF_32_BIT_SERVICE_SOLICITATION_UUIDS,
            AdType.LIST_OF_128_BIT_SERVICE_SOLICITATION_UUIDS,
        ):
            for ad_struct in self.get_all(ad_type):
                uuids.extend([UUID(s) for s in cast(list[str], ad_struct.decoded)])
        for ad_type in (
            AdType.SERVICE_DATA_16_BIT_UUID,
            AdType.SERVICE_DATA_32_BIT_UUID,
            AdType.SERVICE_DATA_128_BIT_UUID,
        ):
            for ad_struct in self.get_all(ad_type):
                uuids.append(UUID(cast(ServiceData, ad_struct.decoded).uuid))
        return uuids

    @property
    def manufacturer_id(self) -> int | None:
        manufacturer_data_struct = self.get(AdType.MANUFACTURER_SPECIFIC_DATA)
        if not manufacturer_data_struct:
            return None
        return cast(ManufacturerData, manufacturer_data_struct.decoded).company_identifier

    @property
    def name(self) -> str | None:
        name_struct = self.get(AdType.COMPLETE_LOCAL_NAME) or self.get(AdType.SHORTENED_LOCAL_NAME)
        if not name_struct:
            return None
        return cast(str, name_struct.decoded)

    def get(self, ad_type: AdType) -> AdStruct | None:
        for ad_struct in self.ad_structs:
            if ad_struct.ad_type == ad_type:
                return ad_struct
        return None

    def get_all(self, ad_type: AdType) -> list[AdStruct]:
        return [ad_struct for ad_struct in self.ad_structs if ad_struct.ad_type == ad_type]

    def __bytes__(self) -> bytes:
        return b"".join(bytes(ad_struct) for ad_struct in self.ad_structs)
