#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import os
from pathlib import Path

import app.common.utilities
from app.ast import ast_vector, ast_generator
from app.tools import emitter, logger
from app.common.utilities import execute_command, find_files, definitions
from app.common import values
import mmap

FILE_GREP_RESULT = ""



def is_node_equal(node_a, node_b, var_map):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    node_type_a = str(node_a['type'])
    node_type_b = str(node_b['type'])
    if node_type_a != node_type_b:
        return False

    if node_type_a in ["DeclStmt", "DeclRefExpr", "VarDecl"]:
        node_value_a = node_a['value']
        node_value_b = node_b['value']
        if node_value_a == node_value_b or node_value_a == var_map[node_value_b] or \
                node_value_b == var_map[node_value_a]:
            return True
        else:
            return False
    elif node_type_a == "ArraySubscriptExpr":
        # print(node_a)
        # print(node_b)
        node_value_a, node_type_a, var_list = converter.convert_array_subscript(node_a)
        node_value_b, node_type_b, var_list = converter.convert_array_subscript(node_b)
        if node_value_a == node_value_b or node_value_a == var_map[node_value_b] or \
                node_value_b == var_map[node_value_a]:
            return True
        else:
            return False
    elif node_type_a == "IntegerLiteral":
        node_value_a = int(node_a['value'])
        node_value_b = int(node_b['value'])
        if node_value_a == node_value_b:
            return True
        else:
            return False

    elif node_type_a == "MemberExpr":
        node_value_a, node_type_a, var_list = converter.convert_member_expr(node_a, True)
        node_value_b, node_type_b, var_list = converter.convert_member_expr(node_b, True)
        if node_value_a == node_value_b:
            return True
        else:
            if node_value_b in var_map and node_value_a == var_map[node_value_b]:
                return True
            else:
                return False
    elif node_type_a == "ParenExpr":
        child_node_a = node_a['children'][0]
        child_node_b = node_b['children'][0]
        return is_node_equal(child_node_a, child_node_b, var_map)
    elif node_type_a == "BinaryOperator":
        left_child_a = node_a['children'][0]
        right_child_a = node_a['children'][1]
        left_child_b = node_b['children'][0]
        right_child_b = node_b['children'][1]
        if is_node_equal(left_child_a, left_child_b, var_map) and \
                is_node_equal(right_child_a, right_child_b, var_map):
            return True
        else:
            return False


def search_vector(file_path):
    with open(file_path, 'r', errors='replace') as vec_file:
            content = vec_file.readline()
            if content:
                vector = [int(s) for s in vec_file.readline().strip().split(" ")]
                vector = ast_vector.Vector.normed(vector)
                return vector
            else:
                emitter.information("Vector file is empty")
    emitter.information("Vector file not found")
    return None


def search_vector_list(project, extension, vec_type):
    if "c" in extension:
        rxt = "C"
    else:
        rxt = "h"

    emitter.normal("\tanalysing vectors for " + vec_type + " segments in " + project.name + "...")
    filepath = definitions.DIRECTORY_OUTPUT + "/vectors_" + rxt + "_" + project.name
    find_files(project.path, extension, filepath, None)
    with open(filepath, "r", errors='replace') as file:
        files = [vec.strip() for vec in file.readlines()]
    vecs = []
    for i in range(len(files)):
        vecs.append((files[i], search_vector(files[i])))
    return vecs


def search_matching_node(ast_node, search_node, var_map):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    node_id = int(ast_node['id'])
    node_type = str(ast_node['type'])
    search_node_type = str(search_node['type'])
    if node_type == search_node_type:
        if is_node_equal(ast_node, search_node, var_map):
            return node_type + "(" + str(node_id) + ")"

    for child_node in ast_node['children']:
        if len(child_node['children']) > 0:
            target_node_str = search_matching_node(child_node, search_node, var_map)
            if target_node_str is not None:
                return target_node_str


