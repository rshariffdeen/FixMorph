#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
from common.utilities import error_exit
from common import values, definitions
from tools import Logger, Emitter, Slicer


def fix_definitions(file_list_to_patch):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("fixing changed definitions")
    for (vec_path_a, vec_path_c, var_map) in file_list_to_patch:
        segment_code = vec_path_a.split(".")[-2].split("_")[0]
        try:
            split_regex = "." + segment_code + "_"
            vector_source_a, vector_name_a = vec_path_a.split(split_regex)
            vector_source_b = vector_source_a.replace(values.Project_A.path, values.Project_B.path)

            Emitter.normal("\t\t" + segment_code + ": " + vector_name_a.replace(".vec", ""))


        except Exception as e:
            error_exit("something went wrong with slicing phase")


def slice_code(file_list_to_patch):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("slicing unrelated segments")

    for (vec_path_a, vec_path_c, var_map) in file_list_to_patch:
        segment_code = vec_path_a.split(".")[-2].split("_")[0]
        try:
            split_regex = "." + segment_code + "_"
            vector_source_a, vector_name_a = vec_path_a.split(split_regex)
            vector_source_b = vector_source_a.replace(values.Project_A.path, values.Project_B.path)
            vector_source_c, vector_name_c = vec_path_c.split(split_regex)

            vector_name_b = vector_name_a.replace(values.PATH_A, values.PATH_B)
            vector_name_d = vector_name_c.replace(values.PATH_C, values.Project_D.path)
            vector_source_d = vector_source_c.replace(values.PATH_C, values.Project_D.path)

            segment_identifier_a = vector_name_a.replace(".vec", "")
            segment_identifier_b = vector_name_b.replace(".vec", "")
            segment_identifier_c = vector_name_c.replace(".vec", "")
            segment_identifier_d = vector_name_d.replace(".vec", "")

            if segment_code == "var":
                segment_identifier_a = vector_name_a[:segment_identifier_a.rfind("_")]
                segment_identifier_b = vector_name_b[:segment_identifier_b.rfind("_")]
                segment_identifier_c = vector_name_c[:segment_identifier_c.rfind("_")]
                segment_identifier_d = vector_name_d[:segment_identifier_d.rfind("_")]

            Emitter.normal("\t\t" + segment_code + ": " + segment_identifier_a)

            if values.DONOR_REQUIRE_MACRO:
                values.PRE_PROCESS_MACRO = values.DONOR_PRE_PROCESS_MACRO
            Slicer.slice_source_file(vector_source_a, segment_code, segment_identifier_a, values.PATH_A, values.DONOR_REQUIRE_MACRO)
            Slicer.slice_source_file(vector_source_b, segment_code, segment_identifier_b, values.PATH_B, values.DONOR_REQUIRE_MACRO)

            seg_found = Slicer.slice_source_file(vector_source_c, segment_code, vector_name_c.replace(".vec", ""), values.PATH_C)

            if not seg_found:
                values.TARGET_REQUIRE_MACRO = True
                values.PRE_PROCESS_MACRO = values.TARGET_PRE_PROCESS_MACRO
                seg_found = Slicer.slice_source_file(vector_source_c, segment_code, segment_identifier_c,
                                                     values.PATH_C, values.TARGET_REQUIRE_MACRO)

            Slicer.slice_source_file(vector_source_d, segment_code, segment_identifier_d,
                                     values.Project_D.path, values.TARGET_REQUIRE_MACRO)

        except Exception as e:
            error_exit("something went wrong with slicing phase")


def revert_definitions(file_list_to_patch):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.sub_sub_title("fixing changed definitions")
    for (vec_path_a, vec_path_c, var_map) in file_list_to_patch:
        segment_code = vec_path_a.split(".")[-2].split("_")[0]
        try:
            split_regex = "." + segment_code + "_"
            vector_source_a, vector_name_a = vec_path_a.split(split_regex)
            vector_source_b = vector_source_a.replace(values.Project_A.path, values.Project_B.path)
            vector_source_c, vector_name_c = vec_path_c.split(split_regex)

            vector_name_b = vector_name_a.replace(values.PATH_A, values.PATH_B)
            vector_name_d = vector_name_a.replace(values.PATH_C, values.Project_D.path)
            vector_source_d = vector_source_c.replace(values.PATH_C, values.Project_D.path)

            Emitter.normal("\t\t" + segment_code + ": " + vector_name_a.replace(".vec", ""))


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
        duration = format((time.time() - start_time) / 60, '.3f')
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        Emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def slice():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Slicing Source Files")
    if values.PHASE_SETTING[definitions.PHASE_SLICING]:
        safe_exec(slice_code, "slice segments", values.file_list_to_patch)
    else:
        Emitter.special("\n\t-skipping this phase-")
