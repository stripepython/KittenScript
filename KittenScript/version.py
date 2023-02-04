from collections import namedtuple

VersionClass = namedtuple('version', ('major', 'minor', 'micro'))

version = VersionClass(1, 2, 1)

def get_version():
    return '.'.join(map(str, version))
