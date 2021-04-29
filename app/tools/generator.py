#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io
import os

import json

import app.common.utilities
from app.common.utilities import execute_command, find_files, definitions, error_exit
from app.tools import merger, emitter
from app.tools import mapper, slicer, parallel, emitter, finder, extractor, logger
from app.ast import ast_vector, ast_generator
from app.common.utilities import error_exit
from app.common import values, utilities, definitions


def generate_slice_for_vector(vector_path, use_macro=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    source_file, segment = vector_path.split(".c.")
    source_file = source_file + ".c"
    seg_type = segment.replace(".vec", "").split("_")[0]
    segment_identifier = "_".join(segment.replace(".vec", "").split("_")[1:])
    slice_file = source_file + "." + seg_type + "." + segment_identifier + ".slice"
    project_path = app.common.utilities.extract_project_path(source_file)
    seg_found = slicer.slice_source_file(source_file, seg_type, segment_identifier,
                                         project_path,
                                         use_macro)
    if not seg_found and values.CONF_PATH_C in project_path:
        values.TARGET_REQUIRE_MACRO = True
        values.PRE_PROCESS_MACRO = values.TARGET_PRE_PROCESS_MACRO
        slicer.slice_source_file(source_file, seg_type, segment_identifier,
                                 project_path,
                                 True)
    if not os.path.isfile(slice_file) or os.stat(slice_file).st_size == 0:
        return None
    return slice_file


def generate_semantic_distance():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())


def generate_similarity_score(vector_path_a, vector_path_c):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    slice_file_a = generate_slice_for_vector(vector_path_a, values.DONOR_REQUIRE_MACRO)
    slice_file_c = generate_slice_for_vector(vector_path_c, values.TARGET_REQUIRE_MACRO)
    source_file_a = utilities.get_source_name_from_slice(slice_file_a)
    source_file_c = utilities.get_source_name_from_slice(slice_file_c)
    utilities.shift_per_slice(slice_file_a)
    utilities.shift_per_slice(slice_file_c)
    map_file_name = definitions.DIRECTORY_TMP + "/morph.map"
    segment_identifier_a = utilities.get_identifier_from_slice(slice_file_a)
    segment_identifier_c = utilities.get_identifier_from_slice(slice_file_c)
    ast_tree_a = ast_generator.get_ast_json(source_file_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_file_c, values.TARGET_REQUIRE_MACRO, regenerate=True)
    ast_node_a = finder.search_function_node_by_name(ast_tree_a, segment_identifier_a)
    ast_node_c = finder.search_function_node_by_name(ast_tree_c, segment_identifier_c)
    generate_map_gumtree(source_file_a, source_file_c, map_file_name)
    ast_node_map = parallel.read_mapping(map_file_name)
    utilities.restore_per_slice(slice_file_a)
    utilities.restore_per_slice(slice_file_c)
    if not ast_node_a or not ast_node_c:
        return 1.0
    id_list_a = extractor.extract_child_id_list(ast_node_a)
    id_list_c = extractor.extract_child_id_list(ast_node_c)

    node_size_a = len(id_list_a)
    node_size_c = len(id_list_c)
    match_count = 0
    for node_str_a in ast_node_map:
        node_id_a = utilities.id_from_string(node_str_a)
        if node_id_a in id_list_a:
            match_count = match_count + 1
    similarity = float(match_count / (node_size_a + node_size_c))
    emitter.information("Segment A Name: " + str(segment_identifier_a))
    emitter.information("Segment C Name: " + str(segment_identifier_c))
    emitter.information("Match Count: " + str(match_count))
    emitter.information("Size of A: " + str(node_size_a))
    emitter.information("Size of C: " + str(node_size_c))
    emitter.information("Similarity: " + str(similarity))

    return similarity


