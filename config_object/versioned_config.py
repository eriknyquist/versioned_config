import json

from config_object.exceptions import (
        ObjectNotSerializableError, InvalidFieldName, VersionedConfigMigrationError
)


DEFAULT_CONFIG_VERSION_KEY = "config_version"


class VersionedConfigMigration(object):
    """
    Container class for data required to migrate a config object from one version
    to the next version
    """
    def __init__(self, from_version, to_version, migrate_func: callable):
        """
        :param from_version: version to migrate from
        :param to_version: version to migrate to
        :param callable migrate_func: function to do the migration
        """
        self.from_version = from_version
        self.to_version = to_version
        self.migrate_func = migrate_func

    def migrate(self, attrs: dict) -> dict:
        return self.migrate_func(attrs)


class VersionedConfigObject(object):
    """
    A nestable, versionable configuration object that can be converted to, and
    from, a JSON-serializable dict.
    """

    VERSION = None

    def _is_serializable_builtin(self, obj) -> bool:
        """
        Check if an object is a builtin serializable type

        :param obj: object to check
        :return: True if object is builtin serializable type
        """
        return type(obj) in [int, float, bool, str, list, dict]

    def _is_instance_var(self, attrname: str) -> bool:
        """
        Check if instance attribute is serializable by name

        :param attrname: name of attribute to check

        :return: True if attribute is serializable instance variable
        """
        return hasattr(self, attrname) and (not callable(self.__dict__[attrname])) and (not attrname.startswith('_'))

    def _instance_varname_generator(self):
        """
        Returns a generator that generates all names of serializable instance variables
        """
        for n in self.__dict__:
            if (not callable(self.__dict__[n])) and (not n.startswith('_')):
                yield n

    def _migrate(self, attrs: dict, old_version, target_version):
        """
        Migrate the provided attributes to the current version of this config object

        :param attrs: attributes to migrate
        :param old_version: old version to migrate from
        :param new_version: current config object version to migrate to
        """
        curr_version = old_version

        if hasattr(self, '_migrations'):
            for m in self._migrations:
                if m.from_version == curr_version:
                    attrs = m.migrate(attrs)
                    curr_version = m.to_version

            if curr_version == target_version:
                # Success
                return

        raise VersionedConfigMigrationError("Failed to migrate %s from version %s to version %s" %
                                            (self.__class__.__name__, old_version, target_version))

    @property
    def config_version_key(self) -> str:
        """
        Return the string to be used for the key of the version field in this confib object
        """
        if hasattr(self, '_config_version_key'):
            return self._config_version_key

        return DEFAULT_CONFIG_VERSION_KEY

    @config_version_key.setter
    def config_version_key(self, value: str):
        """
        Set the string to be used for the key of the version field in this config object

        :param str value: String to be used for version key
        """
        setattr(self, '_config_version_key', value)

    def to_json_serializable(self) -> object:
        """
        Convert this config object's instance variables to a JSON-serializable dict

        :raise ObjectNotSerializableError: if object cannot be serialized
        :raise ValueError: if a reserved name was used as an instance variable name

        :return: dict suitable for passing to json.dump
        """
        attrs = {}
        for n in self._instance_varname_generator():

            obj = getattr(self, n)

            if isinstance(obj, VersionedConfigObject):
                # Object is another ConfigObject instance
                attrs[n] = obj.to_json_serializable()
            elif self._is_serializable_builtin(obj):
                # Object is something else that can be serialized by json library
                attrs[n] = obj
            else:
                # Object is not serializable
                raise ObjectNotSerializableError("Object type '%s' is not serializable" %
                                                 obj.__class__.__name__)

        # Check if this class is versioned
        if self.__class__.VERSION is not None :
            if self.config_version_key in attrs:
                raise ValueError("Cannot have an attribute with name '%s', name is reserved" % n)

            attrs[self.config_version_key] = self.__class__.VERSION

        return attrs

    def from_json_serializable(self, attrs: object):
        """
        Load new values into this config object's instance variables, from a JSON-serializable dict

        :param attrs: JSON-serializable dict to load from

        :raise VersionedConfigMigrationError: if an older config object can't be migrated to the current version
        :raise InvalidFieldName: if config data contains a field name not present in class
        :raise ObjectNotSerializableError: if object cannot be de-serialized
        """
        # Is this class versioned?
        if self.config_version_key in attrs:
            # Do the versions match?
            if attrs[self.config_version_key] != self.__class__.VERSION:
                self._migrate(attrs, attrs[self.config_version_key], self.__class__.VERSION)

            del attrs[self.config_version_key]

        # Migration successful, or not needed
        for n in attrs:
            if not self._is_instance_var(n):
                raise InvalidFieldName("Unrecognized field name '%s'" % n)

            obj = getattr(self, n)
            if isinstance(obj, VersionedConfigObject):
                # Object is another ConfigObject instance
                obj.from_json_serializable(attrs[n])
            elif self._is_serializable_builtin(obj):
                setattr(self, n, attrs[n])
            else:
                raise ObjectNotSerializableError("Object type '%s' is not de-serializable" %
                                                 obj.__class__.__name__)

    def add_migration(self, from_version, to_version, migration_func):
        """
        Add a new migration function to this config object

        :param from_version: version to migrate from
        :param to_version: version to migrate to
        :param migration_func: function to perform the migration
        """
        if not hasattr(self, '_migrations'):
            setattr(self, '_migrations', [])

        self._migrations.append(VersionedConfigMigration(from_version, to_version, migration_func))

    def dump(self, fp, **kwargs):
        """
        Dump this config object to a file as JSON data

        :param fp: file handle to write JSON data to
        :param kwargs: accepts same kwargs as json.dump function
        """
        return json.dump(self.to_json_serializable(), fp, **kwargs)

    def dumps(self, **kwargs) -> str:
        """
        Dump this config object to a string as JSON data

        :param kwargs: accepts same kwargs as json.dumps function

        :return: string containing JSON data
        """
        return json.dumps(self.to_json_serializable(), **kwargs)

    def load(self, fp, **kwargs):
        """
        Populate this config object from a file containing JSON data

        :param fp: file handle to read JSON data from
        :param kwargs: accepts same kwargs as json.load function
        """
        self.from_json_serializable(json.load(fp, **kwargs))

        return self

    def loads(self, s, **kwargs):
        """
        Populate this config object from a string containing JSON data

        :param s: string to read JSON data from
        :param kwargs: accepts same kwargs as json.loads function
        """
        self.from_json_serializable(json.loads(s, **kwargs))
        return self
