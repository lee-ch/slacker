'''
Functions for manipulating, inspecting or working with data types
and data structures.
'''

# Python libs
from __future__ import absolute_import, print_function, unicode_literals
import collections
import copy
import fnmatch
import logging
import re

import salt.utils.stringutils

from salt.utils.decorators.jinja import jinja_filter

from slacker.ext import six
from slacker.ext.six.moves import range

log = logging.getLogger(__name__)


def decode_dict(data, encoding=None, errors='strict', keep=False,
                normalize=False, preserve_dict_class=False,
                preserve_tuples=False, to_str=False):
    '''
    Decode all string values to Unicode. Optionally use to_str=True to ensure
    strings are str types and not unicode in Python 2
    '''
    _decode_func = salt.utils.stringutils.to_unicode \
        if not to_str \
        else salt.utils.stringutils.to_str
    rv = data.__class__() if preserve_dict_class else {}
    for key, value in six.iteritems(data):
        if isinstance(key, tuple):
            key = decode_tuple(key, encoding, errors, keep, normalize,
                               preserve_dict_class, to_str) \
                if preserve_tuples \
                else decode_list(key, encoding, errors, keep, normalize,
                                preserve_dict_class, preserve_tuples, to_str)
        else:
            try:
                key = _decode_func(key, encoding, errors, normalize)
            except TypeError:
                pass
            except UnicodeDecodeError:
                if not keep:
                    pass

        if isinstance(value, list):
            value = decode_list(value, encoding, errors, keep, normalize,
                                preserve_dict_class, preserve_tuples, to_str)
        elif isinstance(value, tuple):
            value = decode_tuple(value, encoding, errors, keep, normalize,
                                preserve_dict_class, to_str) \
                if preserve_tuples \
                else decode_list(value, encoding, errors, keep, normalize,
                                preserve_dict_class, preserve_tuples, to_str)
        elif isinstance(value, collections.Mapping):
            value = decode_dict(value, encoding, errors, keep, normalize,
                                preserve_dict_class, preserve_tuples, to_str)
        else:
            try:
                value = _decode_func(value, encoding, errors, normalize)
            except TypeError:
                pass
            except UnicodeDecodeError:
                if not keep:
                    raise

        rv[key] = value
    return rv


def decode_list(data, encoding=None, errors='strict', keep=False,
                normalize=False, preserve_dict_class=False,
                preserve_tuples=False, to_str=False):
    '''
    Decode all string values to unicode. Optionally use to_str=True to ensure
    strings are str types and not unicode in Python 2
    '''
    _decode_func = salt.utils.stringutils.to_unicode \
        if not to_str \
        else salt.utils.stringutils.to_str
    rv = []
    for item in data:
        if isinstance(item, list):
            item = decode_list(item, encoding, errors, keep, normalize,
                               preserve_dict_class, preserve_tuples, to_str)
        elif isinstance(item, tuple):
            item = decode_tuple(item, encoding, errors, keep, normalize,
                                preserve_dict_class, to_str)
        elif isinstance(item, collections.Mapping):
            item = decode_dict(item, encoding, errors, keep, normalize,
                               preserve_dict_class, preserve_tuples, to_str)
        else:
            try:
                item = _decode_func(item, encoding, errors, normalize)
            except TypeError:
                pass
            except UnicodeDecodeError:
                if not keep:
                    raise

        rv.append(item)
    return rv


def decode_tuple(data, encoding=None, errors='strict', keep=False,
                normalize=False, preserve_dict_class=False, to_str=False):
    '''
    Decode all string values to Unicode. Optionally use to_str=True to ensure
    strings are str types and not unicode on Python 2.
    '''
    return tuple(
        decode_list(data, encoding, errors, keep, normalize,
                    preserve_dict_class, True, to_str)
    )


