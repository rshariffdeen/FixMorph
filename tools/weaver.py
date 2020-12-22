from common import definitions, values
from common.utilities import execute_command, error_exit, get_code, backup_file, show_partial_diff, backup_file_orig, restore_file_orig, replace_file, get_code_range
from tools import emitter, logger, finder, extractor, identifier
from ast import Generator

import os
import sys

file_index = 1
backup_file_list = dict()
FILENAME_BACKUP = "temp-source"
TOOL_AST_PATCH = "patchweave"


def restore_files():
    global backup_file_list
    emitter.warning("Restoring files...")
    for b_file in backup_file_list.keys():
        backup_file = backup_file_list[b_file]
        backup_command = "cp backup/" + backup_file + " " + b_file
        execute_command(backup_command)
    emitter.warning("Files restored")


def execute_ast_transformation(script_path, source_file_info):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    file_a, file_b, file_c, file_d = source_file_info
    emitter.normal("\t[action] executing AST transformation")

    output_file = definitions.DIRECTORY_OUTPUT + str(file_index) + "_temp." + file_c[-1]
    backup_command = ""
    # We add file_c into our dict (changes) to be able to backup and copy it

    if file_c not in backup_file_list.keys():
        filename = file_c.split("/")[-1]
        backup_file = str(file_index) + "_" + filename
        backup_file_list[file_c] = backup_file
        backup_command += "cp " + file_c + " " + definitions.DIRECTORY_BACKUP + "/" + backup_file
    # print(backup_command)
    execute_command(backup_command)

    parameters = " -s=" + definitions.PATCH_SIZE

    if values.DONOR_REQUIRE_MACRO:
        parameters += " " + values.DONOR_PRE_PROCESS_MACRO + " "

    if values.TARGET_REQUIRE_MACRO:
        parameters += " " + values.TARGET_PRE_PROCESS_MACRO + " "

    parameters += " -script=" + script_path + " -source=" + file_a
    parameters += " -destination=" + file_b + " -target=" + file_c
    parameters += " -map=" + definitions.FILE_NAMESPACE_MAP

    patch_command = definitions.PATCH_COMMAND + parameters + " > " + definitions.FILE_TEMP_FIX

    ret_code = int(execute_command(patch_command))

    if ret_code == 0:
        move_command = "cp " + definitions.FILE_TEMP_FIX + " " + file_d
        execute_command(move_command)
        show_partial_diff(file_c, file_d)

    else:
        error_exit("\t AST transformation FAILED")

    if os.stat(file_d).st_size == 0:
        error_exit("\t AST transformation FAILED")

    if values.BREAK_WEAVE:
        exit()

    return ret_code


def show_patch(file_a, file_b, file_c, file_d, index):
    emitter.highlight("\tOriginal Patch")
    original_patch_file_name = definitions.DIRECTORY_OUTPUT + "/" + index + "-original-patch"
    generated_patch_file_name = definitions.DIRECTORY_OUTPUT + "/" + index + "-generated-patch"
    diff_command = "diff -ENZBbwr " + file_a + " " + file_b + " > " + original_patch_file_name
    execute_command(diff_command)
    with open(original_patch_file_name, 'r', encoding='utf8', errors="ignore") as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            emitter.special("\t\t" + diff_line)
            diff_line = diff.readline().strip()

    emitter.highlight("\tGenerated Patch")
    diff_command = "diff -ENZBbwr " + file_c + " " + file_d + " > " + generated_patch_file_name
    # print(diff_command)
    execute_command(diff_command)
    with open(generated_patch_file_name, 'r', encoding='utf8', errors="ignore") as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            emitter.special("\t\t" + diff_line)
            diff_line = diff.readline().strip()


def insert_code(patch_code, source_path, line_number):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = ""
    if os.path.exists(source_path):
        with open(source_path, 'r', encoding='utf8', errors="ignore") as source_file:
            content = source_file.readlines()
            existing_statement = content[line_number]
            content[line_number] = patch_code + existing_statement

    with open(source_path, 'w', encoding='utf8', errors="ignore") as source_file:
        source_file.writelines(content)


def insert_code_range(patch_code, source_path, line_number):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = ""
    emitter.information("inserting code at line " + str(line_number) + " in " + source_path)
    if os.path.exists(source_path):
        with open(source_path, 'r', encoding='utf8', errors="ignore") as source_file:
            content = source_file.readlines()

    updated_content = content[:line_number-1] + patch_code + content[line_number-1:]
    # print(set(updated_content) - set(content))
    with open(source_path, 'w', encoding='utf8', errors="ignore") as source_file:
        source_file.writelines(updated_content)


