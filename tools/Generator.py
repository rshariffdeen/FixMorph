#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io
import os

import json
from common.Utilities import execute_command, error_exit, find_files, get_file_extension_list
from tools import Emitter, Logger, Extractor
from ast import Vector, Parser, Generator as ASTGenerator
from common.Utilities import error_exit, clean_parse
from common import Definitions, Values


def find_source_file(diff_file_list, project, log_file, file_extension):
    Emitter.normal("\t\t\tlocating source files")
    source_dir = None
    list_files = set()
    for source_loc in diff_file_list:
        file_path_list = set()
        source_path, line_number = source_loc.split(":")
        source_path = source_path.replace(Values.PATH_A, "")
        source_path = source_path[1:]
        git_query = "cd " + Values.PATH_A + ";"
        result_file = Definitions.DIRECTORY_TMP + "/list"
        git_query += "git log --follow --pretty=\"\" --name-only " + source_path + " > " + result_file
        execute_command(git_query)
        with open(result_file, 'r') as tmp_file:
            list_lines = tmp_file.readlines()
            for path in list_lines:
                file_path_list.add(path.strip().replace("\n", ""))

        for file_path in file_path_list:
            new_path = project.path + "/" + file_path
            if os.path.isfile(new_path):
                list_files.add(new_path)
                break

        if not list_files:
            iterate_path(source_path, project, file_extension, log_file)

        # file_name = source_path.split("/")[-1][:-2]
        # source_dir = source_path[:str(source_path).find(file_name)]
        # source_dir = source_dir.replace(Values.PATH_A, "")[1:]
        # if regex is None:
        #     regex = file_name
        # else:
        #     regex = regex + "\|" + file_name

    # print(list_files)
    if list_files:
        with open(log_file, 'w') as out_file:
            out_file.writelines(list_files)


def iterate_path(source_path, project, file_extension, log_file):
    regex = None
    file_name = source_path.split("/")[-1][:-2]
    source_dir = source_path[:str(source_path).find(file_name)]
    source_dir = source_dir.replace(Values.PATH_A, "")
    if regex is None:
        regex = file_name
    else:
        regex = regex + "\|" + file_name

    find_files(project.path, file_extension, log_file, regex)

    while os.stat(log_file).st_size == 0:
        source_dir = source_dir[:-1]
        regex = source_dir
        find_files(project.path, file_extension, log_file, regex)
        if "/" not in source_dir:
            break
        last_sub_dir = source_dir.split("/")[-1]
        source_dir = source_dir[:source_dir.find(last_sub_dir)]


def generate_segmentation(source_file, use_macro=False):
    enum_list = list()
    function_list = list()
    macro_list = list()
    struct_list = list()
    type_def_list = list()
    def_list = list()
    decl_list = list()
    Emitter.normal("\t\t\tgenerating neighborhoods")
    function_list, definition_list = ASTGenerator.parse_ast(source_file, use_deckard=False, use_macro=use_macro)
    ast_tree = generate_ast_json(source_file, use_macro)
    if ast_tree is None:
        return None

    source_file_pattern = [source_file, source_file.split("/")[-1],
                           source_file.replace(Values.Project_C.path, '')[1:], source_file.replace(Values.Project_C.path, '')]
    for ast_node in ast_tree['children']:
        # print(ast_node)
        node_type = str(ast_node["type"])
        if node_type in ["VarDecl"]:
            if 'file' in ast_node.keys():
                if ast_node['file'] in source_file_pattern:
                    parent_id = int(ast_node['parent_id'])
                    if parent_id == 0:
                        decl_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["EnumConstantDecl", "EnumDecl"]:
            if 'file' in ast_node.keys():
                if ast_node['file'] in source_file_pattern:
                    enum_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["Macro"]:
            if 'file' in ast_node.keys():
                if ast_node['file'] in source_file_pattern:
                    if 'value' in ast_node.keys():
                        macro_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["TypedefDecl"]:
            if 'file' in ast_node.keys():
                if ast_node['file'] in source_file_pattern:
                    type_def_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["RecordDecl"]:
            if 'file' in ast_node.keys():
                if ast_node['file'] in source_file_pattern:
                    struct_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["FunctionDecl"]:
            if 'file' in ast_node.keys():
                if ast_node['file'] in source_file_pattern:
                    function_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["EmptyDecl", "FileScopeAsmDecl"]:
            continue
        else:
            Emitter.error("unknown node type for code segmentation: " + str(node_type))
            print(source_file, ast_node)

    return enum_list, function_list, macro_list, struct_list, type_def_list, def_list, decl_list, definition_list