def find_ast_node_position(ast_node, line_number):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    node_id = ast_node['id']
    node_type = ast_node['type']
    child_index = 0
    line_number = int(line_number)
    prev_child_node = ""
    for child_node in ast_node['children']:
        child_node_id = int(child_node['id'])
        child_node_type = str(child_node['type'])
        child_node_start_line = int(child_node['start line'])
        child_node_end_line = int(child_node['end line'])
        if child_node_start_line == line_number:
            return str(node_type) + "(" + str(node_id) + ") at " + str(child_index)
        elif child_node_start_line > line_number:
            return find_ast_node_position(prev_child_node, line_number)
        prev_child_node = child_node
        child_index += 1
    return find_ast_node_position(prev_child_node, line_number)


def search_ast_node_by_id(ast_node, find_id):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    is_high = False
    is_low = False
    prev_child_node = None
    if not ast_node:
        return None
    node_id = int(ast_node['id'])
    if node_id == find_id:
        return ast_node
    for child_node in ast_node['children']:
        child_id = int(child_node['id'])
        if child_id == find_id:
            return child_node
        elif child_id < find_id:
            is_low = True
        else:
            is_high = True

        if is_low and is_high:
            return search_ast_node_by_id(prev_child_node, int(find_id))
        else:
            prev_child_node = child_node
    return search_ast_node_by_id(prev_child_node, int(find_id))


def search_function_node_by_name(ast_node, function_name):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    function_node = None
    for child_node in ast_node['children']:
        child_node_type = child_node['type']
        if child_node_type == "FunctionDecl":
            child_node_identifier = child_node['identifier']
            # print(child_node_identifier, function_name)
            if child_node_identifier == function_name:
                function_node = child_node
    return function_node


def search_node(ast_tree, node_type, node_identifier):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    for ast_node in ast_tree['children']:
        ast_node_type = ast_node['type']
        if ast_node_type == node_type:
            ast_node_identifier = ast_node['identifier']
            # print(child_node_identifier, function_name)
            if ast_node_identifier == node_identifier:
                if node_type == "FunctionDecl":
                    if 'file' in ast_node.keys():
                        if str(ast_node['file'])[-2:] == ".h":
                            continue
                    if len(ast_node['children']) > 1:
                        if ast_node['children'][1]['type'] == "CompoundStmt":
                            return ast_node
                else:
                    return ast_node


