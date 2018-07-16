'''
Functions for manipulating or processing strings
'''

# Python libs
from __future__ import absolute_import, print_function, unicode_literals
import base64
import errno
import fnmatch
import logging
import os
import shlex
import re
import time
import unicodedata

# Salt libs
from salt.utils.decorators.jinja import jinja_filter

# 3rd-part libs
from salt.ext import six
from salt.ext.six.moves import range

log = logging.getLogger(__name__)


@jinja_filter('to_bytes')
def to_bytes(s, encoding=None, errors='strict'):
    '''
    Given bytes, bytearray, str or unicode (python 2), return bytes (str for
    python 2)
    '''
    if six.PY3:
        if isinstance(s, bytes):
            return s
        if isinstance(s, bytearray):
            return bytes(s)
        if isinstance(s, six.string_types):
            if encoding:
                return s.encode(encoding, errors)
            else:
                try:
                    return s.encode('utf-8', errors)
                except UnicodeDecodeError:
                    return s.encode(__salt_system_encoding__, errors)
        raise TypeError('expected bytes, bytearray or str')
    else:
        return to_str(s, encoding, errors)


def to_str(s, encoding=None, errors='strict', normalize=False):
    '''
    Given str, bytes, bytearray or unicode (python 2), return str
    '''
    def _normalize(s):
        try:
            return unicodedata.normalize('NFC', s) if normalize else s
        except TypeError:
            return s

    if isinstance(s, str):
        return _normalize(s)
    if six.PY3:
        if isinstance(s, (bytes, bytearray)):
            if encoding:
                return _normalize(s.decode(encoding, errors))
            else:
                try:
                    return _normalize(s.decode('utf-8', errors))
                except UnicodeDecodeError:
                    # Fall back to system detected encoding
                    return _normalize(s.decode(__salt_system_encoding__, errors))
        raise TypeError('expected str, bytes or bytearray not {}'.format(type(s)))
    else:
        if isinstance(s, bytearray):
            return str(s)
        if isinstance(s, unicode):
            if encoding:
                return _normalize(s).encode(encoding, errors)
            else:
                try:
                    return _normalize(s).encode('utf-8', errors)
                except UnicodeDecodeError:
                    return _normalize(s).encode(__salt_system_encoding__, errors)
        raise TypeError('expected str, bytearray or unicode')


def to_unicode(s, encoding=None, errors='strict', normalize=False):
    '''
    Given str or unicode, return unicode (str for python 3)
    '''
    def _normalize(s):
        return unicodedata.normalize('NFC', s) if normalize else s

    if six.PY3:
        if isinstance(s, str):
            return _normalize(s)
        if isinstance(s, (bytes, bytearray)):
            return _normalize(to_str(s, encoding, errors))
        raise TypeError('expected str, bytes or bytearray')
    else:
        if isinstance(s, unicode):
            return _normalize(s)
        elif isinstance(s, (str, bytearray)):
            if encoding:
                return _normalize(s.decode(encoding, errors))
            else:
                return _normalize(s.decode(__salt_system_encoding__, errors))
        raise TypeError('expected str or bytearray not {}'.format(type(s)))


@jinja_filter('str_to_num')
@jinja_filter('to_num')
def to_num(text):
    '''
    Convert a string to a number.
    Returns an integer if the string represents an integer, a floating
    point number if the string is a real number, or the string unchanged
    otherwise.
    '''
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def to_none(text):
    '''
    Convert a string to None if the string is empty or contains only spaces.
    '''
    if six.text_type(text).strip():
        return text
    return None


def is_quoted(value):
    '''
    Return a single or double quote if a string is wrapped in extra quotes.
    Otherwise return an empty string.
    '''
    ret = ''
    if isinstance(value, six.string_types) \
            and value[0] == value[1] \
            and value.startswith(('\'', '"')):
        ret = value[0]
    return ret


def dequote(value):
    '''
    Removes extra quotes around a string
    '''
    if is_quoted(value):
        return value[1:-1]
    return value


@jinja_filter('is_hex')
def is_hex(value):
    '''
    Returns True if value is a hexidecimal string, otherwise returns False
    '''
    try:
        int(value, 16)
        return True
    except (TypeError, ValueError):
        return False


def is_binary(data):
    '''
    Detects if the passed string of data is binary or text
    '''
    if not data or not isinstance(data, (six.string_types, six.binary_type)):
        return False

    try:
        if isinstance(data, six.binary_type):
            if b'\0' in data:
                return True
        elif str('\0') in data:
            return True
    except UnicodeDecodeError:
        pass

    text_characters = ''.join([chr(x) for x in range(32, 127)] + list('\n\r\t\b'))
    if six.PY3:
        if isinstance(data, six.binary_type):
            import salt.utils.data
            nontext = data.translate(None, salt.utils.data.encode(text_characters))
        else:
            trans = ''.maketrans('', '', text_characters)
            nontext = data.translate(trans)
    else:
        if isinstance(data, six.text_type):
            trans_args = ({ord(x): None for x in text_characters},)
        else:
            trans_args = (None, str(text_characters))
        nontext = data.translate(*trans_args)

    if float(len(nontext)) / len(data) > 0.30:
        return True
    return False


@jinja_filter('random_str')
def random(size=32):
    key = os.urandom(size)
    return to_unicode(base64.b64encode(key).replace(b'\n', b'')[:size])