def create_vectors(project, source_file, segmentation_list):
    project.enum_list[source_file] = dict()
    project.struct_list[source_file] = dict()
    project.function_list[source_file] = dict()
    project.macro_list[source_file] = dict()
    project.decl_list[source_file] = dict()
    Emitter.normal("\t\t\tcreating vectors for neighborhoods")
    enum_list, function_list, macro_list, \
    struct_list, type_def_list, def_list, decl_list, definition_list = segmentation_list

    if Values.IS_FUNCTION:
        # Emitter.normal("\t\t\tgenerating function vectors")
        for function_name, begin_line, finish_line in function_list:
            function_name = "func_" + function_name.split("(")[0]
            project.function_list[source_file][function_name] = Vector.Vector(source_file, function_name, begin_line,
                                                                              finish_line, True)

        ASTGenerator.get_vars(project, source_file, definition_list)

    if Values.IS_STRUCT:
        # Emitter.normal("\t\t\tgenerating struct vectors")
        for struct_name, begin_line, finish_line in struct_list:
            struct_name = "struct_" + struct_name.split(";")[0]
            project.struct_list[source_file][struct_name] = Vector.Vector(source_file, struct_name, begin_line,
                                                                          finish_line, True)

    if Values.IS_TYPEDEC:
        # Emitter.normal("\t\t\tgenerating struct vectors")
        for var_name, begin_line, finish_line in decl_list:
            var_name = "var_" + var_name.split(";")[0]
            var_type = (var_name.split("(")[1]).split(")")[0]
            var_name = var_name.split("(")[0] + "_" + var_type.split(" ")[0]
            project.decl_list[source_file][var_name] = Vector.Vector(source_file, var_name, begin_line, finish_line,
                                                                     True)

    if Values.IS_MACRO:
        # Emitter.normal("\t\t\tgenerating macro vectors")
        for macro_name, begin_line, finish_line in macro_list:
            macro_name = "macro_" + macro_name
            project.macro_list[source_file][macro_name] = Vector.Vector(source_file, macro_name, begin_line,
                                                                        finish_line, True)

    if Values.IS_ENUM:
        # Emitter.normal("\t\t\tgenerating enum vectors")
        count = 0
        for enum_name, begin_line, finish_line in enum_list:
            enum_name = "enum_" + enum_name.split(";")[0]
            if "anonymous" in enum_name:
                count = count + 1
                enum_name = "enum_" + str(count)
            project.enum_list[source_file][enum_name] = Vector.Vector(source_file, enum_name, begin_line, finish_line,
                                                                      True)


def generate_vectors(file_extension, log_file, project, diff_file_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\t\tgenerating vectors for " + file_extension + " files in " + project.name + "...")
    # Generates an AST file for each file of extension ext

    # intelligently generate vectors
    regex = None
    if Values.BACKPORT or Values.FORK:
        find_source_file(diff_file_list, project, log_file, file_extension)
    else:
        find_files(project.path, file_extension, log_file, regex)

    if os.stat(log_file).st_size == 0:
        find_files(project.path, file_extension, log_file, None)

    with open(log_file, 'r') as file_list:
        source_file = file_list.readline().strip()
        while source_file:
            # Parses it to get useful information and generate vectors
            # if source_file != "/data/linux/3/v3_16/mm/hugetlb.c":
            #     source_file = file_list.readline().strip()
            #     continue
            Values.TARGET_PRE_PROCESS_MACRO = Extractor.extract_pre_macro_list(source_file)

            try:
                segmentation_list = generate_segmentation(source_file)
                if segmentation_list is None:
                    source_file = file_list.readline().strip()
                    continue
                create_vectors(project, source_file, segmentation_list)
                segmentation_list_macro = generate_segmentation(source_file, True)
                create_vectors(project, source_file, segmentation_list_macro)

            except Exception as e:
                error_exit(e, "Unexpected error in parseAST with file:", source_file)
            source_file = file_list.readline().strip()


def generate_ast_json(file_path, use_macro=False):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    json_file = file_path + ".AST"
    macro_list = Values.TARGET_PRE_PROCESS_MACRO
    if Values.PATH_A in file_path:
        macro_list = Values.DONOR_PRE_PROCESS_MACRO
    dump_command = Definitions.APP_AST_DIFF + " -ast-dump-json "
    if use_macro:
        dump_command += " " + macro_list + "  "
    dump_command += file_path
    if file_path[-1] == 'h':
        dump_command += " --"
    dump_command += " 2> output/errors_AST_dump > " + json_file
    return_code = execute_command(dump_command)
    Emitter.debug("return code:" + str(return_code))
    if os.stat(json_file).st_size == 0:
        return None
    with io.open(json_file, 'r', encoding='utf8', errors="ignore") as f:
        ast_json = json.loads(f.read())
    return ast_json['root']


def generate_untracked_file_list(output_file_path, project_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    file_list = list()
    Emitter.normal("\t\texcluding untracked files...")
    list_command = 'cd ' + project_path+ ';'
    list_command += 'git ls-files --others --exclude-standard > ' +  output_file_path
    execute_command(list_command)
    Emitter.normal("\t\tuntracked files:")
    with open(output_file_path, 'r') as output_file:
        file_name = output_file.readline().strip()
        while file_name:
            Emitter.normal("\t\t\t" + file_name)
            file_list.append(file_name)
            file_name = output_file.readline().strip()
    if not file_list:
        Emitter.normal("\t\t\t-none-")
    return file_list
