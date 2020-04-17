#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import sys
import os
import io
import json
from git import Repo
from common.Utilities import execute_command, error_exit, save_current_state, load_state
from common import Definitions, Values
from ast import Vector, Parser
import difflib
from tools import Logger, Emitter, Detector, Writer, Generator, Reader, Differ, Merger

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
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Differ.diff_files(Definitions.FILE_DIFF_ALL,
                      Definitions.FILE_DIFF_C,
                      Definitions.FILE_DIFF_H,
                      Definitions.FILE_EXCLUDED_EXTENSIONS_A,
                      Definitions.FILE_EXCLUDED_EXTENSIONS_B,
                      Definitions.FILE_EXCLUDED_EXTENSIONS,
                      path_a,
                      path_b)

    Emitter.sub_sub_title("analysing untracked files")
    untracked_file_list = Generator.generate_untracked_file_list(Definitions.FILE_EXCLUDED_EXTENSIONS)
    Emitter.sub_sub_title("analysing header files")
    diff_h_file_list = Differ.diff_h_files(Definitions.FILE_DIFF_H, path_a, untracked_file_list)
    Emitter.sub_sub_title("analysing C/CPP source files")
    diff_c_file_list = Differ.diff_c_files(Definitions.FILE_DIFF_C, path_b, untracked_file_list)
    Emitter.sub_sub_title("analysing changed code lines")
    diff_info_c = Differ.diff_line(diff_c_file_list, Definitions.FILE_TEMP_DIFF)
    diff_info_h = Differ.diff_line(diff_h_file_list, Definitions.FILE_TEMP_DIFF)
    diff_info = Merger.merge_diff_info(diff_info_c, diff_info_h)
    return diff_info


def analyse_ast_diff(path_a, path_b, diff_info):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not diff_info:
        error_exit("no files modified in diff")
    updated_diff_info = Differ.diff_ast(diff_info,
                                        path_a,
                                        path_b,
                                        Definitions.FILE_AST_SCRIPT)
    return updated_diff_info


def load_values():
    global FILE_DIFF_C, FILE_DIFF_H, FILE_DIFF_ALL
    global FILE_AST_SCRIPT, FILE_AST_DIFF_ERROR
    global FILE_EXCLUDED_EXTENSIONS, FILE_EXCLUDED_EXTENSIONS_A, FILE_EXCLUDED_EXTENSIONS_B
    Definitions.FILE_ORIG_DIFF_INFO = Definitions.DIRECTORY_OUTPUT + "/orig-diff-info"
    Definitions.FILE_PORT_DIFF_INFO = Definitions.DIRECTORY_OUTPUT + "/port-diff-info"
    Definitions.FILE_TRANSPLANT_DIFF_INFO = Definitions.DIRECTORY_OUTPUT + "/transplant-diff-info"
    Definitions.FILE_ORIG_DIFF = Definitions.DIRECTORY_OUTPUT + "/orig-diff"
    Definitions.FILE_PORT_DIFF = Definitions.DIRECTORY_OUTPUT + "/port-diff"
    Definitions.FILE_TRANSPLANT_DIFF = Definitions.DIRECTORY_OUTPUT + "/transplant-diff"


def save_values():
    Writer.write_as_json(ported_diff_info, Definitions.FILE_PORT_DIFF_INFO)
    Writer.write_as_json(original_diff_info, Definitions.FILE_ORIG_DIFF_INFO)
    Writer.write_as_json(transplanted_diff_info, Definitions.FILE_TRANSPLANT_DIFF_INFO)
    file_list_a = set()
    file_list_c = set()
    for path_a in original_diff_info:
        path_a = path_a.split(":")[0]
        file_list_a.add(path_a)
    for path_a in file_list_a:
        path_b = path_a.replace(Values.Project_A.path, Values.Project_B.path)
        diff_command = "diff -ENZBbwr " + path_a + " " + path_b + " >> " + Definitions.FILE_ORIG_DIFF
        execute_command(diff_command)
    for path_c in ported_diff_info:
        path_c = path_c.split(":")[0]
        file_list_c.add(path_c)
    for path_c in file_list_c:
        path_e = path_c.replace(Values.Project_C.path, Values.Project_E.path)
        diff_command = "diff -ENZBbwr " + path_c + " " + path_e + " >> " + Definitions.FILE_PORT_DIFF
        execute_command(diff_command)
    if not Values.ONLY_ANALYSE:
        for path_c in file_list_c:
            path_d = path_c.replace(Values.Project_C.path, Values.Project_D.path)
            diff_command = "diff -ENZBbwr " + path_c + " " + path_d + " >> " + Definitions.FILE_TRANSPLANT_DIFF
            execute_command(diff_command)
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


def compare():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global original_diff_info, ported_diff_info, transplanted_diff_info
    Emitter.title("Comparison with Manual Porting")
    load_values()

    if not Values.SKIP_COMPARE:
        if not Values.PATH_E:
            error_exit("Path E is missing in configuration")

        ported_diff_info = safe_exec(analyse_source_diff, "analysing source diff of Ported Patch",
                                     Values.PATH_C, Values.PATH_E)
        ported_diff_info = safe_exec(analyse_ast_diff, "analysing ast diff of Ported Patch",
                                     Values.PATH_C, Values.PATH_E, ported_diff_info)

        transplanted_diff_info = safe_exec(analyse_source_diff, "analysing source diff of Transplanted Patch",
                                         Values.PATH_C, Values.Project_D.path)
        transplanted_diff_info = safe_exec(analyse_ast_diff, "analysing ast diff of Transplanted Patch",
                                         Values.PATH_C, Values.Project_D.path, transplanted_diff_info)

        print(ported_diff_info)
        print(transplanted_diff_info)

        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")