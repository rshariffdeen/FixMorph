#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
from common.utilities import error_exit, save_current_state, clear_values
from common import definitions, values
from tools import logger, emitter, differ, writer, merger, generator, identifier

FILE_EXCLUDED_EXTENSIONS = ""
FILE_EXCLUDED_EXTENSIONS_A = ""
FILE_EXCLUDED_EXTENSIONS_B = ""
FILE_DIFF_C = ""
FILE_DIFF_H = ""
FILE_DIFF_ALL = ""
FILE_AST_SCRIPT = ""
FILE_AST_DIFF_ERROR = ""

diff_info = dict()


def segment_code():
    global diff_info
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.sub_sub_title("identifying modified definitions")
    identifier.identify_definition_segment(diff_info, values.Project_A)
    emitter.sub_sub_title("identifying modified segments")
    identifier.identify_code_segment(diff_info, values.Project_A, definitions.FILE_ORIG_N)


def analyse_source_diff():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global diff_info
    clear_values(values.Project_A)
    differ.diff_files(definitions.FILE_DIFF_ALL,
                      definitions.FILE_DIFF_C,
                      definitions.FILE_DIFF_H,
                      definitions.FILE_EXCLUDED_EXTENSIONS_A,
                      definitions.FILE_EXCLUDED_EXTENSIONS_B,
                      definitions.FILE_EXCLUDED_EXTENSIONS,
                      values.CONF_PATH_A,
                      values.CONF_PATH_B)

    emitter.sub_sub_title("analysing untracked files")
    untracked_file_list = generator.generate_untracked_file_list(definitions.FILE_EXCLUDED_EXTENSIONS, values.CONF_PATH_A)
    emitter.sub_sub_title("analysing header files")
    diff_h_file_list = differ.diff_h_files(definitions.FILE_DIFF_H, values.CONF_PATH_A, untracked_file_list)
    emitter.sub_sub_title("analysing C/CPP source files")
    diff_c_file_list = differ.diff_c_files(definitions.FILE_DIFF_C, values.CONF_PATH_A, untracked_file_list)
    emitter.sub_sub_title("analysing changed code lines")
    diff_info_c = dict()
    diff_info_h = dict()
    if diff_c_file_list:
        emitter.normal("\t\tcollecting diff line information for C/CPP files")
        diff_info_c = differ.diff_line(diff_c_file_list, definitions.FILE_TEMP_DIFF)
    if diff_h_file_list:
        emitter.normal("\t\tcollecting diff line information for header files")
        diff_info_h = differ.diff_line(diff_h_file_list, definitions.FILE_TEMP_DIFF)
    diff_info = merger.merge_diff_info(diff_info_c, diff_info_h)


def analyse_ast_diff():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global diff_info
    if not diff_info:
        error_exit("no files modified in diff")
    diff_info = differ.diff_ast(diff_info,
                                values.CONF_PATH_A,
                                values.CONF_PATH_B,
                                definitions.FILE_AST_SCRIPT)


def safe_exec(function_def, title, *args):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    emitter.sub_title(title)
    description = title[0].lower() + title[1:]
    try:
        logger.information("running " + str(function_def))
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def load_values():
    global FILE_DIFF_C, FILE_DIFF_H, FILE_DIFF_ALL
    global FILE_AST_SCRIPT, FILE_AST_DIFF_ERROR
    global FILE_EXCLUDED_EXTENSIONS, FILE_EXCLUDED_EXTENSIONS_A, FILE_EXCLUDED_EXTENSIONS_B
    definitions.FILE_AST_SCRIPT = definitions.DIRECTORY_OUTPUT + "/ast-script-temp"
    definitions.FILE_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/diff-info"
    definitions.FILE_TEMP_DIFF = definitions.DIRECTORY_OUTPUT + "/temp_diff"
    definitions.FILE_AST_DIFF_ERROR = definitions.DIRECTORY_OUTPUT + "/errors_ast_diff"
    definitions.FILE_ORIG_N = definitions.DIRECTORY_OUTPUT + "/n-orig"


def save_values():
    writer.write_as_json(diff_info, definitions.FILE_DIFF_INFO)
    save_current_state()


def diff():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.title("Analysing Changes")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_DIFF]:
        safe_exec(analyse_source_diff, "analysing source diff")
        safe_exec(segment_code, "segmentation of code")
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")



