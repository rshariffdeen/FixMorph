#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from common import Definitions
from common.Utilities import get_code, error_exit, execute_command
from ast import Generator as ASTGenerator
from tools import Extractor, Oracle, Logger, Filter, Emitter


def transform_source_file(source_path, ast_script, output_file=None):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    with open(Definitions.FILE_AST_SCRIPT, "w") as script_file:
        for script_line in ast_script:
            if script_line != ast_script[-1]:
                script_line = script_line + "\n"
            script_file.write(script_line)

    transform_command = Definitions.PATCH_COMMAND + " -s=" + Definitions.PATCH_SIZE + \
         " -script=" + Definitions.FILE_AST_SCRIPT + " -source=" + source_path + \
         " -destination=" + source_path + " -target=" + source_path

    if source_path[-1] == 'h':
        transform_command += " --"
    if not output_file:
        output_file = Definitions.FILE_TEMP_TRANSFORM
    transform_command += " 2> output/errors > " + output_file
    if not output_file:
        transform_command += "; cp " + Definitions.FILE_TEMP_TRANSFORM + " " + source_path
    execute_command(transform_command)
