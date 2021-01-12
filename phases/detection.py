#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time, sys
from common.utilities import execute_command, error_exit, save_current_state, load_state
from common import definitions, values
from ast import ast_vector, ast_parser
from tools import logger, emitter, detector, writer, generator, reader

segment_clone_list = dict()
file_clone_list = dict()


def generate_target_vectors():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.sub_sub_title("Generating vector files for all code segments in Target")
    gen_header = False
    gen_source = False
    diff_file_list = values.original_diff_info.keys()
    for diff_file in diff_file_list:
        if ".c" in diff_file:
            gen_source = True
        elif ".h" in diff_file:
            gen_header = True
    if gen_header:
        generator.generate_vectors("*\.h", definitions.FILE_FIND_RESULT, values.Project_C, diff_file_list)
    if gen_source:
        generator.generate_vectors("*\.c", definitions.FILE_FIND_RESULT, values.Project_C, diff_file_list)


def find_segment_clones():
    global segment_clone_list
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    segment_clone_list = detector.detect_segment_clones()
    # Values.c_file_list_to_patch = Detector.find_clone()


def find_file_clones():
    global file_clone_list
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    file_clone_list = detector.detect_file_clones(values.original_diff_info)
    values.VECTOR_MAP = file_clone_list
    # Values.c_file_list_to_patch = Detector.find_clone()


def load_values():
    if not values.original_diff_info:
        values.original_diff_info = reader.read_json(definitions.FILE_DIFF_INFO)
        load_state()
    definitions.FILE_CLONE_INFO = definitions.DIRECTORY_OUTPUT + "/clone-info"
    definitions.FILE_VECTOR_MAP = definitions.DIRECTORY_OUTPUT + "/vector-map"
    definitions.FILE_AST_MAP = definitions.DIRECTORY_OUTPUT + "/ast-map"
    definitions.FILE_VECTOR_MAP = definitions.DIRECTORY_OUTPUT + "/source-map"


def save_values():
    writer.write_clone_list(segment_clone_list, definitions.FILE_CLONE_INFO)
    writer.write_as_json(values.VECTOR_MAP, definitions.FILE_VECTOR_MAP)
    writer.write_as_json(values.SOURCE_MAP, definitions.FILE_SOURCE_MAP)
    if values.DEFAULT_OPERATION_MODE in [0, 3]:
        values.file_list_to_patch = segment_clone_list
    else:
        values.file_list_to_patch = file_clone_list
    save_current_state()


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


def start():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.title("Clone Detection")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_DETECTION]:
        if values.DEFAULT_OPERATION_MODE == 0:
            if not values.SKIP_VEC_GEN:
                safe_exec(generate_target_vectors, "generating vectors for target")
            safe_exec(find_segment_clones, "finding segment clones in target")
        else:
            safe_exec(find_file_clones, "finding file clones in target")
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")
