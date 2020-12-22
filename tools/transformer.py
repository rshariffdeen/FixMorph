#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from common import definitions, values
from common.utilities import get_code, error_exit, execute_command
from ast import ast_generator as ASTGenerator
from tools import extractor, oracle, logger, filter, emitter


def transform_source_file(source_path, ast_script, output_file=None, ast_script_path=definitions.FILE_AST_SCRIPT):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    with open(ast_script_path, "w") as script_file:
        for script_line in ast_script:
            if script_line != ast_script[-1]:
                script_line = script_line + "\n"
            script_file.write(script_line)

    transform_command = definitions.PATCH_COMMAND + " -s=" + definitions.PATCH_SIZE
    if values.CONF_PATH_A in source_path or values.CONF_PATH_B in source_path:
        if values.DONOR_REQUIRE_MACRO:
            transform_command += " " + values.DONOR_PRE_PROCESS_MACRO + " "
    if values.CONF_PATH_C in source_path or values.Project_D.path in source_path:
        if values.TARGET_REQUIRE_MACRO:
            transform_command += " " + values.TARGET_PRE_PROCESS_MACRO + " "

    transform_command += " -script=" + ast_script_path + " -source=" + source_path + \
         " -destination=" + source_path + " -target=" + source_path + " -map=" + definitions.FILE_NAMESPACE_MAP

    if source_path[-1] == 'h':
        transform_command += " --"
    if not output_file:
        output_file = definitions.FILE_TEMP_TRANSFORM
    transform_command += " 2> output/errors > " + output_file
    if not output_file:
        transform_command += "; cp " + definitions.FILE_TEMP_TRANSFORM + " " + source_path
    execute_command(transform_command)