def delete_code(source_path, start_line, end_line):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = ""
    emitter.information("deleting lines " + str(start_line) + "-" + str(end_line) + " in " + source_path)
    if os.path.exists(source_path):
        with open(source_path, 'r+', encoding='utf8', errors="ignore") as source_file:
            content = source_file.readlines()
            source_file.seek(0)
            source_file.truncate()
    original_content = content
    del content[start_line-1:end_line]
    # print(set(original_content) - set(content))
    with open(source_path, 'w', encoding='utf8', errors="ignore") as source_file:
        source_file.writelines(content)


def weave_headers(missing_header_list, modified_source_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_header_list:
        emitter.normal("\t-none-")
    target_file = ""
    for header_name in missing_header_list:
        emitter.normal(header_name)
        target_file = missing_header_list[header_name]
        if "/" in header_name:
            transplant_code = "\n#include<" + header_name + ">\n"
        else:
            transplant_code = "\n#include \"" + header_name + "\"\n"
        def_insert_line = finder.find_definition_insertion_point(target_file)
        backup_file(target_file, FILENAME_BACKUP)
        insert_code(transplant_code, target_file, def_insert_line)
        if target_file not in modified_source_list:
            modified_source_list.append(target_file)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, target_file)

    # for source_file_c in modified_source_list:
    #     source_file_a = None
    #     for path_a, path_c in Values.VECTOR_MAP:
    #         if source_file_c in path_c:
    #             source_file_a = path_a.split(".c.")[0] + ".c"
    #     if source_file_a:
    #         added_header_list = Values.Project_A.header_list[source_file_a]['added']
    #         for header_name in added_header_list:
    #             Emitter.normal(header_name)
    #             target_file = source_file_c
    #             transplant_code = "\n#include<" + header_name + ">\n"
    #             def_insert_line = Finder.find_definition_insertion_point(target_file)
    #             backup_file(target_file, FILENAME_BACKUP)
    #             insert_code(transplant_code, target_file, def_insert_line)
    #             if target_file not in modified_source_list:
    #                 modified_source_list.append(target_file)
    #             backup_file_path = Definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
    #             show_partial_diff(backup_file_path, target_file)

    return modified_source_list


def weave_definitions(missing_definition_list, modified_source_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_definition_list:
        emitter.normal("\t-none-")
    for def_name in missing_definition_list:
        emitter.normal(def_name)
        macro_info = missing_definition_list[def_name]
        source_file = macro_info['source']
        target_file = macro_info['target']
        macro_def_list = extractor.extract_macro_definitions(source_file)
        def_insert_line = finder.find_definition_insertion_point(target_file)
        transplant_code = ""
        for macro_def in macro_def_list:
            if def_name in macro_def:
                if "#define" in macro_def:
                    if def_name in macro_def.split(" "):
                        transplant_code += "\n" + macro_def + "\n"

        if transplant_code == "" and not values.BACKPORT:
            header_file = finder.find_header_file(def_name, source_file)
            # print(header_file)
            if header_file is not None:
                macro_def_list = extractor.extract_macro_definitions(header_file)
                # print(macro_def_list)
                transplant_code = ""
                for macro_def in macro_def_list:
                    if def_name in macro_def:
                        # print(macro_def)
                        if "#define" in macro_def:
                            if def_name in macro_def.split(" "):
                                transplant_code += "\n" + macro_def + "\n"
                            elif str(macro_def).count(def_name) == 1:
                                transplant_code += "\n" + macro_def + "\n"

        backup_file(target_file, FILENAME_BACKUP)
        insert_code(transplant_code, target_file, def_insert_line)
        if target_file not in modified_source_list:
            modified_source_list.append(target_file)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, target_file)
    return modified_source_list


def weave_data_type(missing_data_type_list, modified_source_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_data_type_list:
        emitter.normal("\t-none-")

    for data_type in missing_data_type_list:
        emitter.normal(data_type)
        data_type_info = missing_data_type_list[data_type]
        ast_node = data_type_info['ast-node']
        def_start_line = int(ast_node['start line'])
        def_end_line = int(ast_node['end line'])
        source_file = ast_node['file']
        target_file = data_type_info['target']
        def_insert_line = finder.find_definition_insertion_point(target_file)
        transplant_code = "\n"
        for i in range(def_start_line, def_end_line + 1, 1):
            transplant_code += get_code(source_file, int(i))
        transplant_code += "\n"
        backup_file(target_file, FILENAME_BACKUP)
        insert_code(transplant_code, target_file, def_insert_line)
        if target_file not in modified_source_list:
            modified_source_list.append(target_file)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, target_file)
    return modified_source_list


