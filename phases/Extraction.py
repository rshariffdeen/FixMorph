#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time
from common import Definitions, Values
from common.Utilities import execute_command, error_exit, save_current_state
from tools import Emitter, Collector, Reader, Writer
from ast import Vector

generated_script_list = dict()


def generate_edit_script(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Emitter.normal("Generating edit script: " + name_a + Definitions.TO + name_b + "...")
    try:
        extra_arg = " --"
        command = Definitions.DIFF_COMMAND + " -s=" + Definitions.DIFF_SIZE + " -dump-matches " + \
                  file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating edit script: " + output_file)


# def generate_script_for_header_files(files_list_to_patch):
#     generated_script_list = dict()
#     script_file_ab = "output/diff_script_AB"
#     for (file_a, file_c, var_map) in files_list_to_patch:
#         file_b = file_a.replace(Values.Project_A.path, Values.Project_B.path)
#         if not os.path.isfile(file_b):
#             error_exit("Error: File not found.", file_b)
#         # Generate edit scripts for diff and matching
#         generate_edit_script(file_a, file_b, script_file_ab)
#         original_script, inserted_node_list, map_ab = Collector.collect_instruction_list(script_file_ab)
#
#         generated_data = (original_script, inserted_node_list, map_ab)
#         generated_script_list[(file_a, file_b, file_c)] = generated_data
#     Values.generated_script_for_header_files = generated_script_list


def generate_script_for_files(file_list_to_patch):
    global generated_script_list
    script_file_ab = Definitions.DIRECTORY_TMP + "/diff_script_AB"
    for (vec_path_a, vec_path_c, var_map) in file_list_to_patch:
        vector_source_a = ""
        vector_source_b = ""
        vector_source_c = ""
        try:
            if "func_" in vec_path_a:
                vector_source_a, vector_name_a = vec_path_a.split(".func_")
                vector_source_b = vector_source_a.replace(Values.Project_A.path, Values.Project_B.path)
                vector_source_c, vector_name_c = vec_path_c.split(".func_")
            elif "struct_" in vec_path_a:
                    vector_source_a, vector_name_a = vec_path_a.split(".struct_")
                    vector_source_b = vector_source_a.replace(Values.Project_A.path, Values.Project_B.path)
                    vector_source_c, vector_name_c = vec_path_c.split(".struct_")
            elif "enum_" in vec_path_a:
                vector_source_a, vector_name_a = vec_path_a.split(".enum_")
                vector_source_b = vector_source_a.replace(Values.Project_A.path, Values.Project_B.path)
                vector_source_c, vector_name_c = vec_path_c.split(".enum_")
                # if vector_source_b not in Values.Project_B.function_list.keys():
                #     error_exit("Error: File not found among affected.", vector_source_b)
                # if vector_name_a in Values.Project_B.function_list[vector_source_b].keys():
                #     vec_b = Values.Project_B.function_list[vector_source_b][vector_name_a]
                # else:
                #     error_exit("Error: Function not found among affected.", vector_name_a, vector_source_b)

            # vec_f_b_file = vec_f_a.replace(Values.Project_A.path, Values.Project_B.path)
            # # print(vec_f_b_file)
            # if vec_f_b_file not in Values.Project_B.function_list.keys():
            #     error_exit("Error: File not found among affected.", vec_f_b_file)
            # if vec_f_a.function_name in Values.Project_B.function_list[vec_f_b_file].keys():
            #     vec_f_b = Values.Project_B.function_list[vec_f_b_file][vec_f_a.function_name]
            # else:
            #     error_exit("Error: Function not found among affected.", vec_f_a.function_name, vec_f_b_file,
            #                Values.Project_B.function_list[vec_f_b_file].keys())

        except Exception as e:
            error_exit("something went wrong with extraction phase")

        # Generate edit scripts for diff and matching
        generate_edit_script(vector_source_a, vector_source_b, script_file_ab)
        original_script, inserted_node_list, map_ab = Collector.collect_instruction_list(script_file_ab)
        generated_data = (original_script, inserted_node_list, map_ab)
        generated_script_list[(vector_source_a, vector_source_b, vector_source_c)] = generated_data


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Emitter.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
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
    if not Values.file_list_to_patch:
        clone_list = Reader.read_json(Definitions.FILE_CLONE_INFO)
        Values.file_list_to_patch = clone_list
    Definitions.FILE_SCRIPT_INFO = Definitions.DIRECTORY_OUTPUT + "/script-info"


def save_values():
    Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    Values.generated_script_for_c_files = generated_script_list
    save_current_state()


def extract():
    Emitter.title("Generating GumTree script for patch")
    # Using all previous structures to transplant patch
    load_values()
    if not Values.SKIP_EXTRACTION:
        # safe_exec(generate_script_for_header_files, "generating script for header files", Values.header_file_list_to_patch)
        safe_exec(generate_script_for_files, "generating script for files", Values.file_list_to_patch)
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")

