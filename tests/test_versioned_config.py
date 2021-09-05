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

    def test_unversioned_builtin_types_nested1(self):
        c1 = new_config_obj(v1=0, v2=True)
        c2 = new_config_obj(v1=99.9, v2=c1)
        d = c2.to_json_serializable()

        self.assertEqual(d['v1'], 99.9)
        self.assertEqual(d['v2']['v1'], 0)
        self.assertEqual(d['v2']['v2'], True)

    def test_unversioned_builtin_types_nested2(self):
        c1 = new_config_obj(v1="lvl5", v2=9999)
        c2 = new_config_obj(v1="lvl4", v2=c1)
        c3 = new_config_obj(v1="lvl3", v2=c2)
        c4 = new_config_obj(v1="lvl2", v2=c3)
        c5 = new_config_obj(v1="lvl1", v2=c4)
        d = c5.to_json_serializable()

        self.assertEqual(d['v1'], "lvl1")
        self.assertEqual(d['v2']['v1'], "lvl2")
        self.assertEqual(d['v2']['v2']['v1'], "lvl3")
        self.assertEqual(d['v2']['v2']['v2']['v1'], "lvl4")
        self.assertEqual(d['v2']['v2']['v2']['v2']['v1'], "lvl5")
        self.assertEqual(d['v2']['v2']['v2']['v2']['v2'], 9999)

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

    def test_unversioned_config_underscore_vars_ignored(self):
        c = new_config_obj(var1=1, _var2=2, __var3=3, ___var4=4, var5=5)
        d = c.to_json_serializable()

        self.assertEqual(len(d), 2)
        self.assertEqual(d['var1'], 1)
        self.assertEqual(d['var5'], 5)
        self.assertFalse('_var2' in d)
        self.assertFalse('__var3' in d)
        self.assertFalse('___var4' in d)

    def test_unversioned_config_property_ignored(self):
        class C1(VersionedConfigObject):
            def __init__(self):
                self.v1 = 123
                self._v2 = None

            @property
            def v2(self):
                return self._v2

            @v2.setter
            def v2(self, value):
                self._v2 = value

        c = C1()
        d = c.to_json_serializable()
        self.assertEqual(len(d), 1)
        self.assertEqual(d['v1'], 123)

    def test_versioned_config_no_migrations_available(self):
        class VC1(VersionedConfigObject):
            VERSION = "1.0.1"

        c = VC1()
        self.assertRaises(VersionedConfigMigrationError, c.from_json_serializable, {'config_version': "1.0.0"})

    def test_versioned_config_wrong_migrations_available(self):
        class VC1(VersionedConfigObject):
            VERSION = "1.0.2"

            def migrate_100_101(self, attrs):
                return attrs

            def __init__(self):
                self.add_migration("1.0.0", "1.0.1", self.migrate_100_101)

        c = VC1()
        self.assertRaises(VersionedConfigMigrationError, c.from_json_serializable, {'config_version': "1.0.0"})

    def test_versioned_config_single_migration_param_added(self):
        class VC1(VersionedConfigObject):
            VERSION = "1.0.1"

            def migrate_100_101(self, attrs):
                attrs['var2'] = 44
                return attrs

            def __init__(self):
                self.var1 = 11
                self.var2 = 22
                self.add_migration("1.0.0", "1.0.1", self.migrate_100_101)

        # Verify the default values before loading old config to force migration
        c = VC1()
        self.assertEqual(c.var1, 11)
        self.assertEqual(c.var2, 22)

        c.from_json_serializable({'config_version': '1.0.0', 'var1': 33})
        self.assertEqual(c.var1, 33)
        self.assertEqual(c.var2, 44)

    def test_versioned_config_single_migration_param_removed(self):
        class VC1(VersionedConfigObject):
            VERSION = "1.0.1"

            def migrate_100_101(self, attrs):
                del attrs['var2']
                return attrs

            def __init__(self):
                self.var1 = 11
                self.add_migration("1.0.0", "1.0.1", self.migrate_100_101)

        # Verify the default value before loading old config to force migration
        c = VC1()
        self.assertEqual(c.var1, 11)

        c.from_json_serializable({'config_version': '1.0.0', 'var1': 33, 'var2': 555})
        self.assertEqual(c.var1, 33)

    def test_versioned_config_single_nested_migration_param_removed(self):
        class VC1(VersionedConfigObject):
            VERSION = "1.0.1"

            def migrate_100_101(self, attrs):
                del attrs['var2']
                return attrs

            def __init__(self):
                self.var1 = 22
                self.add_migration("1.0.0", "1.0.1", self.migrate_100_101)

        class VC2(VersionedConfigObject):
            VERSION = None

            def __init__(self):
                self.var1 = 11
                self.var2 = VC1()


        # Verify the default value before loading old config to force migration
        c = VC2()
        self.assertEqual(c.var1, 11)
        self.assertEqual(c.var2.var1, 22)

        # Config data to be migrated
        d = {
            'var1': 77,
            'var2': {
                'var1': 88,
                'var2': 48309853085,
                'config_version': "1.0.0"
            }
        }

        c.from_json_serializable(d)
        self.assertEqual(c.var1, 77)
        self.assertEqual(c.var2.var1, 88)

    def test_versioned_config_double_nested_migration(self):
        class VC1(VersionedConfigObject):
            VERSION = "1.0.1"

            # When this config moved from 1.0.0 to 1.0.1, the 'var2' was removed
            def migrate_100_101(self, attrs):
                del attrs['var2']
                return attrs

            def __init__(self):
                self.var1 = 33
                self.add_migration("1.0.0", "1.0.1", self.migrate_100_101)

        class VC2(VersionedConfigObject):
            VERSION = "2.0.1"

            # When this config moved from 2.0.0 to 2.0.1, the 'var2' field was added
            def migrate_200_201(self, attrs):
                attrs['var2'] = 44
                return attrs

            def __init__(self):
                self.var1 = 11
                self.var2 = 22
                self.var3 = VC1()

                self.add_migration("2.0.0", "2.0.1", self.migrate_200_201)

        # Verify the default value before loading old config to force migration
        c = VC2()
        self.assertEqual(c.var1, 11)
        self.assertEqual(c.var2, 22)
        self.assertEqual(c.var3.var1, 33)

        # Config data to be migrated
        d = {
            'var1': 77,
            'var3': {
                'var1': 99,
                'var2': 48309855,
                'config_version': "1.0.0"
            },

            'config_version': '2.0.0'
        }

        c.from_json_serializable(d)
        self.assertEqual(c.var1, 77)
        self.assertEqual(c.var2, 44)
        self.assertEqual(c.var3.var1, 99)

    def test_versioned_config_change_config_key_name(self):
        class VC1(VersionedConfigObject):
            VERSION = "9.9.9"

            def __init__(self):
                self.config_version_key = "abcdefg"
                self.var1 = "data"

        c = VC1()
        d = c.to_json_serializable()

        self.assertEqual(len(d), 2)
        self.assertEqual(d["abcdefg"], "9.9.9")
        self.assertEqual(d["var1"], "data")

    def test_versioned_config_multiple_migrations(self):
        class VC1(VersionedConfigObject):
            VERSION = "1.0.3"

            def migrate_100_101(self, attrs):
                attrs['b'] = 77
                return attrs

            def migrate_101_102(self, attrs):
                attrs['x'] = 88
                return attrs

            def migrate_102_103(self, attrs):
                del attrs['c']
                attrs['y'] = 99
                return attrs

            def __init__(self):
                self.a = 1
                self.b = 2
                self.x = 3
                self.y = 4

                self.add_migration("1.0.0", "1.0.1", self.migrate_100_101)
                self.add_migration("1.0.1", "1.0.2", self.migrate_101_102)
                self.add_migration("1.0.2", "1.0.3", self.migrate_102_103)

        c = VC1()
        c.from_json_serializable({'config_version': '1.0.0', 'a': 66, 'c': 14134})

        self.assertEqual(c.a, 66)
        self.assertEqual(c.b, 77)
        self.assertEqual(c.x, 88)
        self.assertEqual(c.y, 99)
        self.assertFalse(hasattr(c, 'c'))
