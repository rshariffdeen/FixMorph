from common import Definitions, Values
from common.Utilities import execute_command, error_exit, get_code, backup_file, show_partial_diff
from tools import Emitter, Logger, Finder, Extractor, Identifier
from ast import Generator
import os
import sys

file_index = 1
backup_file_list = dict()
FILENAME_BACKUP = "temp-source"
TOOL_AST_PATCH = "patchweave"
FILE_TEMP_FIX = Definitions.DIRECTORY_TMP + "/temp-fix"


def restore_files():
    global backup_file_list
    Emitter.warning("Restoring files...")
    for b_file in backup_file_list.keys():
        backup_file = backup_file_list[b_file]
        backup_command = "cp backup/" + backup_file + " " + b_file
        execute_command(backup_command)
    Emitter.warning("Files restored")


def execute_ast_transformation(source_path_b, source_path_d, file_info):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    skip_file, ast_script_file, var_map_file = file_info
    Emitter.normal("\t\texecuting AST transformation")
    parameters = " -map=" + var_map_file + " -script=" + ast_script_file
    parameters += " -source=" + source_path_b + " -target=" + source_path_d
    parameters += " -skip-list=" + skip_file
    transform_command = TOOL_AST_PATCH + parameters + " > " + FILE_TEMP_FIX
    ret_code = int(execute_command(transform_command))
    if ret_code == 0:
        move_command = "cp " + FILE_TEMP_FIX + " " + source_path_d
        show_partial_diff(source_path_d, FILE_TEMP_FIX)
        execute_command(move_command)
    else:
        error_exit("\t AST transformation FAILED")
    return ret_code


def show_patch(file_a, file_b, file_c, file_d, index):
    Emitter.special("Original Patch")
    original_patch_file_name = Definitions.DIRECTORY_OUTPUT + index + "-original-patch"
    generated_patch_file_name = Definitions.DIRECTORY_OUTPUT + index + "-generated-patch"
    diff_command = "diff -ENZBbwr " + file_a + " " + file_b + " > " + original_patch_file_name
    execute_command(diff_command)
    with open(original_patch_file_name, 'r') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Emitter.special("\t" + diff_line)
            diff_line = diff.readline().strip()

    Emitter.special("Generated Patch")
    diff_command = "diff -ENZBbwr " + file_c + " " + file_d + " > " + generated_patch_file_name
    # print(diff_command)
    execute_command(diff_command)
    with open(generated_patch_file_name, 'r') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Emitter.special("\t" + diff_line)
            diff_line = diff.readline().strip()


def insert_code(patch_code, source_path, line_number):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = ""
    if os.path.exists(source_path):
        with open(source_path, 'r') as source_file:
            content = source_file.readlines()
            existing_statement = content[line_number]
            content[line_number] = patch_code + existing_statement

    with open(source_path, 'w') as source_file:
        source_file.writelines(content)


def weave_headers(missing_header_list, modified_source_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_header_list:
        Emitter.normal("\t-none-")
    for header_name in missing_header_list:
        Emitter.normal(header_name)
        target_file = missing_header_list[header_name]
        transplant_code = "\n#include<" + header_name + ">\n"
        def_insert_line = Finder.find_definition_insertion_point(target_file)
        backup_file(target_file, FILENAME_BACKUP)
        insert_code(transplant_code, target_file, def_insert_line)
        if target_file not in modified_source_list:
            modified_source_list.append(target_file)
        backup_file_path = Definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, target_file)
    return modified_source_list


def weave_definitions(missing_definition_list, modified_source_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_definition_list:
        Emitter.normal("\t-none-")
    for def_name in missing_definition_list:
        Emitter.normal(def_name)
        macro_info = missing_definition_list[def_name]
        source_file = macro_info['source']
        target_file = macro_info['target']
        macro_def_list = Extractor.extract_macro_definitions(source_file)
        def_insert_line = Finder.find_definition_insertion_point(target_file)
        transplant_code = ""
        for macro_def in macro_def_list:
            if def_name in macro_def:
                if "#define" in macro_def:
                    if def_name in macro_def.split(" "):
                        transplant_code += "\n" + macro_def + "\n"

        if transplant_code == "" and not Values.BACKPORT:
            header_file = Finder.find_header_file(def_name, source_file)
            # print(header_file)
            if header_file is not None:
                macro_def_list = Extractor.extract_macro_definitions(header_file)
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
        backup_file_path = Definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, target_file)
    return modified_source_list


def weave_data_type(missing_data_type_list, modified_source_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_data_type_list:
        Emitter.normal("\t-none-")

    for data_type in missing_data_type_list:
        Emitter.normal(data_type)
        data_type_info = missing_data_type_list[data_type]
        ast_node = data_type_info['ast-node']
        def_start_line = int(ast_node['start line'])
        def_end_line = int(ast_node['end line'])
        source_file = ast_node['file']
        target_file = data_type_info['target']
        def_insert_line = Finder.find_definition_insertion_point(target_file)
        transplant_code = "\n"
        for i in range(def_start_line, def_end_line + 1, 1):
            transplant_code += get_code(source_file, int(i))
        transplant_code += "\n"
        backup_file(target_file, FILENAME_BACKUP)
        insert_code(transplant_code, target_file, def_insert_line)
        if target_file not in modified_source_list:
            modified_source_list.append(target_file)
        backup_file_path = Definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, target_file)
    return modified_source_list


