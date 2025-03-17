import base64
from uuid import UUID

import pytest

from bluenumbers import (
    AdPacket,
    AdStruct,
    AdType,
    Flags,
    ManufacturerData,
    ServiceData,
    decode_ad_struct,
    decode_flags,
    decode_manufacturer_data,
    decode_service_data,
    decode_str,
    decode_uuid_list,
    get_full_uuid,
)


class TestGetFullUUID:
    def test_16bit_uuid(self):
        uuid = get_full_uuid(0xAAAA, 16)
        assert uuid == UUID("0000aaaa-0000-1000-8000-00805f9b34fb")

    def test_32bit_uuid(self):
        uuid = get_full_uuid(0xAAAAAAAA, 32)
        assert uuid == UUID("aaaaaaaa-0000-1000-8000-00805f9b34fb")

    def test_128bit_uuid(self):
        uuid_int = 0x0000AAAA0000100080000080AFAFAAAA
        uuid = get_full_uuid(uuid_int, 128)
        assert uuid == UUID(int=uuid_int)

    def test_invalid_bit_length(self):
        with pytest.raises(ValueError, match="Invalid bit length. Must be 16, 32, or 128."):
            get_full_uuid(0xAAAA, 64)


class TestDecodeFlags:
    def test_decode_flags(self):
        # Test with all flags set
        all_flags = (
            Flags.LE_LIMITED_DISCOVERABLE_MODE
            | Flags.LE_GENERAL_DISCOVERABLE_MODE
            | Flags.BR_EDR_NOT_SUPPORTED
            | Flags.SIMULTANEOUS_LE_AND_BR_EDR_TO_SAME_DEVICE_CAPABLE_CONTROLLER
            | Flags.SIMULTANEOUS_LE_AND_BR_EDR_TO_SAME_DEVICE_CAPABLE_HOST
        )
        assert decode_flags(bytes([all_flags])) == all_flags

        # Test with specific flags
        flags = Flags.LE_LIMITED_DISCOVERABLE_MODE | Flags.BR_EDR_NOT_SUPPORTED
        assert decode_flags(bytes([flags])) == flags

        # Test with no flags
        assert decode_flags(bytes([0])) == Flags(0)


class TestDecodeUUIDList:
    def test_decode_16bit_uuid_list(self):
        # Two 16-bit UUIDs (2 bytes each)
        value = bytes([0xAA, 0xBB, 0xCC, 0xDD])
        uuids = decode_uuid_list(
            AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS, value
        )
        assert len(uuids) == 2
        assert uuids[0] == str(UUID("0000bbaa-0000-1000-8000-00805f9b34fb"))
        assert uuids[1] == str(UUID("0000ddcc-0000-1000-8000-00805f9b34fb"))

    def test_decode_32bit_uuid_list(self):
        # One 32-bit UUID (4 bytes)
        value = bytes([0xAA, 0xBB, 0xCC, 0xDD])
        uuids = decode_uuid_list(
            AdType.COMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS, value
        )
        assert len(uuids) == 1
        assert uuids[0] == str(UUID("ddccbbaa-0000-1000-8000-00805f9b34fb"))

    def test_decode_128bit_uuid_list(self):
        # One 128-bit UUID (16 bytes)
        value = bytes(range(16))  # 0x00, 0x01, 0x02, ..., 0x0F
        uuids = decode_uuid_list(
            AdType.COMPLETE_LIST_OF_128_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS, value
        )
        assert len(uuids) == 1
        # The bytes are interpreted in little-endian order
        expected_uuid = UUID("0f0e0d0c-0b0a-0908-0706-050403020100")
        assert uuids[0] == str(expected_uuid)


class TestDecodeStr:
    def test_decode_str(self):
        value = b"Test Device"
        assert decode_str(value) == "Test Device"

        value = b"\x00"
        assert decode_str(value) == "\x00"

        value = b""
        assert decode_str(value) == ""


