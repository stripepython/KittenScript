from collections import namedtuple

VersionClass = namedtuple('version', ('major', 'minor', 'micro'))

version = VersionClass(1, 0, 5)

def get_version():
    return '.'.join(map(str, version))