def weave_functions(missing_function_list, modified_source_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_function_list:
        Emitter.normal("\t-none-")
    def_insert_point = ""
    missing_header_list = dict()
    missing_macro_list = dict()
    for function_name in missing_function_list:
        info = missing_function_list[function_name]
        node_id = info['node_id']
        source_path_b = info['source_b']
        source_path_d = info['source_d']
        Emitter.normal(function_name)
        ast_map_b = Generator.get_ast_json(source_path_b)
        function_ref_node_id = int(info['ref_node_id'])
        function_ref_node = Finder.search_ast_node_by_id(ast_map_b, function_ref_node_id)
        function_def_node = Finder.search_ast_node_by_id(ast_map_b, int(node_id))
        function_node, function_source_file = Extractor.extract_complete_function_node(function_def_node,
                                                                                       source_path_b)
        missing_def_list = Identifier.identify_missing_definitions(function_node, missing_function_list)
        def_insert_point = Finder.find_definition_insertion_point(source_path_d)

        missing_macro_list = Identifier.identify_missing_macros_in_func(function_node, function_source_file,
                                                                        source_path_d)
        missing_header_list = Identifier.identify_missing_headers(function_node, source_path_d)
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
        backup_file_path = Definitions.DIRECTORY_BACKUP + "/" + FILENAME_BACKUP
        show_partial_diff(backup_file_path, source_path_d)

    return missing_header_list, missing_macro_list, modified_source_list


def weave_code(file_a, file_b, file_c, instruction_list):
    missing_function_list = dict()
    missing_var_list = dict()
    missing_macro_list = dict()
    missing_header_list = dict()
    missing_data_type_list = dict()

    ast_map_a = Generator.get_ast_json(file_a)
    ast_map_b = Generator.get_ast_json(file_b)
    ast_map_c = Generator.get_ast_json(file_c)

    file_d = str(file_c).replace(Values.Project_C.path, Values.Project_D.path)

    # Check for an edit script
    script_file_name = Definitions.DIRECTORY_OUTPUT + str(file_index) + "_script"
    syntax_error_file_name = Definitions.DIRECTORY_OUTPUT + str(file_index) + "_syntax_errors"
    with open(script_file_name, 'w') as script_file:
        for instruction in instruction_list:
            if "Insert" in instruction:
                insert_node_id = instruction.split("(")[1].split(")")[0]
                inserting_node = Finder.search_ast_node_by_id(ast_map_b, int(insert_node_id))
                missing_function_list.update(Identifier.identify_missing_functions(ast_map_a,
                                                                                   inserting_node,
                                                                                   file_b,
                                                                                   file_d,
                                                                                   ast_map_c))

                missing_macro_list.update(Identifier.identify_missing_macros(inserting_node,
                                                                             file_b,
                                                                             file_d
                                                                             ))

            script_file.write(instruction + "\n")

    output_file = Definitions.DIRECTORY_OUTPUT + str(file_index) + "_temp." + file_c[-1]
    backup_command = ""
    # We add file_c into our dict (changes) to be able to backup and copy it

    if file_c not in backup_file_list.keys():
        filename = file_c.split("/")[-1]
        backup_file = str(file_index) + "_" + filename
        backup_file_list[file_c] = backup_file
        backup_command += "cp " + file_c + " " + Definitions.DIRECTORY_BACKUP + "/" + backup_file
    # print(backup_command)
    execute_command(backup_command)

    # We apply the patch using the script and crochet-patch
    patch_command = Definitions.PATCH_COMMAND + " -s=" + Definitions.PATCH_SIZE + \
         " -script=" + script_file_name + " -source=" + file_a + \
         " -destination=" + file_b + " -target=" + file_c
    if file_c[-1] == "h":
        patch_command += " --"
    patch_command += " 2> output/errors > " + output_file + "; "
    patch_command += "cp " + output_file + " " + file_d

    # print(patch_command)
    execute_command(patch_command)

    # We fix basic syntax errors that could have been introduced by the patch
    fix_command = Definitions.SYNTAX_CHECK_COMMAND + "-fixit " + file_d
    if file_c[-1] == "h":
        fix_command += " --"
    fix_command += " 2>" + syntax_error_file_name
    execute_command(fix_command)

    # # We check that everything went fine, otherwise, we restore everything
    # try:
    #     check_command = Definitions.SYNTAX_CHECK_COMMAND + file_d + " 2>" + syntax_error_file_name
    #     if file_c[-1] == "h":
    #         check_command += " --"
    #     execute_command(check_command)
    # except Exception as e:
    #     Emitter.error("Clang-check could not repair syntax errors.")
    #     restore_files()
    #     error_exit(e, "Crochet failed.")

    # # We format the file to be with proper spacing (needed?)
    # format_command = Definitions.STYLE_FORMAT_COMMAND + file_c
    # if file_c[-1] == "h":
    #     format_command += " --"
    # format_command += " > " + output_file + "; "
    # execute_command(format_command)
    show_patch(file_a, file_b, file_c, file_d, str(file_index))
    #
    # c5 = "cp " + output_file + " " + file_c + ";"
    # execute_command(c5)

    Emitter.success("\n\tSuccessful transformation")
    return missing_function_list, missing_macro_list