def find_source_file(diff_file_list, project, log_file, file_extension):
    emitter.normal("\t\t\tlocating source files")
    source_dir = None
    list_files = set()
    source_file_list = list()
    for source_loc in diff_file_list:
        file_path_list = set()
        source_path, line_number = source_loc.split(":")
        # source_path = source_path.replace(values.CONF_PATH_A, "")
        # source_path = source_path[1:]
        if source_path in source_file_list:
            continue
        source_file_list.append(source_path)
        clone_file = finder.find_clone(source_path)
        if clone_file:
            list_files.add(clone_file)
        # git_query = "cd " + values.CONF_PATH_A + ";"
        # result_file = definitions.DIRECTORY_TMP + "/list"
        # git_query += "git log --follow --pretty=\"\" --name-only " + source_path + " > " + result_file
        # execute_command(git_query)
        # with open(result_file, 'r') as tmp_file:
        #     list_lines = tmp_file.readlines()
        #     for path in list_lines:
        #         file_path_list.add(path.strip().replace("\n", ""))
        #
        # for file_path in file_path_list:
        #     new_path = project.path + "/" + file_path
        #     if os.path.isfile(new_path):
        #         list_files.add(new_path)
        #         break

        if not list_files:
            source_path = source_path.replace(values.CONF_PATH_A, "")
            source_path = source_path[1:]
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
    source_dir = source_dir.replace(values.CONF_PATH_A, "")
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
    heading = "generating neighborhoods"
    if use_macro:
        heading = heading + " using macros"
    emitter.normal("\t\t\t" + heading)
    function_list, definition_list = ast_generator.parse_ast(source_file, use_deckard=False, use_macro=use_macro, use_local=True)
    ast_tree = generate_ast_json(source_file, use_macro)
    if ast_tree is None:
        return None

    source_file_pattern = [source_file, source_file.split("/")[-1],
                           source_file.replace(values.Project_C.path, '')[1:], source_file.replace(
            values.Project_C.path, '')]
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
                        macro_value = ast_node["value"]
                        if "(" in macro_value:
                            macro_value = macro_value.split("(")[0]
                        macro_list.append((macro_value, ast_node["start line"], ast_node["end line"]))

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
            emitter.error("unknown node type for code segmentation: " + str(node_type))
            print(source_file, ast_node)

    return enum_list, function_list, macro_list, struct_list, type_def_list, def_list, decl_list, definition_list


def create_vectors(project, source_file, segmentation_list):
    project.enum_list[source_file] = dict()
    project.struct_list[source_file] = dict()
    project.function_list[source_file] = dict()
    project.macro_list[source_file] = dict()
    project.decl_list[source_file] = dict()
    emitter.normal("\t\t\tcreating vectors for neighborhoods")
    enum_list, function_list, macro_list, \
    struct_list, type_def_list, def_list, decl_list, definition_list = segmentation_list

    if values.IS_FUNCTION:
        # Emitter.normal("\t\t\tgenerating function vectors")
        vector_list_a = finder.search_vector_list(values.Project_A, "*.func_*\.vec", 'func')
        function_name_list_a = list()
        function_name_list_c = dict()

        for vector_a in vector_list_a:
            # Assume vector already created
            file_path_a = vector_a[0]
            source_a, function_name_a = file_path_a.split(".func_")
            function_name_list_a.append(function_name_a.replace(".vec", ""))
        for function_name, begin_line, finish_line in function_list:
            function_name_list_c[function_name] = (begin_line, finish_line)

        filtered_function_list = function_list
        if values.DEFAULT_OPERATION_MODE == 0:
            filtered_function_list = list()
            for function_name in function_name_list_a:
                if function_name in function_name_list_c.keys():
                    begin_line, finish_line = function_name_list_c[function_name]
                    filtered_function_list.append((function_name, begin_line, finish_line))
            if len(function_name_list_a) != len(filtered_function_list):
                filtered_function_list = function_list

        for function_name, begin_line, finish_line in filtered_function_list:
            function_name = "func_" + function_name.split("(")[0]
            project.function_list[source_file][function_name] = ast_vector.Vector(source_file, function_name,
                                                                                  begin_line,
                                                                                  finish_line, True)

        ast_generator.get_vars(project, source_file, definition_list)

    if values.IS_STRUCT:
        # Emitter.normal("\t\t\tgenerating struct vectors")
        for struct_name, begin_line, finish_line in struct_list:
            struct_name = "struct_" + struct_name.split(";")[0]
            project.struct_list[source_file][struct_name] = ast_vector.Vector(source_file, struct_name, begin_line,
                                                                              finish_line, True)

    if values.IS_TYPEDEC:
        # Emitter.normal("\t\t\tgenerating struct vectors")
        for var_name, begin_line, finish_line in decl_list:
            var_name = "var_" + var_name.split(";")[0]
            var_type = (var_name.split("(")[1]).split(")")[0]
            var_name = var_name.split("(")[0]
            project.decl_list[source_file][var_name] = ast_vector.Vector(source_file, var_name, begin_line, finish_line,
                                                                         True)

    if values.IS_MACRO:
        # Emitter.normal("\t\t\tgenerating macro vectors")
        for macro_name, begin_line, finish_line in macro_list:
            macro_name = "macro_" + macro_name
            project.macro_list[source_file][macro_name] = ast_vector.Vector(source_file, macro_name, begin_line,
                                                                            finish_line, True)

    if values.IS_ENUM:
        # Emitter.normal("\t\t\tgenerating enum vectors")
        count = 0
        for enum_name, begin_line, finish_line in enum_list:
            enum_name = "enum_" + enum_name.split(";")[0]
            if "anonymous" in enum_name:
                count = count + 1
                enum_name = "enum_" + str(count)
            project.enum_list[source_file][enum_name] = ast_vector.Vector(source_file, enum_name, begin_line,
                                                                          finish_line,
                                                                          True)


