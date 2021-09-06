Python library for safe JSON-serializable objects
#################################################


Defining serializable object structure
--------------------------------------

To create a new JSON-serializable object, define a new class that is a subclass of
``VersionedConfigObject``. Instance variables of a ``VersionedConfigObject`` (any instance
variables that are not callables, and do not begin with ``_``) are treated as key-value
pairs in a JSON object. ``VersionedConfigObject`` instances can also be nested, i.e.
the value of an instance variable can be another ``VersionedConfigObject instance``:

*Example of defining a new serializable object structure*:

.. code-block:: python

    from config_object import VersionedConfigObject

    class MyConfig1(VersionedConfigObject):
        def __init__(self):
            # Any instance variables that are not callables, and do not begin with "_",
            # will be treated as a serializable attribute
            self.var1 = 123
            self.var2 = ["a", "b"]

    class MyConfig2(VersionedConfigObject):
        def __init__(self):
            self.var1 = 99.9

            # Instance variables can be another VersionedConfigObject
            self.var2 = MyConfig1()

Serializing/deserializing a ``VersionedConfigObject`` instance
--------------------------------------------------------------

*Example of instantiating/serializing/deserializing custom object*:

.. code-block:: python

   >>> config = MyConfig2()                       # Create instance of the MyConfig2 class defined above
   >>> config.var1 = 99.8                         # Modify some values
   >>> config.var2.var2.append("c")
   >>>
   >>> with open('config.json', 'w') as fh:       # Write to .json file
   >>>     config.dump(fh, indent=4)
   >>>
   >>> s = config.dumps(indent=4)                 # Or, get .json data as string
   >>> print(s)
   {
       "var1": 99.8,
       "var2": {
           "var1": 123,
           "var2": [
               "a",
               "b",
               "c"
           ]
       }
   }
   >>>
   >>> d = config.to_json_serializable()          # Or, get JSON-serializable data as dict (suitable for json.dump)
   >>> print(d)
   {'var1': 99.8, 'var2': {'var1': 123, 'var2': ['a', 'b', 'c']}}
   >>>
   >>> with open('config.json', 'r') as fh:       # Populate config object from JSON file
   >>>     config.load(fh)
   >>>

Versioned serializable objects and migrations
---------------------------------------------

Versioned objects
=================

Serializable objects can be versioned by setting the ``VERSION`` class variable
on a ``VersionedConfigObject`` subclass. Migration functions can be added so that
when JSON data with an older version is loaded, it can be migrated to the newest
version.

*Example of defining a versioned object class*:

.. code-block:: python

    from config_object import VersionedConfigObject

    class MyVersionedConfig(VersionedConfigObject):
        VERSION = "1.0.0"

        def __init__(self):
            self.var1 = 0.0
            self.var2 = 555

Migrations
==========

Now, imagine a situation where you have already released software that saves/loads data using
the ``MyVersionedConfig`` class. In an upcoming new release, you need to change the format
of ``MyVersionedConfig``, but of course you don't want your update to break any JSON files
that users may already have on their systems. This is where migrations are useful. For each
new release that changes the format of ``MyVersionedConfig``, you can define a migration
function that modifies the object structure to conform to the new object structure.

*Example of adding a migration function to the same class*:

.. code-block:: python

    from config_object import VersionedConfigObject

    class MyVersionedConfig(VersionedConfigObject):
        VERSION = "1.0.1"

        def __init__(self):
            self.var1 = 0.0
            self.var2 = 555

            # In the update to 1.0.1, var3 was added
            self.var3 = "zzz"

            self.add_migration("1.0.0", "1.0.1", self.migrate_100_101)

         def migrate_100_101(self, attrs):
            # Add var3 to the JSON decoded data
            attrs['var3'] = ""

            # Return the modified data
            return attrs

For further releases, add more migration functions if needed (make sure migration
functions are added in the correct order):

*Example of adding another migration function to the same class*:

.. code-block:: python

    from config_object import VersionedConfigObject

    class MyVersionedConfig(VersionedConfigObject):
        VERSION = "1.0.2"

        def __init__(self):
            # In the update to 1.0.2, var4 was added, and var1 was removed
            self.var2 = 555
            self.var3 = "zzz"
            self.var4 = "yyy"

            self.add_migration("1.0.0", "1.0.1", self.migrate_100_101)
            self.add_migration("1.0.1", "1.0.2", self.migrate_101_102)

         def migrate_100_101(self, attrs):
            attrs['var3'] = ""
            return attrs

         def migrate_101_102(self, attrs):
            # Remove var1
            del attrs['var1']

            # Add var4
            attrs['var4']

            return attrs

.. note:: any added migrations will be automatically performed, if needed, by the
          ``load()``, ``loads()`` and ``from_json_serializable()`` methods.