def weave_functions(missing_function_list, modified_source_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_function_list:
        emitter.normal("\t-none-")
    def_insert_point = ""
    missing_header_list = dict()
    missing_macro_list = dict()
    for function_name in missing_function_list:
        info = missing_function_list[function_name]
        node_id = info['node_id']
        source_path_b = info['source_b']
        source_path_d = info['source_d']
        emitter.normal(function_name)
        ast_map_b = Generator.get_ast_json(source_path_b)
        function_ref_node_id = int(info['ref_node_id'])
        function_ref_node = finder.search_ast_node_by_id(ast_map_b, function_ref_node_id)
        function_def_node = finder.search_ast_node_by_id(ast_map_b, int(node_id))
        function_node, function_source_file = extractor.extract_complete_function_node(function_def_node,
                                                                                       source_path_b)
        def_insert_point = finder.find_definition_insertion_point(source_path_d)

        start_line = function_node["start line"]
        end_line = function_node["end line"]
        # print(function_name)
        original_function = ""
        for i in range(int(start_line), int(end_line + 1)):
            original_function += get_code(function_source_file, int(i)) + "\n"
        # translated_patch = translate_patch(original_patch, var_map_ac)
        backup_file(source_path_d, FILENAME_BACKUP)
        insert_code(original_function, source_path_d, def_insert_point)
        if source_path_d not in modified_source_list:
            modified_source_list.append(source_path_d)
        backup_file_path = definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_path_d)
    return modified_source_list


def weave_code(file_a, file_b, file_c, script_file_name, modified_source_list):
    if values.DONOR_REQUIRE_MACRO:
        values.PRE_PROCESS_MACRO = values.DONOR_PRE_PROCESS_MACRO
    if values.TARGET_REQUIRE_MACRO:
        values.PRE_PROCESS_MACRO = values.TARGET_PRE_PROCESS_MACRO

    file_d = str(file_c).replace(values.Project_C.path, values.Project_D.path)

    # Check for an edit script
    # script_file_name = Definitions.DIRECTORY_OUTPUT + "/" + str(file_index) + "_script"
    syntax_error_file_name = definitions.DIRECTORY_OUTPUT + "/" + str(file_index) + "_syntax_errors"

    file_info = file_a, file_b, file_c, file_d
    execute_ast_transformation(script_file_name, file_info)
    # We fix basic syntax errors that could have been introduced by the patch
    fix_command = definitions.SYNTAX_CHECK_COMMAND + "-fixit " + file_d

    if file_c[-1] == 'h':
        fix_command += " --"
    fix_command += " 2>" + syntax_error_file_name
    execute_command(fix_command)

    if file_d not in modified_source_list:
        modified_source_list.append(file_d)

    emitter.success("\n\tSuccessful transformation")
    return modified_source_list


def weave_slice(slice_info):
    for source_file_d, source_file_b in slice_info:
        source_file_c = source_file_d.replace(values.Project_D.path, values.PATH_C)
        emitter.normal("\t\t" + source_file_d)
        slice_list = slice_info[(source_file_d, source_file_b)]
        weave_list = dict()
        for slice_file in slice_list:
            segment_code = slice_file.replace(source_file_d + ".", "").split(".")[0]
            segment_identifier = slice_file.split("." + segment_code + ".")[-1].replace(".slice", "")
            emitter.normal("\t\t\tweaving slice " + segment_identifier)
            segment_type = values.segment_map[segment_code]
            backup_file_orig(source_file_d)
            replace_file(slice_file, source_file_d)
            if values.TARGET_REQUIRE_MACRO:
                values.PRE_PROCESS_MACRO = values.TARGET_PRE_PROCESS_MACRO
            ast_tree_slice = Generator.get_ast_json(source_file_d, values.TARGET_REQUIRE_MACRO, True)
            restore_file_orig(source_file_d)
            ast_tree_source = Generator.get_ast_json(source_file_d, values.TARGET_REQUIRE_MACRO, True)
            segment_node_slice = finder.search_node(ast_tree_slice, segment_type, segment_identifier)
            segment_node_source = finder.search_node(ast_tree_source, segment_type, segment_identifier)
            start_line_source = int(segment_node_source['start line'])
            end_line_source = int(segment_node_source['end line'])
            start_line_slice = int(segment_node_slice['start line'])
            end_line_slice = int(segment_node_slice['end line'])
            weave_list[start_line_source] = (slice_file, end_line_source, start_line_slice, end_line_slice)

        for start_line_source in reversed(sorted(weave_list.keys())):
            slice_file, end_line_source, start_line_slice, end_line_slice = weave_list[start_line_source]
            slice_code = get_code_range(slice_file, start_line_slice, end_line_slice)
            delete_code(source_file_d, start_line_source, end_line_source)
            insert_code_range(slice_code, source_file_d, start_line_source)

        source_file_a = source_file_b.replace(values.PATH_B, values.PATH_A)
        show_patch(source_file_a, source_file_b, source_file_c, source_file_d, segment_identifier)
