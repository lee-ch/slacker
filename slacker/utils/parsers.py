# -*- coding: utf-8 -*-
'''
slacker.utils.parsers

This is the CLI parser for all of slackers CLI tools
'''

# Import python libs
from __future__ import print_function, absolute_import, unicode_literals
import os
import sys
import signal
import getpass
import logging
import optparse
import traceback
from functools import partial

# Import slacker libs
import slacker.utils.files
import slacker.utils.data
import slacker.version as version

from slacker.defaults import DEFAULT_PATH_DELIM
from slacker.ext import six
from slacker.ext.six.moves import range

logger = logging.getLogger(__name__)


def _sorted(mixins_or_funcs):
    return sorted(
        mixins_or_funcs, key=lambda mf: getattr(mf, '_mixin_prio_', 1000)
    )


class MixInMeta(type):
    # This attribute doesn't do anything, but if you need to specify
    # an order or dependency within the mix-ins, define the attribute
    # in the MixIn
    _mixin_prio_ = 0

    def __new__(mcs, name, bases, attrs):
        instance = super(MixInMeta, mcs).__new__(mcs, name, bases, attrs)
        if not hasattr(instance, '_mixin_setup'):
            raise RuntimeError(
                'Don\'t subclass {0} in {1} if you\'re not going '
                'to use it as a slacker parser mix-in'.format(mcs.__name__, name)
            )
        return instance


class OptionParserMeta(MixInMeta):
    def __new__(mcs, name, bases, attrs):
        instance = super(OptionParserMeta, mcs).__new__(mcs,
                                                        name,
                                                        bases,
                                                        attrs)
        if not hasattr(instance, '_mixin_setup_funcs'):
            instance._mixin_setup_funcs = []
        if not hasattr(instance, '_mixin_process_funcs'):
            instance._mixin_process_funcs = []
        if not hasattr(instance, '_mixin_after_parsed_funcs'):
            instance._mixin_after_parsed_funcs = []
        if not hasattr(instance, '_mixin_before_exit_funcs'):
            instance._mixin_before_exit_funcs = []

        for base in _sorted(bases + (instance,)):
            func = getattr(base, '_mixin_setup', None)
            if func is not None and func not in instance._mixin_setup_funcs:
                instance._mixin_setup_funcs.append(func)
            
            func = getattr(base, '_mixin_after_parsed_funcs', None)
            if func is not None and func not in instance._mixin_after_parsed_funcs:
                instance._mixin_after_parsed_funcs.append(func)

            for func in dir(base):
                if not func.startswith('process_'):
                    continue

                func = getattr(base, func)
                if getattr(func, '_mixin_prio_', None) is not None:
                    # Attribute already set, don't override it
                    continue

                if six.PY2:
                    func.__func__._mixin_prio_ = getattr(
                        base, '_mixin_prio_', 1000
                    )
                else:
                    func._mixin_prio_ = getattr(
                        base, '_mixin_prio_', 1000
                    )

        return instance


class CustomOption(optparse.Option, object):
    def take_action(self, action, dest, *args, **kwargs):
        # see https://github.com/python/cpython/blob/master/Lib/optparse.py#L786
        self.explicit = True
        return optparse.Option.take_action(self, action, dest, *args, **kwargs)


class OptionParser(optparse.OptionParser, object):
    VERSION = version.__version__

    usage = '%prog [options]'

    epilog = ('You can find additional help about %prog issuing "man %prog"')
    description = None

    # Private attributes
    _mixin_prio_ = 100

    # Setup multiprocessing logging queue listener
    _setup_mp_logging_listener_ = False

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('version', '%prog {0}'.format(self.VERSION))
        kwargs.setdefault('usage', self.usage)
        if self.description:
            kwargs.setdefault('description', self.description)

        if self.epilog:
            kwargs.setdefault('epilog', self.epilog)

        kwargs.setdefault('option_class', CustomOption)

        if self.epilog and '%prog' in self.epilog:
            self.epilog = self.epilog.replace('%prog', self.get_prog_name())

    def add_option_group(self, *args, **kwargs):
        option_group = optparse.OptionParser.add_option_group(self, *args, **kwargs)
        option_group.option_class = CustomOption
        return option_group

    def parse_args(self, args=None, values=None):
        options, args = optparse.OptionParser.parse_args(self, args, values)
        if 'args_stdin' in options.__dict__ and options.args_stdin is True:
            # Read additional options and/or arguments from stdin and combine
            # them with the options and arguments from the CLI
            new_inargs = sys.stdin.readlines()
            new_inargs = [arg.rstrip('\r\n') for arg in new_inargs]
            new_options, new_args = optparse.OptionParser.parse_args(
                self,
                new_inargs)
            options.__dict__.update(new_options.__dict__)
            args.extend(new_args)

        if options.version_report:
            self.print_versions_report()

        self.options, self.args = options, args

        # Get some proper sys.stderr logging as soon as possible
        # This logging handler will be removed once the proper console or
        # logfile logging is setup.
        temp_log_level = getattr(self.options, 'log_level', None)
        log.setup_temp_logger(
            'error' if temp_log_level is None else temp_log_level
        )

        # Gather and run the process_<option> functions in the proper order
        process_option_funcs = []
        for option_key in options.__dict__:
            process_option_func = getattr(
                self, 'process_{0}'.format(option_key), None
            )
            if process_option_func is not None:
                process_option_funcs.append(process_option_func)

        for process_option_func in _sorted(process_option_funcs):
            try:
                process_option_func()
            except Exception as err:
                logger.exception(err)
                self.error(
                    'Error while processing {0}: {1}'.format(
                        process_option_func, traceback.format_exc(err)
                    )
                )

        for mixin_after_parsed_func in self._mixin_after_parsed_funcs:
            try:
                mixin_after_parsed_func(self)
            except Exception as err:
                logger.exception(err)
                self.error(
                    'Error while processing {0}: {1}'.format(
                        mixin_after_parsed_func, traceback.format_exc(err)
                    )
                )

        if self.config.get('conf_file', None) is not None:
            logger.debug(
                'Configuration file path: %s',
                self.config['conf_file']
            )

        # Retain the standard behavior of optparse to return options and args
        return options, args

    def _populate_option_list(self, option_list, add_help=True):
        optparse.OptionParser._populate_option_list(
            self, option_list, add_help=add_help
        )
        for mixin_setup_func in self._mixin_setup_funcs:
            mixin_setup_func(self)

    def _add_version_option(self):
        optparse.OptionParser._add_version_option(self)
        self.add_option(
            '--versions-report',
            '-V',
            action='store_true',
            help='Show program\'s dependencies version number and exit.'
        )

    def print_versions_report(self, file=sys.stdout):
        print('\n'.join(version.version_report()), file=file)
        self.exit(slacker.defaults.exitcodes.EX_OK)

    