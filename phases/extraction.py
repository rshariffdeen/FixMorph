#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time
from common import definitions, values, utilities
from common.utilities import execute_command, error_exit, save_current_state
from tools import emitter, collector, reader, writer, generator
from ast import ast_vector

generated_script_list = dict()


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

            utilities.shift_slice_source(slice_file_a, slice_file_c)
            generator.generate_edit_script(vector_source_a, vector_source_b, script_file_ab)
            utilities.restore_slice_source()

            original_script, inserted_node_list, map_ab = collector.collect_instruction_list(script_file_ab)
            values.NODE_MAP[(slice_file_a, slice_file_b)] = map_ab
            if not original_script:
                error_exit("failed to extract AST transformation")
            generated_data = (original_script, inserted_node_list, map_ab)
            emitter.highlight("\tOriginal AST script")
            original_script_str = list()
            for instruction in original_script:
                instruction_line = ""
                for token in instruction:
                    instruction_line += token + " "
                original_script_str.append(instruction_line)
            emitter.emit_ast_script(original_script_str)
            generated_script_list[(slice_file_a, slice_file_b, slice_file_c)] = generated_data
            generated_source_list.append(vector_source_a)

        except Exception as e:
            error_exit("something went wrong with extraction phase")


def generate_diff_for_files(file_list_to_patch):
    global generated_script_list
    generated_source_list = list()

    for source_file_a in file_list_to_patch:
        source_file_c = file_list_to_patch[source_file_a]
        emitter.sub_sub_title(source_file_a)
        try:
            source_file_b = source_file_a.replace(values.Project_A.path, values.Project_B.path)
            diff_file_ab = source_file_b + ".diff"
            emitter.normal("\t\tcreating diff file:" + diff_file_ab)
            generator.generate_edit_diff(source_file_a, source_file_b, diff_file_ab)
            generated_script_list[(source_file_a, source_file_b, source_file_c)] = diff_file_ab
            generated_source_list.append(source_file_a)
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
    values.diff_transformation_info = generated_script_list
    save_current_state()


def start():
    emitter.title("Extract AST Transformation")
    # Using all previous structures to transplant patch
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_EXTRACTION]:
        if not values.file_list_to_patch:
            error_exit("no clone file detected to generate AST")
        if values.DEFAULT_OPERATION_MODE in [0, 3]:
            safe_exec(generate_script_for_files, "extraction of AST transformation", values.file_list_to_patch)
        elif values.DEFAULT_OPERATION_MODE in [1, 2]:
            safe_exec(generate_diff_for_files, "extraction of diff transformation", values.file_list_to_patch)
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")

