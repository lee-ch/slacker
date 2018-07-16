# -*- coding: utf-8 -*-
'''
Setup version of Slacker
'''

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals
import re
import sys
import platform

# linux_distribution deprecated in python 3.7
try:
    from platform import linux_distribution
except ImportError:
    from distro import linux_distribution

# Import 3rd-party libs
from slacker.ext import six
from slacker.ext.six.moves import map

# This is used during install, so don't use external modules
if sys.version_info[0] == 3:
    MAX_SIZE = sys.maxsize
    string_types = (str,)
else:
    MAX_SIZE = sys.maxint
    string_types = (six.string_types,)



VERSION = (0, 0, 1)
__VERSION__ = '.'.join(map(str, VERSION))

__version__ = __VERSION__
version = __version__


def slacker_information():
    '''
    Report version of slacker.
    '''
    yield 'Slacker', __version__


def dependency_information():
    '''
    Report versions of library dependencies.
    '''
    libs = [
        ('Python', None, sys.version.rsplit('\n')[0].strip()),
        ('Jinja2', 'jinja2', '__version__'),
        ('M2Crypto', 'M2Crypto', 'version'),
        ('msgpack-python', 'msgpack', 'version'),
        ('msgpack-pure', 'msgpack_pure', 'version'),
        ('pycrypto', 'Crypto', '__version__'),
        ('pycryptodome', 'Cryptodome', 'version_info'),
        ('libnacl', 'libnacl', '__version__'),
        ('PyYAML', 'yaml', '__version__'),
        ('ioflo', 'ioflo', '__version__'),
        ('PyZMQ', 'zmq', '__version__'),
        ('RAET', 'raet', '__version__'),
        ('ZMQ', 'zmq', 'zmq_version'),
        ('Mako', 'mako', '__version__'),
        ('Tornado', 'tornado', 'version'),
        ('timelib', 'timelib', 'version'),
        ('dateutil', 'dateutil', '__version__'),
        ('pygit2', 'pygit2', '__version__'),
        ('libgit2', 'pygit2', 'LIBGIT2_VERSION'),
        ('smmap', 'smmap', '__version__'),
        ('cffi', 'cffi', '__version__'),
        ('pycparser', 'pycparser', '__version__'),
        ('gitdb', 'gitdb', '__version__'),
        ('gitpython', 'git', '__version__'),
        ('python-gnupg', 'gnupg', '__version__'),
        ('mysql-python', 'MySQLdb', '__version__'),
        ('cherrypy', 'cherrypy', '__version__'),
        ('docker-py', 'docker', '__version__'),
    ]

    for name, imp, attr in libs:
        if imp is None:
            yield name, attr
            continue
        try:
            imp = __import__(imp)
            version = getattr(imp, attr, None)
            if version is None:
                version = 'Unable to determine version'
            if callable(version):
                version = version()
            if isinstance(version, (tuple, list)):
                version = '.'.join(map(str, version))
            yield name, version
        except Exception:
            yield name, None


def system_information():
    '''
    Report system versions.
    '''
    def system_version():
        '''
        Return host system version.
        '''
        lin_ver = linux_distribution()
        mac_ver = platform.mac_ver()
        win_ver = platform.win32_ver()

        if lin_ver[0]:
            return ' '.join(lin_ver)
        elif mac_ver[0]:
            if isinstance(mac_ver[1], (tuple, list)) and ''.join(mac_ver[1]):
                return ' '.join([mac_ver[0], '.'.join(mac_ver[1]), mac_ver[2]])
            else:
                return ' '.join([mac_ver[0], mac_ver[2]])
        elif win_ver[0]:
            return ' '.join(win_ver)
        else:
            return ''

    version = system_version()
    release = platform.release()
    if platform.win32_ver()[0]:
        import win32api
        server = {'Vista': '2008Server',
                  '7': '200ServerR2',
                  '8': '2012Server',
                  '8.1': '2012ServerR2',
                  '10': '2016Server'}
        
        if win32api.GetVerionEx(1)[8] > 1 and release in server:
            release = server[release]
        _, ver, sp, extra = platform.win32_ver()
        version = ' '.join([release, ver, sp, extra])

    system = [
        ('system', platform.system()),
        ('dist', ' '.join(linux_distribution(full_distribution_name=False))),
        ('release', release),
        ('machine', platform.machine()),
        ('version', version),
    ]

    for name, attr in system:
        yield name, attr
        continue


def version_report():
    return 'Slacker v{0}'.format(__version__)