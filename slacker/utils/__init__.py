# -*- coding: utf-8 -*-
'''
Some of the utils used by salt

New functions should be organized in other files under salt/utils/*.
'''

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import os

# Import Salt libs
from slacker.defaults import DEFAULT_PATH_DELIM

# Import 3rd-party libs
from slacker.ext import six