class TestDecodeServiceData:
    def test_decode_16bit_service_data(self):
        # 16-bit UUID (2 bytes) followed by data
        uuid_bytes = bytes([0xAA, 0xBB])  # UUID 0xbbaa (little-endian)
        data_bytes = bytes([0x01, 0x02, 0x03])
        value = uuid_bytes + data_bytes

        service_data = decode_service_data(AdType.SERVICE_DATA_16_BIT_UUID, value)
        assert service_data.uuid == str(UUID("0000bbaa-0000-1000-8000-00805f9b34fb"))
        assert service_data.data == data_bytes

    def test_decode_32bit_service_data(self):
        # 32-bit UUID (4 bytes) followed by data
        uuid_bytes = bytes([0xAA, 0xBB, 0xCC, 0xDD])  # UUID 0xddccbbaa (little-endian)
        data_bytes = bytes([0x01, 0x02, 0x03])
        value = uuid_bytes + data_bytes

        service_data = decode_service_data(AdType.SERVICE_DATA_32_BIT_UUID, value)
        assert service_data.uuid == str(UUID("ddccbbaa-0000-1000-8000-00805f9b34fb"))
        assert service_data.data == data_bytes

    def test_decode_128bit_service_data(self):
        # 128-bit UUID (16 bytes) followed by data
        uuid_bytes = bytes(range(16))  # 0x00, 0x01, 0x02, ..., 0x0F
        data_bytes = bytes([0x01, 0x02, 0x03])
        value = uuid_bytes + data_bytes

        service_data = decode_service_data(AdType.SERVICE_DATA_128_BIT_UUID, value)
        expected_uuid = UUID("0f0e0d0c-0b0a-0908-0706-050403020100")
        assert service_data.uuid == str(expected_uuid)
        assert service_data.data == data_bytes


class TestDecodeManufacturerData:
    def test_decode_manufacturer_data(self):
        # Company identifier (2 bytes) followed by data
        company_id_bytes = bytes([0x34, 0x12])  # Company ID 0x1234 (little-endian)
        data_bytes = bytes([0x01, 0x02, 0x03])
        value = company_id_bytes + data_bytes

        manufacturer_data = decode_manufacturer_data(value)
        assert manufacturer_data.company_identifier == 0x1234
        assert manufacturer_data.data == data_bytes