def search_function_node_by_loc(ast_node, line_number, source_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    file_name = source_path.split("/")[-1]
    for child_node in ast_node['children']:
        child_node_type = child_node['type']
        if child_node_type == "FunctionDecl":
            if "file" in child_node.keys():
                function_source = child_node['file']
                if file_name not in function_source:
                    continue
            child_node_start_line = int(child_node['start line'])
            child_node_end_line = int(child_node['end line'])
            if line_number in range(child_node_start_line, child_node_end_line + 1):
                return child_node

    for child_node in ast_node['children']:
        if child_node_type == "Macro":
            child_node_start_line = int(child_node['start line'])
            child_node_end_line = int(child_node['end line'])
            if line_number in range(child_node_start_line, child_node_end_line + 1):
                return child_node
    return None


def search_node_by_loc(ast_node, line_number):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    for child_node in ast_node['children']:
        child_node_start_line = int(child_node['start line'])
        child_node_end_line = int(child_node['end line'])
        if child_node_start_line == line_number:
            return child_node
        if child_node_start_line == line_number:
            return child_node
        if line_number in range(child_node_start_line, child_node_end_line + 1):
            return search_node_by_loc(child_node, line_number)
    return None


def find_definition_insertion_point(source_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    file_name = source_path.split("/")[-1]
    ast_node = ast_generator.get_ast_json(source_path, regenerate=True)
    for child_node in ast_node['children']:
        child_node_type = child_node['type']
        if child_node_type == "FunctionDecl":
            if 'file' in child_node:
                child_node_file_name = child_node['file'].split("/")[-1]
                if child_node_file_name == file_name:
                    return int(child_node['start line']) - 1
    return 0


def find_header_file(query, source_path, target_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global FILE_GREP_RESULT
    project_dir = app.common.utilities.extract_project_path(source_path)
    FILE_GREP_RESULT = definitions.DIRECTORY_OUTPUT + "/grep-output"
    search_command = "cd " + project_dir + ";"
    search_command += "grep -inr -e \"" + query + "\" . | grep define"
    search_command += " > " + FILE_GREP_RESULT
    execute_command(search_command)
    target_ast_tree = ast_generator.get_ast_json(target_path, regenerate=True)
    header_file_list_in_target = extract_header_file_list(target_ast_tree)
    # print(header_file_list_in_target)
    with open(FILE_GREP_RESULT, 'r') as result_file:
        candidate_list = result_file.readlines()
        candidate_header_list = list()
        for candidate in candidate_list:
            candidate_file = str(candidate).split(":")[0]
            if values.Project_D.path in candidate_file:
                candidate_file = candidate_file.replace(values.Project_D.path + "/", "")
            if candidate_file[0] == ".":
                candidate_file = candidate_file[2:]
            if candidate_file not in candidate_header_list:
                candidate_header_list.append(candidate_file)
        # print(candidate_header_list)
        intersection = list(set(header_file_list_in_target).intersection(candidate_header_list))
        if intersection:
            for header_file_path in intersection:
                header_abs_path = values.CONF_PATH_C + "/" + header_file_path
                with open(header_abs_path, "rb", 0) as header_file:
                    with mmap.mmap(header_file.fileno(), 0, access=mmap.ACCESS_READ) as read_map:
                        if read_map.find(bytes(query, 'utf-8')) != -1:
                            return None
        if len(candidate_list) >= 1:
            # TODO: can improve selection
            best_candidate = str(candidate_list[0]).split(":")[0]
            if len(candidate_list) > 1:
                for candidate_file in candidate_header_list:
                    if ".h" in candidate_file:
                        best_candidate = candidate_file
                emitter.warning("\t\t[warning] more than one definition found")
            abs_path = project_dir + "/" + best_candidate
            return abs_path
    return None


def find_file_in_dir(query, search_dir):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    file_name = query.split("/")[-1]
    file_list = Path(search_dir).rglob(file_name)
    best_candidate = None
    # TODO: can improve selection
    for candidate in file_list:
        if query in candidate:
            best_candidate = candidate
            return
    return best_candidate


def find_clone(file_name):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    # check if obvious exist
    candidate_path = file_name.replace(values.CONF_PATH_A, values.CONF_PATH_C).replace(values.CONF_PATH_B, values.CONF_PATH_C)
    if os.path.isfile(candidate_path):
        return candidate_path
    file_path_list = set()
    source_path = file_name.replace(values.CONF_PATH_A, "").replace(values.CONF_PATH_B, "")
    if source_path[0] == "/":
        source_path = source_path[1:]
    git_query = "cd " + values.CONF_PATH_A + ";"
    result_file = definitions.DIRECTORY_TMP + "/list"
    git_query += "git log --follow --pretty=\"\" --name-only " + source_path + " > " + result_file
    execute_command(git_query)
    clone_path = None
    with open(result_file, 'r') as tmp_file:
        list_lines = tmp_file.readlines()
        for path in list_lines:
            file_path_list.add(path.strip().replace("\n", ""))
    # remove duplicates
    file_path_list = list(set(file_path_list))
    for file_path in file_path_list:
        new_path = values.Project_C.path + "/" + file_path
        if os.path.isfile(new_path):
            clone_path = new_path
            break
    # TODO: use semantic clone detection if NONE

    return clone_path


def extract_header_file_list(ast_tree):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    header_file_list = list()
    if "file" in ast_tree:
        file_loc = ast_tree['file']
        if ".h" in file_loc:
            if values.Project_D.path in file_loc:
                file_loc = file_loc.replace(values.Project_D.path + "/", "")
            header_file_list.append(file_loc)
    if len(ast_tree['children']) > 0:
        for child_node in ast_tree['children']:
            child_list = extract_header_file_list(child_node)
            header_file_list = header_file_list + child_list
    return list(set(header_file_list))