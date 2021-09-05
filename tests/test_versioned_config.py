import unittest

from config_object import VersionedConfigObject
from config_object import ObjectNotSerializableError, InvalidFieldName, VersionedConfigMigrationError


# Test with a child class of VersionedConfigObject
class TestConfigClass(VersionedConfigObject):
    pass

# Helper function to create a new config object instance with specific field names / values
def new_config_obj(**kwargs):
    ret = TestConfigClass()
    for attrname in kwargs:
        setattr(ret, attrname, kwargs[attrname])

    return ret


class TestVersionedConfig(unittest.TestCase):
    def test_unversioned_builtin_types(self):
        c = new_config_obj(
            intvar=123, boolvar=True, floatvar=123.2, strvar="test string",
            listvar=[1,2,3], dictvar={1:"a", 2:"b"}
        )

        d = c.to_json_serializable()

        self.assertEqual(d['intvar'], 123)
        self.assertEqual(d['boolvar'], True)
        self.assertEqual(d['floatvar'], 123.2)
        self.assertEqual(d['strvar'], "test string")
        self.assertEqual(d['listvar'], [1,2,3,])
        self.assertEqual(d['dictvar'], {1:"a", 2:"b"})

        
    def test_unversioned_builtin_types_nested(self):
        c1 = new_config_obj(v1=0, v2=True)
        c2 = new_config_obj(v1=99.9, v2=c1)
        d = c2.to_json_serializable()

        self.assertEqual(d['v1'], 99.9)
        self.assertEqual(d['v2']['v1'], 0)
        self.assertEqual(d['v2']['v2'], True)

    def test_unversioned_config_version_paramname_allowed(self):
        c = new_config_obj(a=1, config_version=222, b=3343)
        d = c.to_json_serializable()

        self.assertEqual(d['a'], 1)
        self.assertEqual(d['config_version'], 222)
        self.assertEqual(d['b'], 3343)

    def test_unversioned_config_unserializable_object(self):
        c = new_config_obj(a=1, b=object())
        self.assertRaises(ObjectNotSerializableError, c.to_json_serializable)

    def test_unversioned_config_invalid_paramname(self):
        c = new_config_obj(var1=1, var2=2)
        attrs_to_load = {'var1':10, 'var2':10, 'var3':10}
        self.assertRaises(InvalidFieldName, c.from_json_serializable, attrs_to_load)

    def test_unversioned_config_callables_ignored(self):
        class C1(VersionedConfigObject):
            def custom_method1(self):
                return 1

            def custom_method2(self):
                return 2

            def __init__(self):
                self.v1 = 1234
                self.v2 = [7,7,7]

        c = C1()
        d = c.to_json_serializable()

        self.assertEqual(d['v1'], 1234)
        self.assertEqual(d['v2'], [7,7,7])