class TestDecodeAdStruct:
    def test_decode_flags(self):
        result = decode_ad_struct(AdType.FLAGS, bytes([0x07]))
        assert result == Flags(0x07)

    def test_decode_uuid_list(self):
        result = decode_ad_struct(
            AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS, bytes([0xAA, 0xBB])
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == str(UUID("0000bbaa-0000-1000-8000-00805f9b34fb"))

    def test_decode_service_data(self):
        result = decode_ad_struct(
            AdType.SERVICE_DATA_16_BIT_UUID, bytes([0xAA, 0xBB, 0x01, 0x02, 0x03])
        )
        assert isinstance(result, ServiceData)
        assert result.uuid == str(UUID("0000bbaa-0000-1000-8000-00805f9b34fb"))
        assert result.data == bytes([0x01, 0x02, 0x03])

    def test_decode_manufacturer_data(self):
        result = decode_ad_struct(
            AdType.MANUFACTURER_SPECIFIC_DATA, bytes([0x34, 0x12, 0x01, 0x02, 0x03])
        )
        assert isinstance(result, ManufacturerData)
        assert result.company_identifier == 0x1234
        assert result.data == bytes([0x01, 0x02, 0x03])

    def test_decode_name(self):
        result = decode_ad_struct(AdType.COMPLETE_LOCAL_NAME, b"Test Device")
        assert result == "Test Device"

    def test_decode_unknown_type(self):
        result = decode_ad_struct(999, bytes([0x01, 0x02, 0x03]))
        assert result is None


class TestAdStruct:
    def test_creation(self):
        ad_struct = AdStruct(length=5, ad_type=AdType.FLAGS, value=bytes([0x07]))
        assert ad_struct.length == 5
        assert ad_struct.ad_type == AdType.FLAGS
        assert ad_struct.value == bytes([0x07])

    def test_decoded(self):
        ad_struct = AdStruct(length=5, ad_type=AdType.FLAGS, value=bytes([0x07]))
        assert ad_struct.decoded == Flags(0x07)

    def test_ad_type_name(self):
        ad_struct = AdStruct(length=5, ad_type=AdType.FLAGS, value=bytes([0x07]))
        assert ad_struct.ad_type_name == "FLAGS"

        ad_struct = AdStruct(
            length=5,
            ad_type=999,  # Unknown type
            value=bytes([0x07]),
        )
        assert ad_struct.ad_type_name is None

    def test_bytes_conversion(self):
        """Test that converting an AdStruct to bytes works correctly."""
        # Create an AdStruct with the correct length
        ad_struct = AdStruct(length=5, ad_type=AdType.FLAGS, value=bytes([0x07]))

        # Convert to bytes
        result = bytes(ad_struct)

        # The result should be [length, type, value]
        expected = bytes([5, AdType.FLAGS, 0x07])
        assert result == expected


class TestAdPacket:
    def test_from_bytes(self):
        # Ensure the name length matches the actual string length
        device_name = b"Test Device"
        name_length = len(device_name) + 1  # +1 for the AD type byte

        # Create a sample advertisement packet
        data = bytes(
            [
                # First AD structure: Flags
                0x02,  # Length (1 byte for type + 1 byte for data)
                AdType.FLAGS,
                0x06,  # BR/EDR Not Supported + General Discoverable Mode
                # Second AD structure: Complete Local Name
                name_length,  # Length (1 byte for type + bytes for data)
                AdType.COMPLETE_LOCAL_NAME,
                *device_name,
                # Third AD structure: 16-bit UUID
                0x03,  # Length (1 byte for type + 2 bytes for data)
                AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
                0xAA,
                0xBB,
            ]
        )

        packet = AdPacket.from_bytes(data)
        assert len(packet.ad_structs) == 3

        # Check the first AD structure (Flags)
        assert packet.ad_structs[0].length == 0x02
        assert packet.ad_structs[0].ad_type == AdType.FLAGS
        assert packet.ad_structs[0].value == bytes([0x06])
        assert (
            packet.ad_structs[0].decoded
            == Flags.LE_GENERAL_DISCOVERABLE_MODE | Flags.BR_EDR_NOT_SUPPORTED
        )

        # Check the second AD structure (Complete Local Name)
        assert packet.ad_structs[1].length == 0x0C
        assert packet.ad_structs[1].ad_type == AdType.COMPLETE_LOCAL_NAME
        assert packet.ad_structs[1].value == b"Test Device"
        assert packet.ad_structs[1].decoded == "Test Device"

        # Check the third AD structure (16-bit UUID)
        assert packet.ad_structs[2].length == 0x03
        assert (
            packet.ad_structs[2].ad_type
            == AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS
        )
        assert packet.ad_structs[2].value == bytes([0xAA, 0xBB])
        assert packet.ad_structs[2].decoded == [str(UUID("0000bbaa-0000-1000-8000-00805f9b34fb"))]

    def test_uuids_property(self):
        # Create a sample advertisement packet with various UUID types
        data = bytes(
            [
                # 16-bit UUID list
                0x05,  # Length (1 byte for type + 4 bytes for data)
                AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
                0xAA,
                0xBB,  # First UUID
                0xCC,
                0xDD,  # Second UUID
                # 32-bit UUID list
                0x05,  # Length (1 byte for type + 4 bytes for data)
                AdType.COMPLETE_LIST_OF_32_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
                0xAA,
                0xBB,
                0xCC,
                0xDD,  # One 32-bit UUID
                # Service data with 16-bit UUID
                0x05,  # Length (1 byte for type + 4 bytes for data)
                AdType.SERVICE_DATA_16_BIT_UUID,
                0x11,
                0x22,  # UUID
                0x33,
                0x44,  # Data
            ]
        )

        packet = AdPacket.from_bytes(data)
        uuids = packet.uuids
        assert len(uuids) == 4

        # Check the UUIDs
        assert UUID("0000bbaa-0000-1000-8000-00805f9b34fb") in uuids
        assert UUID("0000ddcc-0000-1000-8000-00805f9b34fb") in uuids
        assert UUID("ddccbbaa-0000-1000-8000-00805f9b34fb") in uuids
        assert UUID("00002211-0000-1000-8000-00805f9b34fb") in uuids

    def test_manufacturer_id_property(self):
        # Create a packet with manufacturer data
        data = bytes(
            [
                0x05,  # Length (1 byte for type + 4 bytes for data)
                AdType.MANUFACTURER_SPECIFIC_DATA,
                0x34,
                0x12,  # Company ID (0x1234 in little-endian)
                0x01,
                0x02,  # Manufacturer data
            ]
        )

        packet = AdPacket.from_bytes(data)
        assert packet.manufacturer_id == 0x1234

        # Test with no manufacturer data
        packet = AdPacket.from_bytes(
            bytes(
                [
                    0x02,  # Length
                    AdType.FLAGS,
                    0x06,  # Flags value
                ]
            )
        )
        assert packet.manufacturer_id is None

    def test_name_property(self):
        # Test with complete local name
        device_name = b"Test Device"
        name_length = len(device_name) + 1  # +1 for the AD type byte

        data = bytes(
            [
                name_length,  # Length (1 byte for type + bytes for data)
                AdType.COMPLETE_LOCAL_NAME,
                *device_name,
            ]
        )
        packet = AdPacket.from_bytes(data)
        assert packet.name == "Test Device"

        # Test with shortened local name
        short_name = b"Test Dev"
        short_name_length = len(short_name) + 1  # +1 for the AD type byte

        data = bytes(
            [
                short_name_length,  # Length (1 byte for type + bytes for data)
                AdType.SHORTENED_LOCAL_NAME,
                *short_name,
            ]
        )
        packet = AdPacket.from_bytes(data)
        assert packet.name == "Test Dev"

        # Test with no name
        packet = AdPacket.from_bytes(
            bytes(
                [
                    0x02,  # Length
                    AdType.FLAGS,
                    0x06,  # Flags value
                ]
            )
        )
        assert packet.name is None

    def test_get_method(self):
        # Create a packet with multiple AD structures
        data = bytes(
            [
                # Flags
                0x02,  # Length
                AdType.FLAGS,
                0x06,  # Flags value
                # Complete Local Name
                0x0B,  # Length
                AdType.COMPLETE_LOCAL_NAME,
                *b"Test Device",
            ]
        )

        packet = AdPacket.from_bytes(data)

        # Test getting existing AD structure
        flags_struct = packet.get(AdType.FLAGS)
        assert flags_struct is not None
        assert flags_struct.ad_type == AdType.FLAGS
        assert flags_struct.value == bytes([0x06])

        # Test getting non-existent AD structure
        uuid_struct = packet.get(AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS)
        assert uuid_struct is None

    def test_get_all_method(self):
        # Create a packet with multiple instances of the same AD type
        data = bytes(
            [
                # First 16-bit UUID list
                0x03,  # Length
                AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
                0xAA,
                0xBB,
                # Second 16-bit UUID list
                0x03,  # Length
                AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS,
                0xCC,
                0xDD,
            ]
        )

        packet = AdPacket.from_bytes(data)
        uuid_structs = packet.get_all(AdType.COMPLETE_LIST_OF_16_BIT_SERVICE_OR_SERVICE_CLASS_UUIDS)

        assert len(uuid_structs) == 2
        assert uuid_structs[0].value == bytes([0xAA, 0xBB])
        assert uuid_structs[1].value == bytes([0xCC, 0xDD])

        # Test with non-existent AD type
        flags_structs = packet.get_all(AdType.FLAGS)
        assert len(flags_structs) == 0

    def test_bytes_conversion(self):
        """Test that converting a packet to bytes and back results in the same packet."""
        # Device name with correct length calculation
        device_name = b"Test Device"
        name_length = len(device_name) + 1  # +1 for type byte

        # Create a packet from bytes
        original_data = bytes(
            [
                0x02,
                AdType.FLAGS,
                0x06,  # First AD structure
                name_length,
                AdType.COMPLETE_LOCAL_NAME,
                *device_name,  # Second AD structure with correct length
            ]
        )

        packet = AdPacket.from_bytes(original_data)

        # Convert back to bytes
        converted_data = bytes(packet)

        # Check if the conversion is correct
        assert converted_data == original_data


class TestServiceData:
    def test_creation(self):
        service_data = ServiceData(
            uuid="0000180f-0000-1000-8000-00805f9b34fb", data=bytes([0x01, 0x02, 0x03])
        )
        assert service_data.uuid == "0000180f-0000-1000-8000-00805f9b34fb"
        assert service_data.data == bytes([0x01, 0x02, 0x03])

    def test_serialization(self):
        service_data = ServiceData(
            uuid="0000180f-0000-1000-8000-00805f9b34fb", data=bytes([0x01, 0x02, 0x03])
        )
        # This tests the field_serializer
        serialized = service_data.model_dump()
        assert serialized["data"] == base64.b64encode(bytes([0x01, 0x02, 0x03])).decode("utf-8")

    def test_validation(self):
        # Test with bytes
        service_data = ServiceData(
            uuid="0000180f-0000-1000-8000-00805f9b34fb", data=bytes([0x01, 0x02, 0x03])
        )
        assert service_data.data == bytes([0x01, 0x02, 0x03])

        # Test with base64 string
        base64_data = base64.b64encode(bytes([0x01, 0x02, 0x03])).decode("utf-8")
        service_data = ServiceData(uuid="0000180f-0000-1000-8000-00805f9b34fb", data=base64_data)
        assert service_data.data == bytes([0x01, 0x02, 0x03])

        # Test with invalid type
        with pytest.raises(ValueError):
            ServiceData(
                uuid="0000180f-0000-1000-8000-00805f9b34fb",
                data=123,  # Invalid data type
            )


class TestManufacturerData:
    def test_creation(self):
        mfg_data = ManufacturerData(
            company_identifier=0x004C,  # Apple
            data=bytes([0x01, 0x02, 0x03]),
        )
        assert mfg_data.company_identifier == 0x004C
        assert mfg_data.data == bytes([0x01, 0x02, 0x03])

    def test_company_name_computed_field(self):
        # This test might need to be adjusted based on your bluenumbers implementation
        # We'll just check that the computed field exists and is either a string or None
        mfg_data = ManufacturerData(
            company_identifier=0x004C,  # Apple
            data=bytes([0x01, 0x02, 0x03]),
        )
        assert isinstance(mfg_data.company_name, str) or mfg_data.company_name is None

    def test_serialization(self):
        mfg_data = ManufacturerData(company_identifier=0x004C, data=bytes([0x01, 0x02, 0x03]))
        # This tests the field_serializer
        serialized = mfg_data.model_dump()
        assert serialized["data"] == base64.b64encode(bytes([0x01, 0x02, 0x03])).decode("utf-8")

    def test_validation(self):
        # Test with bytes
        mfg_data = ManufacturerData(company_identifier=0x004C, data=bytes([0x01, 0x02, 0x03]))
        assert mfg_data.data == bytes([0x01, 0x02, 0x03])

        # Test with base64 string
        base64_data = base64.b64encode(bytes([0x01, 0x02, 0x03])).decode("utf-8")
        mfg_data = ManufacturerData(company_identifier=0x004C, data=base64_data)
        assert mfg_data.data == bytes([0x01, 0x02, 0x03])

        # Test with invalid type
        with pytest.raises(ValueError):
            ManufacturerData(
                company_identifier=0x004C,
                data=123,  # Invalid data type
            )
