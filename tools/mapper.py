from common import definitions, values
from common.utilities import execute_command, error_exit, backup_file_orig, restore_file_orig, replace_file, get_source_name_from_slice
from tools import emitter, logger, finder, converter, writer, parallel
from ast import ast_generator
import sys

BREAK_LIST = [",", " ", " _", ";", "\n"]


def map_ast_from_source(source_a, source_b, script_file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    ast_generator.generate_ast_script(source_a, source_b, script_file_path, True)
    mapping = dict()
    with open(script_file_path, 'r', encoding='utf8', errors="ignore") as script_file:
        script_lines = script_file.readlines()
        for script_line in script_lines:
            if "Match" in script_line:
                node_id_a = int(((script_line.split(" to ")[0]).split("(")[1]).split(")")[0])
                node_id_b = int(((script_line.split(" to ")[1]).split("(")[1]).split(")")[0])
                mapping[node_id_b] = node_id_a
    return mapping


def generate_map_gumtree(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    emitter.normal("\tsource: " + file_a)
    emitter.normal("\ttarget: " + file_b)
    emitter.normal("\tgenerating ast map")
    try:
        extra_arg = ""
        if file_a[-1] == 'h':
            extra_arg = " --"
        command = definitions.DIFF_COMMAND + " -s=" + definitions.DIFF_SIZE + " -dump-matches "
        if values.DONOR_REQUIRE_MACRO:
            command += " " + values.DONOR_PRE_PROCESS_MACRO + " "
        if values.TARGET_REQUIRE_MACRO:
            command += " " + values.TARGET_PRE_PROCESS_MACRO + " "
        command += file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        # command += "| grep '^Match ' "
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


def generate_map(file_list):
    slice_file_a = file_list[0]
    slice_file_c = file_list[2]
    vector_source_a = get_source_name_from_slice(slice_file_a)
    vector_source_c = get_source_name_from_slice(slice_file_c)

    backup_file_orig(vector_source_a)
    backup_file_orig(vector_source_c)
    replace_file(slice_file_a, vector_source_a)
    replace_file(slice_file_c, vector_source_c)

    map_file_name = definitions.DIRECTORY_OUTPUT + "/" + slice_file_a.split("/")[-1] + ".map"
    if not values.CONF_USE_CACHE:
        generate_map_gumtree(vector_source_a, vector_source_c, map_file_name)

    ast_node_map = parallel.read_mapping(map_file_name)
    emitter.data(ast_node_map)
    ast_node_map = parallel.extend_mapping(ast_node_map, vector_source_a, vector_source_c)
    emitter.data(ast_node_map)
    namespace_map = parallel.derive_namespace_map(ast_node_map, vector_source_a,
                                                  vector_source_c, slice_file_a)
    restore_file_orig(vector_source_a)
    restore_file_orig(vector_source_c)

    return ast_node_map, namespace_map


def anti_unification(ast_node_a, ast_node_c):
    au_pairs = dict()
    waiting_list_a = [ast_node_a]
    waiting_list_c = [ast_node_c]

    while len(waiting_list_a) != 0 and len(waiting_list_c) != 0:
        current_a = waiting_list_a.pop()
        current_c = waiting_list_c.pop()

        children_a = current_a["children"]
        children_c = current_c["children"]

        # do not support anti-unification with different number of children yet
        if len(children_a) != len(children_c):
            continue

        length = len(children_a)
        for i in range(length):
            child_a = children_a[i]
            child_c = children_c[i]
            if child_a["type"] == child_c["type"]:
                waiting_list_a.append(child_a)
                waiting_list_c.append(child_c)
            else:
                key = child_a["type"] + "(" + str(child_a["id"]) + ")"
                value = child_c["type"] + "(" + str(child_c["id"]) + ")"
                au_pairs[key] = value

    return au_pairs

