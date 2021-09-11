import base64

from versioned_config import VersionedConfigObject


class BinaryBlob(VersionedConfigObject):
    """
    Allows arbitrary binary blobs to be serialized/deserialized as base64 data
    in JSON files
    """
    def __init__(self, data=b''):
        self._bytes = data

    @property
    def data(self):
        """
        Return the binary data as a bytes() object
        """
        return self._bytes

    @data.setter
    def data(self, b: bytes):
        """
        Set the binary data as a bytes object
        """
        self._bytes = b

    def to_json_serializable(self):
        return base64.b64encode(self._bytes).decode('utf-8')

    def from_json_serializable(self, b64_str):
        self._bytes = base64.b64decode(b64_str.encode('utf-8'))
