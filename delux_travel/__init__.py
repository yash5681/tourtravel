import pymysql

# Install PyMySQL as MySQLdb for Django
pymysql.install_as_MySQLdb()

# Compatibility patches for WAMP Server MySQL 5.5.x
try:
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.backends.mysql.base import DatabaseWrapper
    from django.db.backends.mysql.features import DatabaseFeatures

    # Bypass strict MySQL 8+ version check
    BaseDatabaseWrapper.check_database_version_supported = lambda self: None

    # Disable microsecond precision not supported in MySQL < 5.6.4
    DatabaseFeatures.supports_microsecond_precision = False
    DatabaseWrapper._data_types['DateTimeField'] = 'datetime'
    DatabaseWrapper._data_types['TimeField'] = 'time'
except Exception:
    pass
