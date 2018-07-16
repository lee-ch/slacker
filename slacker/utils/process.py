'''
Functions for daemonizing and modifying running processes
'''

# Python libs
from __future__ import absolute_import, print_function, unicode_literals
import copy
import os
import sys
import time
import errno
import types
import signal
import logging
import threading
import contextlib
import subprocess
import multiprocessing
import multiprocessing.util
import socket

# Import 3rd party libs
from salt.ext import six
from salt.ext.six.moves import queue, range
from tornado import gen


log = logging.getLogger(__name__)

HAS_PSUTIL = False
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    pass

try:
    import setproctitle
    HAS_SETPROCTITLE = True
except ImportError:
    HAS_SETPROCTITLE = False


def appendproctitle(name):
    '''
    Append ``name`` to the current process title
    '''
    if HAS_SETPROCTITLE:
        setproctitle.setproctitle(setproctitle.getproctitle() + ' ' + name)


def daemonize(redirect_out=True):
    '''
    Daemonize process
    '''
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as exc:
        log.error('fork #1 failed: %s (%s)', exc.errno, exc)
        sys.exit(1)

    os.chdir('/')
    os.setsid()
    os.umask(0o022)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as exc:
        log.error('fork #2 failed: %s (%s)', exc.errno, exc)

    if redirect_out:
        with open('/dev/null', 'r+') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdin.fileno())
            os.dup2(dev_null.fileno(), sys.stdout.fileno())
            os.dup2(dev_null.fileno(), sys.stderr.fileno())
            os.dup2(dev_null.fileno(), 0)
            os.dup2(dev_null.fileno(), 1)
            os.dup2(dev_null.fileno(), 2)