#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time
from common import definitions, values
from common.utilities import execute_command, error_exit, save_current_state, backup_file_orig, restore_file_orig, replace_file
from tools import emitter, collector, reader, writer, slicer
from ast import ast_vector

generated_script_list = dict()


def generate_edit_script(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    emitter.normal("\t\t\tgenerating transformation script")
    try:
        extra_arg = ""
        if file_a[-1] == 'h':
            extra_arg = " --"
        command = definitions.DIFF_COMMAND + " -s=" + definitions.DIFF_SIZE + " -dump-matches "
        if values.DONOR_REQUIRE_MACRO:
            command += " " + values.DONOR_PRE_PROCESS_MACRO + " "
        command += file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating edit script: " + output_file)


def generate_edit_diff(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    emitter.normal("\t\t\tgenerating edit diff")
    try:
        command = definitions.LINUX_DIFF_COMMAND
        if values.DEFAULT_OPERATION_MODE == 2:
            command += " --context " + str(values.DEFAULT_CONTEXT_LEVEL) + " "
        command += file_a + " " + file_b + " 2> output/errors_linux_diff "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating edit script: " + output_file)


def generate_script_for_files(file_list_to_patch):
    global generated_script_list
    generated_source_list = list()
    script_file_ab = definitions.DIRECTORY_TMP + "/diff_script_AB"
    for (vec_path_a, vec_path_c, var_map) in file_list_to_patch:
        segment_code = vec_path_a.split(".")[-2].split("_")[0]
        emitter.sub_sub_title(vec_path_a)
        try:
            split_regex = "." + segment_code + "_"
            vector_source_a, vector_name_a = vec_path_a.split(split_regex)
            vector_source_b = vector_source_a.replace(values.Project_A.path, values.Project_B.path)
            vector_source_c, vector_name_c = vec_path_c.split(split_regex)
            vector_name_b = vector_name_a.replace(values.CONF_PATH_A, values.CONF_PATH_B)
            # if vector_source_a in generated_source_list:
            #     continue

            emitter.normal("\t\t" + segment_code + ": " + vector_name_a.replace(".vec", ""))

            slice_file_a = vector_source_a + "." + segment_code + "." + vector_name_a.replace(".vec", "") + ".slice"
            slice_file_b = vector_source_b + "." + segment_code + "." + vector_name_b.replace(".vec", "") + ".slice"
            slice_file_c = vector_source_c + "." + segment_code + "." + vector_name_c.replace(".vec", "") + ".slice"

            backup_file_orig(vector_source_a)
            backup_file_orig(vector_source_b)
            replace_file(slice_file_a, vector_source_a)
            replace_file(slice_file_b, vector_source_b)
            generate_edit_script(vector_source_a, vector_source_b, script_file_ab)
            restore_file_orig(vector_source_a)
            restore_file_orig(vector_source_b)

            original_script, inserted_node_list, map_ab = collector.collect_instruction_list(script_file_ab)
            values.NODE_MAP[(slice_file_a, slice_file_b)] = map_ab
            if not original_script:
                error_exit("failed to extract AST transformation")
            generated_data = (original_script, inserted_node_list, map_ab)
            generated_script_list[(slice_file_a, slice_file_b, slice_file_c)] = generated_data
            generated_source_list.append(vector_source_a)

        except Exception as e:
            error_exit("something went wrong with extraction phase")


def generate_diff_for_files(file_list_to_patch):
    global generated_script_list
    generated_source_list = list()

    for (vec_path_a, vec_path_c, var_map) in file_list_to_patch:
        segment_code = vec_path_a.split(".")[-2].split("_")[0]
        emitter.sub_sub_title(vec_path_a)
        try:
            split_regex = "." + segment_code + "_"
            vector_source_a, vector_name_a = vec_path_a.split(split_regex)
            vector_source_b = vector_source_a.replace(values.Project_A.path, values.Project_B.path)
            vector_source_c, vector_name_c = vec_path_c.split(split_regex)
            vector_name_b = vector_name_a.replace(values.CONF_PATH_A, values.CONF_PATH_B)
            # if vector_source_a in generated_source_list:
            #     continue

            emitter.normal("\t\t" + segment_code + ": " + vector_name_a.replace(".vec", ""))

            slice_file_a = vector_source_a + "." + segment_code + "." + vector_name_a.replace(".vec", "") + ".slice"
            slice_file_b = vector_source_b + "." + segment_code + "." + vector_name_b.replace(".vec", "") + ".slice"
            slice_file_c = vector_source_c + "." + segment_code + "." + vector_name_c.replace(".vec", "") + ".slice"
            diff_file_ab = slice_file_b + ".diff"

            backup_file_orig(vector_source_a)
            backup_file_orig(vector_source_b)
            replace_file(slice_file_a, vector_source_a)
            replace_file(slice_file_b, vector_source_b)
            generate_edit_diff(vector_source_a, vector_source_b, diff_file_ab)
            restore_file_orig(vector_source_a)
            restore_file_orig(vector_source_b)

            generated_script_list[(slice_file_a, slice_file_b, slice_file_c)] = diff_file_ab
            generated_source_list.append(vector_source_a)

        except Exception as e:
            error_exit("something went wrong with extraction phase")


def safe_exec(function_def, title, *args):
    start_time = time.time()
    emitter.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
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


def load_values():
    if not values.file_list_to_patch:
        clone_list = reader.read_json(definitions.FILE_CLONE_INFO)
        values.file_list_to_patch = clone_list
    definitions.FILE_SCRIPT_INFO = definitions.DIRECTORY_OUTPUT + "/script-info"
    definitions.FILE_MACRO_DEF = definitions.DIRECTORY_TMP + "/macro-def"


def save_values():
    writer.write_script_info(generated_script_list, definitions.FILE_SCRIPT_INFO)
    values.generated_script_files = generated_script_list
    save_current_state()


def start():
    emitter.title("Extract AST Transformation")
    # Using all previous structures to transplant patch
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_EXTRACTION]:
        if not values.file_list_to_patch:
            error_exit("no clone file detected to generate AST")
        if values.DEFAULT_OPERATION_MODE == 0:
            safe_exec(generate_script_for_files, "extraction of AST transformation", values.file_list_to_patch)
        elif values.DEFAULT_OPERATION_MODE in [1, 2]:
            safe_exec(generate_diff_for_files, "extraction of diff transformation", values.file_list_to_patch)
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")

