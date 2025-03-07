# BlueNumbers: Easily access Bluetooth SIG Assigned Numbers

## Usage

Install the Python package using `pip`:

```sh
# pip install bluenumbers  # TODO: Publish to PyPI
pip install git+https://github.com/Microwave-WYB/bluenumbers.git
```

Using the package is very simple:

```python
import bluenumbers

print(bluenumbers.uuids.get(0x0002))
print(bluenumbers.company_identifiers.get(0x004C))
print(bluenumbers.ad_types.get(0x09))
```

This will output:

```
{'short_uuid': 2, 'name': 'UDP', 'id': None, 'category': 'protocol_identifiers'}
{'value': 76, 'name': 'Apple, Inc.'}
{'value': 9, 'name': 'Complete Local Name', 'reference': 'Core Specification Supplement, Part A, Section 1.2'}
```
