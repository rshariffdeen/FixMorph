import os
import sys
import time
import Common
import Initialization
import Detection
from Utils import exec_com, err_exit, find_files, clean, get_extensions
import Project
import Print
import ASTVector
import ASTgen
import ASTparser


def ASTscript(file1, file2, output, only_matches=False):
    extra_arg = ""
    if file1[-2:] == ".h":
        extra_arg = " --"
    c = Common.DIFF_COMMAND + " -s=" + Common.DIFF_SIZE + " -dump-matches " + \
        file1 + " " + file2 + extra_arg + " 2> output/errors_clang_diff "
    if only_matches:
        c += "| grep '^Match ' "
    c += " > " + output
    exec_com(c, True)


def generate_edit_script(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Print.blue("Generating edit script: " + name_a + Common.TO + name_b + "...")
    try:
        ASTscript(file_a, file_b, output_file)
    except Exception as e:
        err_exit(e, "Unexpected fail at generating edit script: " + output_file)


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


def get_mapping(map_file_name):
    node_map = dict()
    with open(map_file_name, 'r', errors='replace') as ast_map:
        line = ast_map.readline().strip()
        while line:
            line = line.split(" ")
            operation = line[0]
            content = " ".join(line[1:])
            if operation == Common.MATCH:
                try:
                    node_a, node_c = clean_parse(content, Common.TO)
                    node_map[node_a] = node_c
                except Exception as exception:
                    err_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return node_map


def map():
    Print.title("Variable Mapping")
    Print.sub_title("Variable mapping for header files")

    for file_list, generated_data in Common.generated_script_for_header_files.items():
        map_file_name = "output/diff_script_AC"
        generate_edit_script(file_list[0], file_list[2], map_file_name)
        map_ac = get_mapping(map_file_name)
        generated_data.insert(map_ac)

    Print.sub_title("Variable mapping for C files")
    for file_list, generated_data in Common.generated_script_for_c_files.items():
        map_file_name = "output/diff_script_AC"
        generate_edit_script(file_list[0], file_list[2], map_file_name)
        map_ac = get_mapping(map_file_name)
        generated_data.insert(map_ac)
