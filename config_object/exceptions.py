class ObjectNotSerializableError(Exception):
    """
    Raised when a VersionedConfigObject instance contains a field that is not serializable
    """
    pass

class InvalidFieldName(Exception):
    """
    Raised when a loaded config file contains a field that does not exist in the
    corresponding VersionedConfigObject instance
    """
    pass

class VersionedConfigMigrationError(Exception):
    """
    Raised when a loaded config file cannot be migrated to the current version of
    a VersionedConfigObject instance
    """
    pass


