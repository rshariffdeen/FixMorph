#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io
import os
import json
from common.Utilities import execute_command, error_exit, find_files, get_file_extension_list
from tools import Emitter, Logger
from ast import Vector, Parser, Generator as ASTGenerator
from common.Utilities import error_exit, clean_parse
from common import Definitions


def generate_vectors(file_extension, log_file, project):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\t\tgenerating vectors for " + file_extension + " files in " + project.name + "...")
    # Generates an AST file for each file of extension ext

    find_files(project.path, file_extension, log_file)
    with open(log_file, 'r') as file_list:
        source_file = file_list.readline().strip()
        while source_file:
            # Parses it to get useful information and generate vectors
            # if source_file != "/data/linux/3/v3_16/mm/hugetlb.c":
            #     source_file = file_list.readline().strip()
            #     continue
            try:
                function_list, definition_list = ASTGenerator.parse_ast(source_file, use_deckard=True)

                ast_tree = generate_ast_json(source_file)
                enum_list = list()
                function_list = list()
                macro_list = list()
                struct_list = list()
                type_def_list = list()
                def_list = list()
                decl_list = list()
                for ast_node in ast_tree['children']:
                    # print(ast_node)
                    node_type = str(ast_node["type"])
                    if node_type in ["VarDecl"]:
                        def_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
                    elif node_type in ["EnumConstantDecl", "EnumDecl"]:
                        if 'file' in ast_node.keys():
                            if ast_node['file'] == source_file:
                                enum_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
                    elif node_type in ["Macro"]:
                        if 'value' in ast_node.keys():
                            macro_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
                    elif node_type in ["TypedefDecl"]:
                        type_def_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
                    elif node_type in ["RecordDecl"]:
                        if 'file' in ast_node.keys():
                            if ast_node['file'] == source_file:
                                struct_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
                    elif node_type in ["FunctionDecl"]:
                        if ast_node['file'] == source_file:
                            function_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
                    elif node_type in ["EmptyDecl"]:
                        continue
                    else:
                        Emitter.error("unknown node type for code segmentation: " + str(node_type))
                        print(ast_node)

                project.enum_list[source_file] = dict()
                project.struct_list[source_file] = dict()
                project.function_list[source_file] = dict()
                project.macro_list[source_file] = dict()

                for function_name, begin_line, finish_line in function_list:
                    function_name = "func_" + function_name.split("(")[0]
                    project.function_list[source_file][function_name] = Vector.Vector(source_file, function_name, begin_line, finish_line, True)

                ASTGenerator.get_vars(project, source_file, definition_list)

                for struct_name, begin_line, finish_line in struct_list:
                    struct_name = "struct_" + struct_name.split(";")[0]
                    project.struct_list[source_file][struct_name] = Vector.Vector(source_file, struct_name, begin_line, finish_line, True)

                for macro_name, begin_line, finish_line in macro_list:
                    macro_name = "macro_" + macro_name
                    project.macro_list[source_file][macro_name] = Vector.Vector(source_file, macro_name, begin_line, finish_line, True)

                count = 0
                for enum_name, begin_line, finish_line in enum_list:
                    enum_name = "enum_" + enum_name.split(";")[0]
                    if "anonymous" in enum_name:
                        count = count + 1
                        enum_name = "enum_" + str(count)
                    project.enum_list[source_file][enum_name] = Vector.Vector(source_file, enum_name, begin_line, finish_line, True)

            except Exception as e:
                error_exit(e, "Unexpected error in parseAST with file:", source_file)
            source_file = file_list.readline().strip()


def generate_ast_json(file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    json_file = file_path + ".AST"
    dump_command = Definitions.APP_AST_DIFF + " -ast-dump-json " + file_path
    dump_command += " --"
    dump_command += " 2> output/errors_AST_dump > " + json_file
    return_code = execute_command(dump_command)
    Emitter.debug("return code:" + str(return_code))
    if os.stat(json_file).st_size == 0:
        return None
    with io.open(json_file, 'r', encoding='utf8', errors="ignore") as f:
        ast_json = json.loads(f.read())
    return ast_json['root']
