import unittest

from config_object.versioned_config import VersionedConfigObject
from config_object.data_types import BinaryBlob


class TestDataTypes(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_binary_blob_field(self):
        class TestClass(VersionedConfigObject):
            def __init__(self):
                self.var1 = 0.0
                self.var2 = BinaryBlob(b'Hello, world!')

        c1 = TestClass()
        s = c1.dumps()
        self.assertEqual('{"var1": 0.0, "var2": "SGVsbG8sIHdvcmxkIQ=="}', s)

        c2 = TestClass()
        c2.loads(s)
        self.assertEqual(c2.var1, 0.0)
        self.assertEqual(c2.var2.data, b'Hello, world!')
