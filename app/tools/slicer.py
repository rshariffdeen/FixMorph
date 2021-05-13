#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import os

import app.common.utilities
from app.common import values, definitions
from app.common.utilities import error_exit, execute_command
from app.ast import ast_generator as ASTGenerator
from app.tools import transformer, emitter, extractor, logger


def slice_source_file(source_path, segment_code, segment_identifier, project_path, use_macro=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    output_file_name = "." + segment_code + "." + segment_identifier + ".slice"
    output_file_path = source_path + output_file_name
    if os.path.isfile(output_file_path):
        return True
    ast_tree = ASTGenerator.get_ast_json(source_path, use_macro, True)
    segment_type = values.segment_map[segment_code]
    ast_script = list()
    project_path = app.common.utilities.extract_project_path(source_path)
    source_relative_path = source_path.replace(project_path, "")[1:]

    segment_found = False
    for ast_node in ast_tree['children']:
        node_id = ast_node['id']
        node_type = ast_node['type']
        if node_type == segment_type:
            node_identifier = ast_node['identifier']
            if node_identifier != segment_identifier:
                # ast_script.append("Delete " + node_type + "(" + str(node_id) + ")")
                if 'file' in ast_node.keys():
                    file_path = ast_node['file']
                    file_project_path = app.common.utilities.extract_project_path(file_path)
                    file_relative_path = file_path
                    if file_project_path:
                        file_relative_path = file_path.replace(file_project_path, "")[1:]
                    if file_relative_path == source_relative_path:
                        ast_script.append("Delete " + node_type + "(" + str(node_id) + ")")
            else:
                segment_found = True
        elif node_type == "FunctionDecl":
            # ast_script.append("Delete " + node_type + "(" + str(node_id) + ")")
            if 'file' in ast_node.keys():
                file_path = ast_node['file']
                file_project_path = app.common.utilities.extract_project_path(file_path)
                file_relative_path = file_path
                if file_project_path:
                    file_relative_path = file_path.replace(file_project_path, "")[1:]
                if file_relative_path == source_relative_path:
                    ast_script.append("Delete " + node_type + "(" + str(node_id) + ")")

    if not segment_found:
        emitter.information("Slice not created")
        return False

    # print(ast_script)
    ast_script_path = definitions.DIRECTORY_OUTPUT + "/" + output_file_path.split("/")[-1] + ".ast"
    if ast_script:
        transformer.transform_source_file(source_path, ast_script, output_file_path, ast_script_path)
        if os.stat(output_file_path).st_size == 0:
            error_exit("Slice is empty")
    else:
        copy_command = "cp " + source_path + " " + output_file_path
        emitter.warning("\t\t[warning] AST script was empty, using full file")
        execute_command(copy_command)

    emitter.normal("\t\t\tcreated " + output_file_path)
    return segment_found


def slice_ast_tree(ast_tree, segment_code, segment_identifier):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    segment_type = values.segment_map[segment_code]
    sliced_ast_tree = ast_tree
    del sliced_ast_tree['children']
    sliced_ast_tree['children'] = list()
    for ast_node in ast_tree['children']:
        node_id = ast_node['id']
        node_type = ast_node['type']
        if node_type == segment_type:
            node_identifier = ast_node['identifier']
            if node_identifier == segment_identifier:
                sliced_ast_tree['children'].append(ast_node)
        elif node_type == "FunctionDecl":
            continue
        else:
            sliced_ast_tree['children'].append(ast_node)

    emitter.normal("\t\t\tcreated AST Slice for " + segment_identifier)
    return sliced_ast_tree
