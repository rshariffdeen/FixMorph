#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time, sys
from common.Utilities import execute_command, error_exit, find_files
from common import Definitions, Values
from ast import Vector, Parser
from tools import Logger, Emitter, Detector, Differ, Generator


diff_info = dict()


def generate_vectors_donor():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("Generating vector files for affected functions in Donor")

    Generator.generate_vectors("*\.h", Definitions.FILE_DIFF_H, Values.Project_A)
    Generator.generate_vectors("*\.c", Definitions.FILE_DIFF_C, Values.Project_A)


def generate_vectors_target():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("Generating vector files for all functions in Target")
    Generator.generate_vectors("*\.h", Definitions.FILE_DIFF_H, Values.Project_C)
    Generator.generate_vectors("*\.c", Definitions.FILE_DIFF_C, Values.Project_C)


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


def detect():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Clone Detection")

    safe_exec(generate_vectors_target, "generating vectors for target")

    # safe_exec(analyse_ast_diff, "analysing ast diff")
    #
    #
    #
    #
    # safe_exec(generate_diff, "search for affected functions")
    # # Generates vectors for all functions in Pc
    # safe_exec(generate_vectors, "vector generation for all functions in Pc")
    # # Pairwise vector comparison for matching
    # Definitions.header_file_list_to_patch = safe_exec(clone_detection_header_files, "clone detection for header files")
    # Definitions.c_file_list_to_patch = safe_exec(clone_detection_for_c_files, "clone detection for C files")
    #
