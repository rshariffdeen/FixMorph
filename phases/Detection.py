#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time, sys
from common.utilities import execute_command, error_exit, save_current_state, load_state
from common import definitions, values
from ast import Vector, Parser
from tools import Logger, Emitter, Detector, Writer, Generator, Reader

clone_list = dict()


def generate_target_vectors():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("Generating vector files for all code segments in Target")
    gen_header = False
    gen_source = False
    diff_file_list = values.original_diff_info.keys()
    for diff_file in diff_file_list:
        if ".c" in diff_file:
            gen_source = True
        elif ".h" in diff_file:
            gen_header = True
    if gen_header:
        Generator.generate_vectors("*\.h", definitions.FILE_FIND_RESULT, values.Project_C, diff_file_list)
    if gen_source:
        Generator.generate_vectors("*\.c", definitions.FILE_FIND_RESULT, values.Project_C, diff_file_list)


def find_clones():
    global clone_list
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    clone_list = Detector.detect_clones()
    # Values.c_file_list_to_patch = Detector.find_clone()


def load_values():
    if not values.original_diff_info:
        values.original_diff_info = Reader.read_json(definitions.FILE_DIFF_INFO)
        load_state()
    definitions.FILE_CLONE_INFO = definitions.DIRECTORY_OUTPUT + "/clone-info"
    definitions.FILE_VECTOR_MAP = definitions.DIRECTORY_OUTPUT + "/vector-map"
    definitions.FILE_AST_MAP = definitions.DIRECTORY_OUTPUT + "/ast-map"


def save_values():
    Writer.write_clone_list(clone_list, definitions.FILE_CLONE_INFO)
    Writer.write_as_json(values.VECTOR_MAP, definitions.FILE_VECTOR_MAP)
    values.file_list_to_patch = clone_list
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
        duration = format((time.time() - start_time) / 60, '.3f')
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        Emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def detect():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Clone Detection")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_DETECTION]:
        if not values.SKIP_VEC_GEN:
            safe_exec(generate_target_vectors, "generating vectors for target")
        safe_exec(find_clones, "finding clones in target")
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")