def encode(data, encoding=None, errors='strict', keep=False,
           preserve_dict_class=False, preserve_tuples=False):
    '''
    Generic function which will encode whichever type is passed, if necessary

    If `strict` is True, and `keep` is False, and we fail to encode, a
    UnicodeEncodeError will be raised. Passing `keep` as True allows for the
    original value to silently be returned in cases where encoding fails. This
    can be useful for cases where the data passed to this function is likely to
    contain binary blobs.
    '''
    if isinstance(data, collections.Mapping):
        return encode_dict(data, encoding, errors, keep,
                           preserve_dict_class, preserve_tuples)
    elif isinstance(data, list):
        return encode_list(data, encoding, errors, keep,
                           preserve_dict_class, preserve_tuples)
    elif isinstance(data, tuple):
        return encode_tuple(data, encoding, errors, keep, preserve_dict_class) \
            if preserve_tuples \
            else encode_list(data, encoding, errors, keep,
                            preserve_dict_class, preserve_tuples)
    else:
        try:
            return salt.utils.stringutils.to_bytes(data, encoding, errors)
        except TypeError:
            pass
        except UnicodeEncodeError:
            if not keep:
                raise
        return data


@jinja_filter('json_decode_dict')
@jinja_filter('json_encode_dict')
def encode_dict(data, encoding=None, errors='strict', keep=False,
                preserve_dict_class=False, preserve_tuples=False):
    '''
    Encode all string values to bytes
    '''
    rv = data.__class__() if preserve_dict_class else {}
    for key, value in six.iteritems(data):
        if isinstance(key, tuple):
            key = encode_tuple(key, encoding, errors, keep, preserve_dict_class) \
                if preserve_tuples \
                else encode_list(key, encoding, errors, keep,
                                preserve_dict_class, preserve_tuples)
        else:
            try:
                key = salt.utils.stringutils.to_bytes(key, encoding, errors)
            except TypeError:
                pass
            except UnicodeEncodeError:
                if not keep:
                    raise

        if isinstance(value, list):
            value = encode_list(value, encoding, errors, keep,
                                preserve_dict_class, preserve_tuples)
        elif isinstance(value, tuple):
            value = encode_tuple(value, encoding, errors, keep, preserve_dict_class) \
                if preserve_tuples \
                else encode_list(value, encoding, errors, keep,
                                 preserve_dict_class, preserve_tuples)
        elif isinstance(value, collections.Mapping):
            value = encode_dict(value, encoding, errors, keep,
                                preserve_dict_class, preserve_tuples)
        else:
            try:
                value = salt.utils.stringutils.to_bytes(value, encoding, errors)
            except TypeError:
                pass
            except UnicodeEncodeError:
                if not keep:
                    raise

        rv[key] = value
    return rv


@jinja_filter('json_decode_list')
@jinja_filter('json_encode_list')
def encode_list(data, encoding=None, errors='strict', keep=False,
                preserve_dict_class=False, preserve_tuples=False):
    '''
    Encode all string values to bytes
    '''
    rv = []
    for item in data:
        if isinstance(item, list):
            item = encode_list(item, encoding, errors, keep,
                               preserve_dict_class, preserve_tuples)
        elif isinstance(item, tuple):
            item = encode_tuple(item, encoding, errors, keep, preserve_dict_class) \
                if preserve_tuples \
                else encode_list(item, encoding, errors, keep,
                                 preserve_dict_class, preserve_tuples)
        elif isinstance(item, collections.Mapping):
            item = encode_dict(item, encoding, errors, keep,
                               preserve_dict_class, preserve_tuples)
        else:
            try:
                item = salt.utils.stringutils.to_bytes(item, encoding, errors)
            except TypeError:
                pass
            except UnicodeEncodeError:
                if not keep:
                    raise

        rv.append(item)
    return rv


def encode_tuple(data, encoding=None, errors='strict', keep=False,
                preserve_dict_class=False):
    '''
    Encode all string values to Unicode
    '''
    return tuple(
        encode_list(data, encoding, errors, keep, preserve_dict_class, True))