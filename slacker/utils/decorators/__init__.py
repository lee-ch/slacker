from __future__ import absolute_import, print_function, unicode_literals
import os
import sys


def decode_string(func):
    def wrapper(string, **kwargs):
        encoding = kwargs.get('encoding', None)
        if encoding is None:
            encoding = 'utf-8'
        decoded = string.decode(encoding)
        return decoded
    return wrapper