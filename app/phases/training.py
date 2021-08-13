#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import sys
import os
from app.common.utilities import execute_command, error_exit, save_current_state, clear_values
from app.common import definitions, values
from app.tools import identifier, merger
from app.tools import generator, differ, emitter, writer, logger

FILE_EXCLUDED_EXTENSIONS = ""
FILE_EXCLUDED_EXTENSIONS_A = ""
FILE_EXCLUDED_EXTENSIONS_B = ""
FILE_DIFF_C = ""
FILE_DIFF_H = ""
FILE_DIFF_ALL = ""
FILE_AST_SCRIPT = ""
FILE_AST_DIFF_ERROR = ""

ported_diff_info = dict()
original_diff_info = dict()
transplanted_diff_info = dict()


def analyse_source_diff(path_a, path_b):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    differ.diff_files(definitions.FILE_DIFF_ALL,
                      definitions.FILE_DIFF_C,
                      definitions.FILE_DIFF_H,
                      definitions.FILE_EXCLUDED_EXTENSIONS_A,
                      definitions.FILE_EXCLUDED_EXTENSIONS_B,
                      definitions.FILE_EXCLUDED_EXTENSIONS,
                      path_a,
                      path_b)

    emitter.sub_sub_title("analysing untracked files")
    untracked_file_list = generator.generate_untracked_file_list(definitions.FILE_EXCLUDED_EXTENSIONS, path_a)
    emitter.sub_sub_title("analysing header files")
    diff_h_file_list = differ.diff_h_files(definitions.FILE_DIFF_H, path_a, untracked_file_list)
    emitter.sub_sub_title("analysing C/CPP source files")
    diff_c_file_list = differ.diff_c_files(definitions.FILE_DIFF_C, path_b, untracked_file_list)
    emitter.sub_sub_title("analysing changed code lines")
    diff_info_c = differ.diff_line(diff_c_file_list, definitions.FILE_TEMP_DIFF)
    diff_info_h = differ.diff_line(diff_h_file_list, definitions.FILE_TEMP_DIFF)
    diff_info = merger.merge_diff_info(diff_info_c, diff_info_h)
    return diff_info


def analyse_ast_diff(path_a, path_b, diff_info):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not diff_info:
        error_exit("no files modified in diff")
    updated_diff_info = differ.diff_ast(diff_info,
                                        path_a,
                                        path_b,
                                        definitions.FILE_AST_SCRIPT)
    return updated_diff_info


def load_values():
    global FILE_DIFF_C, FILE_DIFF_H, FILE_DIFF_ALL
    global FILE_AST_SCRIPT, FILE_AST_DIFF_ERROR
    global FILE_EXCLUDED_EXTENSIONS, FILE_EXCLUDED_EXTENSIONS_A, FILE_EXCLUDED_EXTENSIONS_B
    definitions.FILE_ORIG_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/orig-diff-info"
    definitions.FILE_PORT_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/port-diff-info"
    definitions.FILE_TRANSPLANT_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/transplant-diff-info"
    definitions.FILE_ORIG_DIFF = definitions.DIRECTORY_OUTPUT + "/orig-diff"
    definitions.FILE_PORT_DIFF = definitions.DIRECTORY_OUTPUT + "/port-diff"
    definitions.FILE_COMPARISON_RESULT = definitions.DIRECTORY_OUTPUT + "/comparison-result"
    definitions.FILE_TRANSPLANT_DIFF = definitions.DIRECTORY_OUTPUT + "/transplant-diff"
    definitions.FILE_PORT_N = definitions.DIRECTORY_OUTPUT + "/n-port"
    definitions.FILE_TRANS_N = definitions.DIRECTORY_OUTPUT + "/n-trans"


def save_values():
    global ported_diff_info, transplanted_diff_info
    writer.write_as_json(ported_diff_info, definitions.FILE_PORT_DIFF_INFO)
    writer.write_as_json(transplanted_diff_info, definitions.FILE_TRANSPLANT_DIFF_INFO)
    open(definitions.FILE_PORT_DIFF, 'w').close()
    open(definitions.FILE_TRANSPLANT_DIFF, 'w').close()
    
    file_list_c = set()
    for path_c in ported_diff_info:
        path_c = path_c.split(":")[0]
        file_list_c.add(path_c)

    for path_c in file_list_c:
        path_e = path_c.replace(values.Project_C.path, values.Project_E.path)
        diff_command = "diff -ENZBbwr"
        if values.DEFAULT_OUTPUT_FORMAT == "unified":
            diff_command += " -u "
        diff_command += path_c + " " + path_e + " >> " + definitions.FILE_PORT_DIFF
        execute_command(diff_command)
    for path_c in file_list_c:
        path_d = path_c.replace(values.Project_C.path, values.Project_D.path)
        diff_command = "diff -ENZBbwr"
        if values.DEFAULT_OUTPUT_FORMAT == "unified":
            diff_command += " -u "
        diff_command += path_c + " " + path_d + " >> " + definitions.FILE_TRANSPLANT_DIFF
        execute_command(diff_command)
        
    is_identical = True

    for path_c in file_list_c:
        temp_diff_file = definitions.DIRECTORY_TMP + "/tmp-ast-diff"
        path_e = path_c.replace(values.Project_C.path, values.Project_E.path)
        path_d = path_c.replace(values.Project_C.path, values.Project_D.path)
        diff_command = "diff -bwZEB " + path_d + " " + path_e + " > " + temp_diff_file
        execute_command(diff_command)
        if os.stat(temp_diff_file).st_size != 0:
            ast_diff_command = "crochet-diff " + path_d + " " + path_e + " > " + temp_diff_file
            execute_command(ast_diff_command)
            if os.stat(temp_diff_file).st_size != 0:
                is_identical = False
                break

    with open(definitions.FILE_COMPARISON_RESULT, 'w') as result_file:
        if is_identical:
            result = "IDENTICAL"
        else:
            result = "DIFFERENT"
        result_file.write(result)
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


def segment_code(diff_info, project, out_file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.sub_sub_title("identifying modified definitions")
    identifier.identify_definition_segment(diff_info, project)
    emitter.sub_sub_title("identifying modified segments")
    identifier.identify_code_segment(diff_info, project, out_file_path)


def start():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global ported_diff_info, original_diff_info
    emitter.title("Training from Evolution History")
    load_values()

    if values.PHASE_SETTING[definitions.PHASE_TRAINING]:
        clear_values(values.Project_C)
        original_diff_info = safe_exec(analyse_source_diff, "analysing source diff of Original Patch",
                                           values.CONF_PATH_A, values.CONF_PATH_B)
        segment_code(original_diff_info, values.Project_A, definitions.FILE_ORIG_N)
        ported_diff_info = safe_exec(analyse_source_diff, "analysing source diff of Ported Patch",
                                     values.CONF_PATH_C, values.CONF_PATH_E)
        segment_code(ported_diff_info, values.Project_C, definitions.FILE_PORT_N)

        if not values.ANALYSE_N:
            save_values()
    else:
        emitter.special("\n\t-skipping this phase-")