def generate_vectors(file_extension, log_file, project, diff_file_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tgenerating vectors for " + file_extension + " files in " + project.name + "...")
    # Generates an AST file for each file of extension ext

    # intelligently generate vectors
    regex = None
    if values.IS_BACKPORT or values.IS_FORK:
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
            values.TARGET_PRE_PROCESS_MACRO = extractor.extract_pre_macro_command(source_file)

            try:
                segmentation_list = generate_segmentation(source_file)
                if segmentation_list is None:
                    source_file = file_list.readline().strip()
                    continue
                segmentation_list_macro = generate_segmentation(source_file, True)
                if segmentation_list_macro:
                    segmentation_list = merger.merge_segmentation_list(segmentation_list, segmentation_list_macro)
                create_vectors(project, source_file, segmentation_list)

            except Exception as e:
                error_exit(e, "Unexpected error in parseAST with file:", source_file)
            source_file = file_list.readline().strip()


def generate_ast_json(file_path, use_macro=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    json_file = file_path + ".AST"
    macro_list = values.TARGET_PRE_PROCESS_MACRO
    if values.CONF_PATH_A in file_path:
        macro_list = values.DONOR_PRE_PROCESS_MACRO
    dump_command = definitions.APP_AST_DIFF + " -ast-dump-json "
    if use_macro:
        if values.CONF_PATH_A in file_path or values.CONF_PATH_B in file_path:
            dump_command += " " + values.DONOR_PRE_PROCESS_MACRO.replace("--extra-arg-a", "--extra-arg") + "  "
        else:
            dump_command += " " + values.TARGET_PRE_PROCESS_MACRO.replace("--extra-arg-c", "--extra-arg") + "  "
    dump_command += file_path
    if file_path[-1] == 'h':
        dump_command += " --"

    error_file = definitions.DIRECTORY_OUTPUT + "/errors_AST_dump"
    dump_command += " 2> " + error_file + " > " + json_file

    return_code = execute_command(dump_command)
    emitter.debug("return code:" + str(return_code))
    if os.stat(json_file).st_size == 0:
        return None
    with io.open(json_file, 'r', encoding='utf8', errors="ignore") as f:
        ast_json = json.loads(f.read())
    return ast_json['root']


def generate_untracked_file_list(output_file_path, project_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    file_list = list()
    emitter.normal("\t\texcluding untracked files...")
    list_command = 'cd ' + project_path+ ';'
    list_command += 'git ls-files --others --exclude-standard > ' +  output_file_path
    execute_command(list_command)
    emitter.normal("\t\tuntracked files:")
    with open(output_file_path, 'r') as output_file:
        file_name = output_file.readline().strip()
        while file_name:
            emitter.normal("\t\t\t" + file_name)
            file_list.append(file_name)
            file_name = output_file.readline().strip()
    if not file_list:
        emitter.normal("\t\t\t-none-")
    return file_list


def generate_edit_script(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    emitter.normal("\t\t\tgenerating transformation script")
    try:
        extra_arg = ""
        if file_a[-1] == 'h':
            extra_arg = " --"
        command = definitions.DIFF_COMMAND + " -s=" + definitions.DIFF_SIZE + " -dump-matches "
        if values.DONOR_REQUIRE_MACRO:
            command += " " + values.DONOR_PRE_PROCESS_MACRO + " "
            command += " " + values.DONOR_PRE_PROCESS_MACRO.replace("--extra-arg-a", "--extra-arg-c") + " "
        command += file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating edit script: " + output_file)


def generate_edit_diff(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    emitter.normal("\t\t\tgenerating edit diff")
    try:
        command = definitions.LINUX_DIFF_COMMAND
        if values.DEFAULT_OPERATION_MODE == 2:
            command += " --context=" + str(values.DEFAULT_CONTEXT_LEVEL) + " "
        command += file_a + " " + file_b + " 2> output/errors_linux_diff "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating edit script: " + output_file)


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
        generate_command = definitions.DIFF_COMMAND + " -s=" + definitions.DIFF_SIZE + " -dump-matches "
        if values.DONOR_REQUIRE_MACRO:
            generate_command += " " + values.DONOR_PRE_PROCESS_MACRO + " "
            if values.CONF_PATH_B in file_b:
                generate_command += " " + values.DONOR_PRE_PROCESS_MACRO.replace("--extra-arg-a", "--extra-arg-c") + " "
        if values.TARGET_REQUIRE_MACRO:
            if values.CONF_PATH_C in file_b:
                generate_command += " " + values.TARGET_PRE_PROCESS_MACRO + " "
        generate_command += file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        # command += "| grep '^Match ' "
        generate_command += " > " + output_file
        execute_command(generate_command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating map: " + output_file)