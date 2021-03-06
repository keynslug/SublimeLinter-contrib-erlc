###
# Erlang linter plugin for SublimeLinter3
# Uses erlc, make sure it is in your PATH
#
# Copyright (C) 2014  Clement 'cmc' Rey <cr.rey.clement@gmail.com>
#
# MIT License
###

"""This module exports the Erlc plugin class."""

import os
import glob
import re
from SublimeLinter.lint import Linter, util


def erlc():
    candidates = ["/usr/local/bin/erlc", "/opt/local/bin/erlc"]
    for p in candidates:
        if os.popen("which " + p).read():
            return p
    return "erlc"


class Erlc(Linter):

    """Provides an interface to erlc."""

    syntax = re.compile(r".*erlang$", re.I)

    executable = erlc()
    tempfile_suffix = "erl"

    # ERROR FORMAT # <file>:<line>: [Warning:|] <message> #
    regex = (
        r".+:(?P<line>\d+):"
        r"(?:(?P<warning>\sWarning:\s)|(?P<error>\s))"
        r"+(?P<message>.+)"
    )

    error_stream = util.STREAM_STDOUT

    defaults = {
        "include_dirs": []
    }

    DEFAULT_COMPILER_OPTS = [
        "+warn_obsolete_guard",
        "+warn_unused_import",
        "+warn_shadow_vars",
        "+warn_export_vars",
        "+strong_validation",
        "+report"
    ]

    DEFAULT_INCLUDE_DIRS = [
        "include",
        "src"
    ]

    DEFAULT_CODE_PATH_DIRS = [
        "ebin"
    ]

    DEFAULT_DEPENDENCY_DIRS = [
        "apps",
        "deps",
        "_build/{profile}/lib"
    ]

    def get_lint_args(self, view):
        settings = self.get_view_settings()
        src_dir = os.path.dirname(view.file_name())
        project_dir = os.path.dirname(src_dir)

        result = []

        for compiler_opt in self.DEFAULT_COMPILER_OPTS:
            result.append(compiler_opt)

        for symbol_opt in settings.get('define_symbols', []):
            result.append("-D" + symbol_opt)

        for include_dir in self.DEFAULT_INCLUDE_DIRS:
            include_path = self.find_file_or_dir(include_dir, view)
            if include_path:
                result.extend(["-I", include_path])

        for code_path_dir in self.DEFAULT_CODE_PATH_DIRS:
            code_path = self.find_file_or_dir(code_path_dir, view)
            if code_path:
                result.extend(["-pa", code_path])

        # Search for addtional include and code paths in depedencies
        path_params = {'profile': settings.get('build_profile', 'default')}
        for dependecy_root_dir in self.DEFAULT_DEPENDENCY_DIRS:
            dependecy_root = self.find_file_or_dir(dependecy_root_dir.format(**path_params), view)
            if dependecy_root:
                result.extend(["-I", dependecy_root])
                for code_path_dir in glob.glob(os.path.join(dependecy_root, "*", "ebin")):
                    result.extend(["-pa", os.path.abspath(code_path_dir)])

        return result

    def find_file_or_dir(self, filename, view):
        '''Find a file or directory with the given name, starting in the view's
           directory, then ascending the file hierarchy up to root.'''
        path = view.file_name()

        # quit if the view is temporary
        if not path:
            return None

        dirname = os.path.dirname(path)

        while True:
            path = os.path.join(dirname, filename)

            if os.path.exists(path):
                return path

            # if we hit root, quit
            parent = os.path.dirname(dirname)

            if parent == dirname:
                return None
            else:
                dirname = parent

    def cmd(self):
        """
        return the command line to execute.

        this func is overridden so we can handle included directories.
        """

        command = [self.executable_path]
        command.extend(self.get_lint_args(self.view))

        settings = self.get_view_settings()
        dirs = settings.get('include_dirs', [])

        for d in dirs:
            command.extend(["-I", d])

        return command
