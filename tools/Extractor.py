#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time
from common import Definitions
from common.Utilities import exec_com, err_exit
import Emitter


def clean_parse(content, separator):
    if content.count(separator) == 1:
        return content.split(separator)
    i = 0
    while i < len(content):
        if content[i] == "\"":
            i += 1
            while i < len(content) - 1:
                if content[i] == "\\":
                    i += 2
                elif content[i] == "\"":
                    i += 1
                    break
                else:
                    i += 1
            prefix = content[:i]
            rest = content[i:].split(separator)
            node1 = prefix + rest[0]
            node2 = separator.join(rest[1:])
            return [node1, node2]
        i += 1
    # If all the above fails (it shouldn't), hope for some luck:
    nodes = content.split(separator)
    half = len(nodes) // 2
    node1 = separator.join(nodes[:half])
    node2 = separator.join(nodes[half:])
    return [node1, node2]


def generate_edit_script(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Emitter.blue("Generating edit script: " + name_a + Definitions.TO + name_b + "...")
    try:
        extra_arg = ""
        if file_a[-2:] == ".h":
            extra_arg = " --"
        command = Definitions.DIFF_COMMAND + " -s=" + Definitions.DIFF_SIZE + " -dump-matches " + \
                  file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += " > " + output_file
        exec_com(command, False)
    except Exception as e:
        err_exit(e, "Unexpected fail at generating edit script: " + output_file)


def get_instruction_list(script_file_name):
    instruction_list = list()
    inserted_node_list = list()
    map_ab = dict()
    with open(script_file_name, 'r', errors='replace') as script:
        line = script.readline().strip()
        while line:
            line = line.split(" ")
            # Special case: Update and Move nodeA into nodeB2
            if len(line) > 3 and line[0] == Definitions.UPDATE and line[1] == Definitions.AND and \
                    line[2] == Definitions.MOVE:
                instruction = Definitions.UPDATEMOVE
                content = " ".join(line[3:])

            else:
                instruction = line[0]
                content = " ".join(line[1:])
            # Match nodeA to nodeB
            if instruction == Definitions.MATCH:
                try:
                    nodeA, nodeB = clean_parse(content, Definitions.TO)
                    map_ab[nodeB] = nodeA
                except Exception as e:
                    err_exit(e, "Something went wrong in MATCH (AB).",
                             line, instruction, content)
            # Update nodeA to nodeB (only care about value)
            elif instruction == Definitions.UPDATE:
                try:
                    nodeA, nodeB = clean_parse(content, Definitions.TO)
                    instruction_list.append((instruction, nodeA, nodeB))
                except Exception as e:
                    err_exit(e, "Something went wrong in UPDATE.")
            # Delete nodeA
            elif instruction == Definitions.DELETE:
                try:
                    nodeA = content
                    instruction_list.append((instruction, nodeA))
                except Exception as e:
                    err_exit(e, "Something went wrong in DELETE.")
            # Move nodeA into nodeB at pos
            elif instruction == Definitions.MOVE:
                try:
                    nodeA, nodeB = clean_parse(content, Definitions.INTO)
                    nodeB_at = nodeB.split(Definitions.AT)
                    nodeB = Definitions.AT.join(nodeB_at[:-1])
                    pos = nodeB_at[-1]
                    instruction_list.append((instruction, nodeA, nodeB, pos))
                except Exception as e:
                    err_exit(e, "Something went wrong in MOVE.")
            # Update nodeA into matching node in B and move into nodeB at pos
            elif instruction == Definitions.UPDATEMOVE:
                try:
                    nodeA, nodeB = clean_parse(content, Definitions.INTO)
                    nodeB_at = nodeB.split(Definitions.AT)
                    nodeB = Definitions.AT.join(nodeB_at[:-1])
                    pos = nodeB_at[-1]
                    instruction_list.append((instruction, nodeA, nodeB, pos))
                except Exception as e:
                    err_exit(e, "Something went wrong in MOVE.")
                    # Insert nodeB1 into nodeB2 at pos
            elif instruction == Definitions.INSERT:
                try:
                    nodeB1, nodeB2 = clean_parse(content, Definitions.INTO)
                    nodeB2_at = nodeB2.split(Definitions.AT)
                    nodeB2 = Definitions.AT.join(nodeB2_at[:-1])
                    pos = nodeB2_at[-1]
                    instruction_list.append((instruction, nodeB1, nodeB2,
                                           pos))
                    inserted_node_list.append(nodeB1)
                except Exception as e:
                    err_exit(e, "Something went wrong in INSERT.")
            line = script.readline().strip()
    return instruction_list, inserted_node_list, map_ab


def generate_script_for_header_files(files_list_to_patch):
    generated_script_list = dict()
    script_file_ab = "output/diff_script_AB"
    for (file_a, file_c, var_map) in files_list_to_patch:
        file_b = file_a.replace(Definitions.Pa.path, Definitions.Pb.path)
        if not os.path.isfile(file_b):
            err_exit("Error: File not found.", file_b)
        # Generate edit scripts for diff and matching
        generate_edit_script(file_a, file_b, script_file_ab)
        original_script, inserted_node_list, map_ab = get_instruction_list(script_file_ab)

        generated_data = (original_script, inserted_node_list, map_ab)
        generated_script_list[(file_a, file_b, file_c)] = generated_data
    Definitions.generated_script_for_header_files = generated_script_list


def generate_script_for_c_files(file_list_to_patch):
    generated_script_list = dict()
    script_file_ab = "output/diff_script_AB"
    for (vec_f_a, vec_f_c, var_map) in file_list_to_patch:
        try:
            vec_f_b_file = vec_f_a.file.replace(Definitions.Pa.path, Definitions.Pb.path)
            if vec_f_b_file not in Definitions.Pb.functions.keys():
                err_exit("Error: File not found among affected.", vec_f_b_file)
            if vec_f_a.function in Definitions.Pb.functions[vec_f_b_file].keys():
                vec_f_b = Definitions.Pb.functions[vec_f_b_file][vec_f_a.function]
            else:
                err_exit("Error: Function not found among affected.", vec_f_a.function, vec_f_b_file,
                         Definitions.Pb.functions[vec_f_b_file].keys())
        except Exception as e:
            err_exit(e, vec_f_b_file, vec_f_a, Definitions.Pa.path, Definitions.Pb.path, vec_f_a.function)

        # Generate edit scripts for diff and matching
        generate_edit_script(vec_f_a.file, vec_f_b.file, script_file_ab)
        original_script, inserted_node_list, map_ab = get_instruction_list(script_file_ab)

        generated_data = (original_script, inserted_node_list, map_ab)
        generated_script_list[(vec_f_a.file, vec_f_b.file, vec_f_c.file)] = generated_data
    Definitions.generated_script_for_c_files = generated_script_list


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
        err_exit(exception, "Unexpected error during " + description + ".")
    return result


def extract():
    Emitter.title("Generating GumTree script for patch")
    # Using all previous structures to transplant patch
    safe_exec(generate_script_for_header_files, "generating script for header files", Definitions.header_file_list_to_patch)
    safe_exec(generate_script_for_c_files, "generating script for C files", Definitions.c_file_list_to_patch)

