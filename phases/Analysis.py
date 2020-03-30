#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time, sys
from common.Utilities import execute_command, error_exit, save_current_state, load_state
from common import Definitions, Values
from ast import Vector, Parser
from tools import Logger, Emitter, Detector, Writer, Generator, Reader

FILE_EXCLUDED_EXTENSIONS = ""
FILE_EXCLUDED_EXTENSIONS_A = ""
FILE_EXCLUDED_EXTENSIONS_B = ""
FILE_DIFF_C = ""
FILE_DIFF_H = ""
FILE_DIFF_ALL = ""
FILE_AST_SCRIPT = ""
FILE_AST_DIFF_ERROR = ""

ported_diff_info = dict()


def find_clones():
    global clone_list
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    clone_list = Detector.detect_clones()
    # Values.c_file_list_to_patch = Detector.find_clone()


def load_values():
    global FILE_DIFF_C, FILE_DIFF_H, FILE_DIFF_ALL
    global FILE_AST_SCRIPT, FILE_AST_DIFF_ERROR
    global FILE_EXCLUDED_EXTENSIONS, FILE_EXCLUDED_EXTENSIONS_A, FILE_EXCLUDED_EXTENSIONS_B

    if not Values.original_diff_info:
        Values.original_diff_info = Reader.read_json(Definitions.FILE_ORIG_DIFF_INFO)
        load_state()

    Definitions.FILE_PORT_DIFF_INFO = Definitions.DIRECTORY_OUTPUT + "/port-diff-info"


def save_values():
    Writer.write_as_json(ported_diff_info, Definitions.FILE_PORT_DIFF_INFO)
    save_current_state()


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


def analyse():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Ported Patch Analysis")
    load_values()
    if not Values.SKIP_ANALYSE:
        if not Values.SKIP_VEC_GEN:
            safe_exec(generate_target_vectors, "generating vectors for target")
        safe_exec(find_clones, "finding clones in target")
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")
