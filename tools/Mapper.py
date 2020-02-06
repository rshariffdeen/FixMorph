from common import Definitions
from common.Utilities import execute_command, error_exit
from tools import Emitter, Logger
from ast import Generator
import sys


def map_ast_from_source(source_a, source_b, script_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Generator.generate_ast_script(source_a, source_b, script_file_path, True)
    mapping = dict()
    with open(script_file_path, "r") as script_file:
        script_lines = script_file.readlines()
        for script_line in script_lines:
            if "Match" in script_line:
                node_id_a = int(((script_line.split(" to ")[0]).split("(")[1]).split(")")[0])
                node_id_b = int(((script_line.split(" to ")[1]).split("(")[1]).split(")")[0])
                mapping[node_id_b] = node_id_a
    return mapping


def generate_map(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Emitter.blue("Generating mapping: " + name_a + Definitions.TO + name_b + "...")
    try:
        extra_arg = " --"
        command = Definitions.DIFF_COMMAND + " -s=" + Definitions.DIFF_SIZE + " -dump-matches " + \
                  file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += "| grep '^Match ' "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating map: " + output_file)


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
            if operation == Definitions.MATCH:
                try:
                    node_a, node_c = clean_parse(content, Definitions.TO)
                    node_map[node_a] = node_c
                except Exception as exception:
                    error_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return node_map


def generate(generated_script_files):
    variable_map = dict()
    if len(generated_script_files) == 0:
        Emitter.normal("\t -nothing-to-do")
    else:
        for file_list, generated_data in generated_script_files.items():
            map_file_name = Definitions.DIRECTORY_TMP + "/diff_script_AC"
            generate_map(file_list[0], file_list[2], map_file_name)
            variable_map = get_mapping(map_file_name)
            variable_map[file_list] = variable_map
    return variable_map
