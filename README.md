# BlueNumbers: Easily access Bluetooth SIG Assigned Numbers

## Usage

Ensure you have all of the required dependencies:

-   Python 3.9+
-   Git (for updating the data source)
-   Internet connection for the first time you import the package (This is when the data is downloaded)

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

Note that on your first import of the package, the data will be downloaded using Git. This may take a while depending on your internet connection.

### Updating the Data Source

This package uses the data from the [Bluetooth SIG Public Repository](https://bitbucket.org/bluetooth-SIG/public/) to provide the assigned number information. On your first import of this package, the data will automatically be downloaded and stored in the package directory. To update the data, you can use the `update` function:

```python
import bluenumbers

bluenumbers.update()
```

This will run `git pull` in the package directory to update the data.
