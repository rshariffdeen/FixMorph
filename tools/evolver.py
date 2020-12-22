from common import definitions, values
from common.utilities import execute_command, error_exit, get_code, backup_file, show_partial_diff, backup_file_orig, restore_file_orig, replace_file, get_code_range
from tools import emitter, logger, finder, extractor, identifier, writer
from ast import generator

import os
import sys


def evolve_definitions(missing_definition_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    missing_header_list = dict()
    missing_macro_list = dict()
    if not missing_definition_list:
        emitter.normal("\t-none-")
    ast_b = None
    def_node_list = dict()
    for def_name in missing_definition_list:
        emitter.normal(def_name)
        macro_info = missing_definition_list[def_name]
        source_file = macro_info['source']
        target_file = macro_info['target']
        def_node_list = extractor.extract_macro_definitions(source_file)
        if not ast_b:
            ast_b = generator.get_ast_json(source_file, use_macro=values.DONOR_REQUIRE_MACRO)
            def_node_list = extractor.extract_def_node_list(ast_b)
        if def_name in def_node_list:
            def_node = def_node_list[def_name]
            if 'identifier' in def_node:
                identifier = def_node['identifier']
                if identifier == def_name:
                    if "file" in def_node:
                        def_file = def_node['file']
                        if def_file[-1] == "h":
                            header_file = def_file.split("/include/")[-1]
                            missing_header_list[header_file] = target_file
                            emitter.success("\t\tfound definition in: " + def_file)
                    else:
                        missing_macro_list[def_name] = missing_definition_list[def_name]
        else:
            missing_macro_list[def_name] = missing_definition_list[def_name]


        # def_insert_line = Finder.find_definition_insertion_point(target_file)
        # missing_macro_list = Identifier.identify_missing_macros_in_func(ast_node, function_source_file,
        #                                                             source_path_d)
        # missing_header_list = Identifier.identify_missing_headers(ast_node, source_path_d)
        #
    print(missing_header_list)
    print(missing_macro_list)
    return missing_header_list, missing_macro_list


def evolve_data_type(missing_data_type_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    missing_header_list = dict()
    missing_macro_list = dict()
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

        # missing_macro_list = Identifier.identify_missing_macros_in_func(ast_node, function_source_file,
        #                                                             source_path_d)
        # missing_header_list = Identifier.identify_missing_headers(ast_node, source_path_d)
        #
    return missing_header_list, missing_macro_list


def evolve_functions(missing_function_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not missing_function_list:
        emitter.normal("\t-none-")
    def_insert_point = ""
    missing_header_list = dict()
    missing_macro_list = dict()
    filtered_missing_function_list = dict()
    for function_name in missing_function_list:
        info = missing_function_list[function_name]
        node_id = info['node_id']
        source_path_b = info['source_b']
        source_path_d = info['source_d']
        emitter.normal(function_name)
        ast_map_b = generator.get_ast_json(source_path_b)
        function_ref_node_id = int(info['ref_node_id'])
        function_ref_node = finder.search_ast_node_by_id(ast_map_b, function_ref_node_id)
        function_def_node = finder.search_ast_node_by_id(ast_map_b, int(node_id))
        function_source_file = function_def_node['file']
        if function_source_file[-1] == "h":
            if "include" in function_source_file:
                header_file = function_source_file.split("/include/")[-1]
            else:
                header_file = function_source_file.split("/")[-1]
            missing_header_list[header_file] = source_path_d

        else:
            function_node, function_source_file = extractor.extract_complete_function_node(function_def_node,
                                                                                           source_path_b)
            missing_def_list = identifier.identify_missing_definitions(function_node, missing_function_list)
            missing_macro_list = identifier.identify_missing_macros_in_func(function_node, function_source_file,
                                                                            source_path_d)
            missing_header_list = identifier.identify_missing_headers(function_node, source_path_d)
        emitter.success("\t\tfound definition in: " + function_source_file)
        # print(function_name)
    return missing_header_list, missing_macro_list, filtered_missing_function_list


def evolve_code(file_a, file_b, file_c, instruction_list, seg_id_a, seg_id_c, seg_code):
    missing_function_list = dict()
    missing_var_list = dict()
    missing_macro_list = dict()
    missing_label_list = dict()
    missing_header_list = dict()
    missing_data_type_list = dict()

    if values.DONOR_REQUIRE_MACRO:
        values.PRE_PROCESS_MACRO = values.DONOR_PRE_PROCESS_MACRO
    ast_map_a = generator.get_ast_json(file_a, values.DONOR_REQUIRE_MACRO, True)
    ast_map_b = generator.get_ast_json(file_b, values.DONOR_REQUIRE_MACRO, True)

    if values.TARGET_REQUIRE_MACRO:
        values.PRE_PROCESS_MACRO = values.TARGET_PRE_PROCESS_MACRO
    ast_map_c = generator.get_ast_json(file_c, values.TARGET_REQUIRE_MACRO, True)

    file_d = str(file_c).replace(values.Project_C.path, values.Project_D.path)

    # Check for an edit script
    script_file_name = definitions.DIRECTORY_OUTPUT + "/" + str(seg_id_c) + "_script"
    syntax_error_file_name = definitions.DIRECTORY_OUTPUT + "/" + str(seg_id_c) + "_syntax_errors"
    neighborhood_a = extractor.extract_neighborhood(file_a, seg_code, seg_id_a)
    neighborhood_b = extractor.extract_neighborhood(file_b, seg_code, seg_id_a)
    neighborhood_c = extractor.extract_neighborhood(file_c, seg_code, seg_id_c)
    var_map = values.map_namespace[(file_a, file_c)]
    with open(script_file_name, 'w') as script_file:
        count = 0
        for instruction in instruction_list:
            count = count + 1
            # Emitter.normal("\t[action]transplanting code segment " + str(count))
            check_node = None
            if "Insert" in instruction:
                check_node_id = instruction.split("(")[1].split(")")[0]
                check_node = finder.search_ast_node_by_id(ast_map_b, int(check_node_id))

            elif "Replace" in instruction:
                check_node_id = instruction.split(" with ")[1].split("(")[1].split(")")[0]
                check_node = finder.search_ast_node_by_id(ast_map_b, int(check_node_id))

            elif "Update" in instruction:
                check_node_id = instruction.split(" to ")[1].split("(")[1].split(")")[0]
                check_node = finder.search_ast_node_by_id(ast_map_b, int(check_node_id))

            elif "Delete" in instruction:
                check_node = None

            if check_node:

                missing_function_list.update(identifier.identify_missing_functions(ast_map_a,
                                                                                   check_node,
                                                                                   file_b,
                                                                                   file_d,
                                                                                   ast_map_c))

                missing_macro_list.update(identifier.identify_missing_macros(check_node,
                                                                             file_b,
                                                                             file_d
                                                                             ))

                # missing_var_list.update(Identifier.identify_missing_var(neighborhood_a,
                #                                                         neighborhood_b,
                #                                                         neighborhood_c,
                #                                                         check_node,
                #                                                         file_b,
                #                                                         file_c,
                #                                                         var_map
                #                                                         ))

                missing_label_list.update(identifier.identify_missing_labels(neighborhood_a,
                                                                             neighborhood_b,
                                                                             neighborhood_c,
                                                                             check_node,
                                                                             file_b,
                                                                             var_map
                                                                             ))

            script_file.write(instruction + "\n")
        # print(missing_var_list)
        target_ast = None
        if neighborhood_c['type'] in ["FunctionDecl", "RecordDecl"]:
            target_ast = neighborhood_c['children'][1]
        position_c = target_ast['type'] + "(" + str(target_ast['id']) + ") at " + str(1)
        for var in missing_var_list:
            # print(var)
            var_info = missing_var_list[var]
            if "ast-node" in var_info.keys():
                ast_node = var_info['ast-node']
                # not sure why the if is required
                # if "ref_type" in ast_node.keys():
                node_id_a = ast_node['id']
                node_id_b = node_id_a
                instruction = "Insert " + ast_node['type'] + "(" + str(node_id_b) + ")"
                instruction += " into " + position_c
                script_file.write(instruction + "\n")
                emitter.highlight("\t\tadditional variable added with instruction: " + instruction)
            elif "value" in var_info.keys():
                var_map[var] = str(var_info['value'])

        values.map_namespace[(file_a, file_c)] = var_map
        writer.write_var_map(var_map, definitions.FILE_NAMESPACE_MAP)
        offset = len(target_ast['children']) - 1
        position_c = target_ast['type'] + "(" + str(target_ast['id']) + ") at " + str(offset)
        for label in missing_label_list:
            # print(var)
            label_info = missing_label_list[label]
            ast_node = label_info['ast-node']
            # not sure why the if is required
            # if "ref_type" in ast_node.keys():
            node_id_a = ast_node['id']
            node_id_b = node_id_a
            instruction = "Insert " + ast_node['type'] + "(" + str(node_id_b) + ")"
            instruction += " into " + position_c
            script_file.write(instruction + "\n")
            emitter.highlight("\t\tadditional label added with instruction: " + instruction)

    emitter.success("\n\tSuccessful evolution")
    return missing_function_list, missing_macro_list

