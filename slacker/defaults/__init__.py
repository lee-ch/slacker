# -*- coding: utf-8 -*-
'''
Default values to be imported
'''
import os
DEFAULT_TARGET_DELIM = ':'
DEFAULT_PATH_DELIM = os.pathsep
DEFAULT_PATH_SEP = os.sep
DEFAULT_PATHS = [p for p in os.getenv('PATH', None).split(DEFAULT_PATH_DELIM) if p is not None]