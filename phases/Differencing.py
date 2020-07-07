#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
from common.Utilities import error_exit, save_current_state
from common import Definitions, Values
from tools import Logger, Emitter, Differ, Writer, Merger, Generator, Identifier

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
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("identifying modified definitions")
    Identifier.identify_definition_segment(diff_info, Values.Project_A)
    Emitter.sub_sub_title("identifying modified segments")
    Identifier.identify_code_segment(diff_info, Values.Project_A)


def analyse_source_diff():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global diff_info
    Differ.diff_files(Definitions.FILE_DIFF_ALL,
                      Definitions.FILE_DIFF_C,
                      Definitions.FILE_DIFF_H,
                      Definitions.FILE_EXCLUDED_EXTENSIONS_A,
                      Definitions.FILE_EXCLUDED_EXTENSIONS_B,
                      Definitions.FILE_EXCLUDED_EXTENSIONS,
                      Values.PATH_A,
                      Values.PATH_B)

    Emitter.sub_sub_title("analysing untracked files")
    untracked_file_list = Generator.generate_untracked_file_list(Definitions.FILE_EXCLUDED_EXTENSIONS, Values.PATH_A)
    Emitter.sub_sub_title("analysing header files")
    diff_h_file_list = Differ.diff_h_files(Definitions.FILE_DIFF_H, Values.PATH_A, untracked_file_list)
    Emitter.sub_sub_title("analysing C/CPP source files")
    diff_c_file_list = Differ.diff_c_files(Definitions.FILE_DIFF_C, Values.PATH_A, untracked_file_list)
    Emitter.sub_sub_title("analysing changed code lines")
    diff_info_c = dict()
    diff_info_h = dict()
    if diff_c_file_list:
        Emitter.normal("\t\tcollecting diff line information for C/CPP files")
        diff_info_c = Differ.diff_line(diff_c_file_list, Definitions.FILE_TEMP_DIFF)
    if diff_h_file_list:
        Emitter.normal("\t\tcollecting diff line information for header files")
        diff_info_h = Differ.diff_line(diff_h_file_list, Definitions.FILE_TEMP_DIFF)
    diff_info = Merger.merge_diff_info(diff_info_c, diff_info_h)


def analyse_ast_diff():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global diff_info
    if not diff_info:
        error_exit("no files modified in diff")
    diff_info = Differ.diff_ast(diff_info,
                                Values.PATH_A,
                                Values.PATH_B,
                                Definitions.FILE_AST_SCRIPT)


def safe_exec(function_def, title, *args):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    Emitter.sub_title(title)
    description = title[0].lower() + title[1:]
    try:
        Logger.information("running " + str(function_def))
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Emitter.error("Crash during " + description + ", after " + duration + " seconds.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def load_values():
    global FILE_DIFF_C, FILE_DIFF_H, FILE_DIFF_ALL
    global FILE_AST_SCRIPT, FILE_AST_DIFF_ERROR
    global FILE_EXCLUDED_EXTENSIONS, FILE_EXCLUDED_EXTENSIONS_A, FILE_EXCLUDED_EXTENSIONS_B
    Definitions.FILE_AST_SCRIPT = Definitions.DIRECTORY_OUTPUT + "/ast-script-temp"
    Definitions.FILE_DIFF_INFO = Definitions.DIRECTORY_OUTPUT + "/diff-info"
    Definitions.FILE_TEMP_DIFF = Definitions.DIRECTORY_OUTPUT + "/temp_diff"
    Definitions.FILE_AST_DIFF_ERROR = Definitions.DIRECTORY_OUTPUT + "/errors_ast_diff"
    Definitions.FILE_N_COUNT = Definitions.DIRECTORY_OUTPUT + "/n-count"


def save_values():
    Writer.write_as_json(diff_info, Definitions.FILE_DIFF_INFO)
    save_current_state()


def diff():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Analysing Changes")
    load_values()
    if not Values.SKIP_DIFF:
        safe_exec(analyse_source_diff, "analysing source diff")
        safe_exec(segment_code, "segmentation of code")
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")



