# -*- coding: utf-8 -*-

''' Main vector generation functions '''

from common.Utilities import error_exit, execute_command, backup_file, restore_file
from ast import Vector, AST
from tools import Logger, Emitter
import sys
from common import Definitions, Values
import json
import os
import io

APP_FORMAT_LLVM = "clang-format -style=LLVM "
APP_AST_DIFF = "crochet-diff"

interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

skip_name_list = ["test", "tests", 'thirdparty', 'cmake', 'CMakeFiles']


def generate_vector(file_path, f_or_struct, start_line, end_line, is_deckard=True):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    v = Vector.Vector(file_path, f_or_struct, start_line, end_line, is_deckard)
    if not v.vector:
        return None
    # if file_path in proj_attribute.keys():
    #     proj_attribute[file_path][f_or_struct] = v
    # else:
    #     proj_attribute[file_path] = dict()
    #     proj_attribute[file_path][f_or_struct] = v
    return v


def ast_dump(file_path, output_path, is_header=True, use_macro=False):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    dump_command = APP_AST_DIFF + " -ast-dump-json "
    if use_macro:
        dump_command += " " + Values.PRE_PROCESS_MACRO + "  "
    dump_command += file_path
    if file_path[-1] == 'h':
        dump_command += " --"
    error_file = Definitions.DIRECTORY_OUTPUT + "/errors_AST_dump"
    dump_command += " 2> " + error_file + " > " + output_path
    return_code = execute_command(dump_command)
    Emitter.debug("return code:" + str(return_code))
    return return_code


def get_ast_json(file_path, use_macro=False, regenerate=False):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    json_file = file_path + ".AST"
    if not (os.path.exists(json_file) and not Values.USE_CACHE) or regenerate:
        generate_json(file_path, use_macro)
    # ast_dump(file_path, json_file, False, use_macro)
    if os.stat(json_file).st_size == 0:
        return None
    with io.open(json_file, 'r', encoding='utf8', errors="ignore") as f:
        ast_json = json.loads(f.read())
    return ast_json['root']


def generate_json(file_path, use_macro=False):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    json_file = file_path + ".AST"
    if not os.path.exists(json_file) and not Values.USE_CACHE:
        ast_dump(file_path, json_file, False, use_macro)
    return AST.load_from_file(json_file)


def convert_to_llvm(file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    try:
        backup_name = "last.c"
        convert_file_path = Definitions.DIRECTORY_OUTPUT + "/temp_llvm.c"
        backup_file(file_path, backup_name)
        format_command = APP_FORMAT_LLVM + file_path + "> " + convert_file_path + " 2>" + Definitions.FILE_ERROR_LOG
        replace_command = format_command + ";" + "cp " + convert_file_path + " " + file_path
        execute_command(replace_command)
    except Exception as exception:
        Emitter.warning(exception)
        Emitter.warning("error in llvm_format with file:")
        Emitter.warning(file_path)
        Emitter.warning("restoring and skipping")
        restore_file(file_path, backup_name)


def parse_ast(file_path, use_deckard=True, use_macro=False):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    # convert_to_llvm(file_path)
    # Save functions here
    function_lines = list()
    # Save variables for each function d[function] = "typevar namevar; ...;"
    dict_file = dict()

    if any(skip_word in str(file_path).lower() for skip_word in skip_name_list):
        return function_lines, dict_file
    try:
        ast = generate_json(file_path, use_macro)
    except Exception as exception:
        # print(exception)
        Emitter.warning("\t\t[warning] failed parsing AST for file: " + file_path)
        return function_lines, dict_file

    start_line = 0
    end_line = 0
    file_line = file_path.split("/")[-1]

    function_nodes = []
    root = ast[0]
    root.get_node_list("type", "FunctionDecl", function_nodes)
    for node in function_nodes:
        set_struct_nodes = set()
        # Output.yellow(node.file)
        if node.file is not None and file_line == node.file.split("/")[-1]:
            f = node.value.split("(")[0]
            start_line = int(node.line)
            end_line = int(node.line_end)
            function_lines.append((f, start_line, end_line))
            generate_vector(file_path, f, start_line, end_line, use_deckard)
            structural_nodes = []
            for interesting_type in interesting:
                node.get_node_list("type", interesting_type, structural_nodes)
            for struct_node in structural_nodes:
                var = struct_node.value.split("(")
                var_type = var[-1][:-1]
                var = var[0]
                line = var_type + " " + var + ";"
                if f not in dict_file.keys():
                    dict_file[f] = ""
                dict_file[f] = dict_file[f] + line
                set_struct_nodes.add(struct_node.value)

        # if use_deckard:
        #     get_vars(project, file_path, dict_file)
        #     print("")

    return function_lines, dict_file


def get_vars(proj, file, dict_file):
    for func in dict_file.keys():
        for line in dict_file[func].split(";"):
            if file in proj.function_list.keys():
                if func in proj.function_list[file].keys():
                    proj.function_list[file][func].variables.append(line)


def is_intersect(start, end, start2, end2):
    return not (end2 < start or start2 > end)


def generate_ast_script(source_a, source_b, outfile_path, dump_matches=False):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    extra_args = " "
    if dump_matches:
        extra_args = " -dump-matches "
    generate_command = APP_AST_DIFF + " -s=" + Values.AST_DIFF_SIZE + extra_args
    generate_command += source_a + " " + source_b
    if source_a[-1] == 'h':
        generate_command += " --"
    generate_command += " 2> " + Definitions.FILE_AST_DIFF_ERROR
    if dump_matches:
        generate_command += " | grep -P '^Match ' | grep -P '^Match '"
    generate_command += " > " + outfile_path

    try:
        # print(generate_command)
        execute_command(generate_command, False)
    except Exception as exception:
        error_exit(exception, "Unexpected error in generate_ast_script.")


def generate_function_list(project, source_file):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    function_list = dict()
    definition_list = dict()
    try:
        function_list, definition_list = parse_ast(source_file, False)
    except Exception as e:
        error_exit(e, "Error in parse_ast.")

    project.function_list[source_file] = dict()
    for function_name, begin_line, finish_line in function_list:
        if function_name not in project.function_list[source_file]:
            project.function_list[source_file][function_name] = Vector.Vector(source_file, function_name, begin_line, finish_line, True)
    get_vars(project, source_file, definition_list)


def get_function_list_for_line_range(project, source_file, pertinent_lines):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\t\t" + project.path + ":")
    function_list = dict()
    definition_list = dict()
    try:
        function_list, definition_list = parse_ast(source_file, False)
    except Exception as e:
        error_exit(e, "Error in parse_ast.")

    for start_line, end_line in pertinent_lines:
        for function_name, begin_line, finish_line in function_list:
            if is_intersect(begin_line, finish_line, start_line, end_line):
                if source_file not in project.function_list.keys():
                    project.function_list[source_file] = dict()

                if function_name not in project.function_list[source_file]:
                    project.function_list[source_file][function_name] = Vector.Vector(source_file, function_name,
                                                                                     begin_line, finish_line, True)
                    Emitter.normal(
                        "\t\t\t" + function_name + " in " + source_file.replace(project.path, project.name + "/"))
                    Emitter.normal("\t\t\t" + function_name + " " + str(begin_line) + "-" + str(finish_line), False)
                break

    get_vars(project, source_file, definition_list)
    return function_list, definition_list