@jinja_filter('contains_whitespace')
def contains_whitespace(text):
    '''
    Returns True if whitespaces discovered in `text`
    '''
    return any(x.isspace() for x in text)


def human_to_bytes(size):
    '''
    Given a human-readable byte string (2G, 30M)
    return the number of bytes. Will return 0 if the argument has
    unexpected form.
    '''
    if size[-1].upper() == 'B':
        size = size[:-1]
    sbytes = size[:-1]
    unit =size[-1].upper()
    if sbytes.isdigit():
        sbytes = int(sbytes)
        if unit == 'P':
            sbytes *= 1125899906842624
        elif unit == 'T':
            sbytes *= 1099511627776
        elif unit == 'G':
            sbytes *= 1073741824
        elif unit == 'M':
            sbytes *= 1048576
        elif unit == 'K':
            sbytes *= 1024
        else:
            sbytes = 0
    else:
        sbytes = 0
    return sbytes


def build_whitespace_split_regex(text):
    '''
    Create a regular expression at runtime which should match ignoring the
    addition or deletion of white space or line breaks, unless between commas

    Example:

    .. code-block:: python

        >>> import re
        >>> import salt.utils.stringutils
        >>> regex = salt.utils.stringutils.build_whitespace_split_regex(
        ...     """if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then"""
        ... )

        >>> regex
        '(?:[\\s]+)?if(?:[\\s]+)?\\[(?:[\\s]+)?\\-z(?:[\\s]+)?\\"\\$debian'
        '\\_chroot\\"(?:[\\s]+)?\\](?:[\\s]+)?\\&\\&(?:[\\s]+)?\\[(?:[\\s]+)?'
        '\\-r(?:[\\s]+)?\\/etc\\/debian\\_chroot(?:[\\s]+)?\\]\\;(?:[\\s]+)?'
        'then(?:[\\s]+)?'
        >>> re.search(
        ...     regex,
        ...     """if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then"""
        ... )
        <_sre.SRE_Match object at 0xb70639c0>
        >>>

    '''
    def __build_parts(text):
        lexer = shlex.shlex(text)
        lexer.whitespace_split = True
        lexer.commenters = ''
        if '\'' in text:
            lexer.quotes = '"'
        elif '"' in text:
            lexer.quotes = '\''
        return list(lexer)

    regex = r''
    for line in text.splitlines():
        parts = [re.escape(s) for s in __build_parts(line)]
        regex += r'(?:[\s]+)?{0}(?:[\s]+)?'.format(r'(?:[\s]+)?'.join(parts))
    return r'(?m)^{0}$'.format(regex)


def expr_match(line, expr):
    '''
    Checks whether or not the passed value matches the specified expression.
    Tries to match expr first as a glob using fnmatch.fnmatch(), and then tries
    to match expr as a regular expression. Originally designed to match minion
    IDs for whitelists/blacklists.

    Note that this also does exact matches, as fnmatch.fnmatch() will return
    ``True`` when no glob characters are used and the string is an exact match:

    .. code-block:: python

        >>> fnmatch.fnmatch('foo', 'foo')
        True
    '''
    try:
        if fnmatch.fnmatch(line, expr):
            return True
        try:
            if re.match(r'\A{0}\Z'.format(expr), line):
                return True
        except re.error:
            pass
    except TypeError:
        log.exception('Value %r or expression %r is not a string', line, expr)
    return False


@jinja_filter('check_whitelist_blacklist')
def check_whitelist_blacklist(value, whitelist=None, blacklist=None):
    '''
    Check a whitelist and/or blacklist to see if the value matches it

    value
        The item to check the whitelist and/or blacklist against.

    whitelist
        The list of items that are white-listed. If ``value`` is found
        in the whitelist, the function returns ``True``. Otherwise, it
        returns ``False``.

    blacklist
        The list of items that are black-listed. If ``value`` is found
        in the blacklist, the function returns ``False``. Otherwise, it
        returns ``True``.

    If both a whitelist and a blacklist are provided, value membership
    in the blacklist will be examined first. If the value is not found
    in the blacklist, then the whitelist is checked. If the value isn't
    found in the whitelist, the function returns ``False``.
    '''
    if blacklist:
        if isinstance(blacklist, six.string_types):
            blacklist = [blacklist]
        if not hasattr(blacklist, '__iter__'):
            raise TypeError(
                'Expecting iterable blacklist, but received {0} ({1})'.format(
                    type(blacklist).__name__, blacklist
                )
            )
    else:
        blacklist = []

    if whitelist:
        if isinstance(whitelist, six.string_types): 
            whitelist = [whitelist]
        if not hasattr(whitelist, '__iter__'):
            raise TypeError(
                'Expecting iterable whitelist, but received {0} ({1})'.format(
                    type(whitelist).__name__, whitelist
                )
            )
    else: 
        whitelist = []

    _blacklist_match = any(expr_match(value, expr) for expr in blacklist)
    _whitelist_match = any(expr_match(value, expr) for expr in whitelist)

    if blacklist and not whitelist:
        return not _blacklist_match
    elif whitelist and not blacklist:
        return _whitelist_match
    elif blacklist and whitelist:
        return not _blacklist_match and _whitelist_match
    else:
        return True