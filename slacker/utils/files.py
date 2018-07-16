'''
jensys.utils.files
'''
from __future__ import absolute_import, unicode_literals, print_function
import codecs
import contextlib
import errno
import logging
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time