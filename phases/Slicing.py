#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
from common.Utilities import error_exit
from common import Values
from tools import Logger, Emitter, Slicer


def slice_code(file_list_to_patch):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())

    Emitter.sub_sub_title("slicing unrelated segments")

    for (vec_path_a, vec_path_c, var_map) in file_list_to_patch:
        segment_code = vec_path_a.split("_")[0]
        try:
            split_regex = "." + segment_code + "_"
            vector_source_a, vector_name_a = vec_path_a.split(split_regex)
            vector_source_b = vector_source_a.replace(Values.Project_A.path, Values.Project_B.path)
            vector_source_c, vector_name_c = vec_path_c.split(split_regex)

            vector_name_b = vector_name_a.replace(Values.PATH_A, Values.PATH_B)
            vector_name_d = vector_name_a.replace(Values.PATH_C, Values.Project_D.path)
            vector_source_d = vector_source_c.replace(Values.PATH_C, Values.Project_D.path)

            Emitter.normal("\t\t" + segment_code + ": " + vector_name_a.replace(".vec", ""))

            Slicer.slice_source_file(vector_source_a, segment_code, vector_name_a.replace(".vec", ""), Values.PATH_A)
            Slicer.slice_source_file(vector_source_b, segment_code, vector_name_b.replace(".vec", ""), Values.PATH_B)
            Slicer.slice_source_file(vector_source_c, segment_code, vector_name_c.replace(".vec", ""), Values.PATH_C)
            Slicer.slice_source_file(vector_source_d, segment_code, vector_name_d.replace(".vec", ""), Values.Project_D.path)

        except Exception as e:
            error_exit("something went wrong with slicing phase")


def safe_exec(function_def, title, *args):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    Emitter.sub_title("starting " + title + "...")
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


def slice():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Slicing Source Files")
    if not Values.SKIP_SLICE:
        safe_exec(slice_code, "slice segments", Values.file_list_to_patch)

