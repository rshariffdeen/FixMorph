#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from common.utilities import execute_command, get_file_extension_list, error_exit
from ast import Generator, AST
from tools import Mapper, Finder, Logger, Extractor, Emitter


def merge_var_info(var_expr_map, var_value_map):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_info = dict()
    # print(var_expr_map)
    # print(var_value_map)
    for var_name in var_value_map:
        if var_name in var_expr_map:
            info = dict()
            # print(var_name)
            info["data_type"] = var_expr_map[var_name]['data_type']
            # print(info["data_type"])
            info["value_list"] = var_value_map[var_name]['value_list']
            # print(info["value_list"])
            info["expr_list"] = var_expr_map[var_name]['expr_list']
            var_info[var_name] = info
    # print(var_info)
    return var_info


def merge_diff_info(info_a, info_b):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    for source_loc in info_b:
        info_a[source_loc] = info_b[source_loc]
    return info_a


def merge_var_map(map_a, map_b):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_map = dict()
    for var_name in map_a:
        if var_name in map_b:
            var_map[var_name] = map_b[var_name]
        else:
            var_map[var_name] = map_a[var_name]

    for var_name in map_b:
        if var_name not in map_a:
            var_map[var_name] = map_b[var_name]

    # print(var_info)
    return var_map


def merge_macro_info(list_a, list_b):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    macro_info = dict()
    for macro_name in list_a:
        info_a = list_a[macro_name]
        if macro_name in list_b.keys():
            info_b = list_b[macro_name]
            if info_a['target'] != info_b['target']:
                error_exit("MULTIPLE USAGE OF MACRO")
        macro_info[macro_name] = info_a

    for macro_name in list_b:
        info_b = list_b[macro_name]
        macro_info[macro_name] = info_b
    return macro_info


def merge_header_info(info_a, info_b):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    header_info = dict()
    for header_name in info_a:
        info = info_a[header_name]
        if header_name in info_b.keys():
            if info_a[header_name] != info_b[header_name]:
                error_exit("MULTIPLE USAGE OF HEADER")
        header_info[header_name] = info

    for header_name in info_b:
        info = info_b[header_name]
        header_info[header_name] = info
    return header_info


def merge_data_type_info(info_a, info_b):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    header_info = dict()
    for header_name in info_a:
        info = info_a[header_name]
        if header_name in info_b.keys():
            error_exit("MULTIPLE USAGE OF DATA TYPE")
        header_info[header_name] = info

    for header_name in info_b:
        info = info_b[header_name]
        header_info[header_name] = info
    return header_info


def merge_ast_script(ast_script, ast_node_a, ast_node_b, mapping_ba):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\t\tmerging AST script")
    merged_ast_script = list()
    inserted_node_list = list()
    deleted_node_list = list()
    replace_node_list = list()
    try:
        ast_tree_a = AST.load_from_map(ast_node_a)
        ast_tree_b = AST.load_from_map(ast_node_b)
    except:
        return None
    # print(ast_script)
    for script_line in ast_script:
        # print(script_line)
        if "Insert" in script_line:
            # print(script_line)
            node_id_a = int(((script_line.split(" into ")[0]).split("(")[1]).split(")")[0])
            node_id_b = int(((script_line.split(" into ")[1]).split("(")[1]).split(")")[0])
            if node_id_b in inserted_node_list or node_id_b == 0:
                inserted_node_list.append(node_id_a)
                if node_id_b == 0:
                    merged_ast_script.append(script_line)
                continue
            insert_node = Finder.search_ast_node_by_id(ast_node_b, node_id_a)
            # print(replace_node)
            target_node_id_a = mapping_ba[node_id_b]
            target_node = Finder.search_ast_node_by_id(ast_node_a, target_node_id_a)
            # print(target_node)
            insert_position = int((script_line.split(" at ")[1]))
            del_op = "Delete " + str(target_node['type']) + "(" + str(target_node_id_a) + ")\n"
            # print(del_op)
            possible_replacement_node = Finder.search_ast_node_by_id(ast_node_a, target_node_id_a)
            parent_node = Finder.search_ast_node_by_id(ast_node_a, int(possible_replacement_node['parent_id']))
            # print(parent_node)
            del_parent_op = "Delete " + str(parent_node['type']) + "(" + str(parent_node['id']) + ")\n"
            # print(del_parent_op)
            # print(ast_script)
            if del_op in ast_script:
                replace_node_str = str(insert_node['type']) + "(" + str(node_id_a) + ")"
                target_node_str = str(possible_replacement_node['type']) + "(" + str(target_node_id_a) + ")"
                script_line = "Replace " + target_node_str + " with " + replace_node_str
                inserted_node_list.append(node_id_a)
            elif del_parent_op in ast_script:
                replace_node_str = str(insert_node['type']) + "(" + str(node_id_a) + ")"
                # print(replace_node_str)
                target_node_str = str(possible_replacement_node['type']) + "(" + str(target_node_id_a) + ")"
                # print(target_node_str)
                script_line = "Replace " + target_node_str + " with " + replace_node_str
                # print(script_line)
            # elif len(target_node['children']) > insert_position:
            #     possible_replacement_node = target_node['children'][insert_position]
            #     # print(possible_replacement_node)
            #     replacement_node_id = possible_replacement_node['id']
            #     del_op = "Delete " + str(possible_replacement_node['type']) + "(" + str(replacement_node_id) + ")\n"
            #     # print(del_op)
            #     if del_op in ast_script:
            #         # print(del_op)
            #         replace_node_str = str(insert_node['type']) + "(" + str(node_id_a) + ")"
            #         target_node_str = str(possible_replacement_node['type']) + "(" + str(replacement_node_id) + ")"
            #         script_line = "Replace " + target_node_str + " with " +  replace_node_str
            #         # print(script_line)
            #         deleted_node_list.append(replacement_node_id)
            #         child_id_list = Extractor.extract_child_id_list(possible_replacement_node)
            #         deleted_node_list = deleted_node_list + child_id_list

            if node_id_b not in inserted_node_list:
                merged_ast_script.append(script_line)
            # mark all child-ids as inserted since merging and avoid update
            child_id_list = Extractor.extract_child_id_list(insert_node)
            inserted_node_list = list(set(child_id_list + inserted_node_list))
            inserted_node_list.append(node_id_a)
        elif "Delete" in script_line:
            # node_id = int((script_line.split("(")[1]).split(")")[0])
            # node = Finder.search_ast_node_by_id(ast_node_a, node_id)
            # child_id_list = Extractor.extract_child_id_list(node)
            # deleted_node_list = deleted_node_list + child_id_list
            # if node_id not in deleted_node_list:
            #     deleted_node_list.append(node_id)
            merged_ast_script.append(script_line)
        elif "Move" in script_line:
            # print(script_line)
            move_position = int((script_line.split(" at ")[1]))
            move_node_str = (script_line.split(" into ")[0]).replace("Move ", "")
            move_node_id_b = int((move_node_str.split("(")[1]).split(")")[0])
            move_node_id_a = mapping_ba[move_node_id_b]
            move_node_b = Finder.search_ast_node_by_id(ast_node_b, move_node_id_b)
            move_node_a = Finder.search_ast_node_by_id(ast_node_a, move_node_id_a)
            move_node_type_b = move_node_b['type']
            move_node_type_a = move_node_a['type']
            if move_node_type_b == "CaseStmt":
                continue
            target_node_id_b = int(((script_line.split(" into ")[1]).split("(")[1]).split(")")[0])

            if target_node_id_b in inserted_node_list or move_node_id_b in inserted_node_list:
                # script_line = "Delete " + str(move_node_a['type']) + "(" + str(move_node_a['id']) + ")\n"
                # if move_node_type_a == "BinaryOperator":
                replace_node_str = str(move_node_a['type']) + "(" + str(move_node_id_a) + ")"
                target_node_str = str(move_node_b['type']) + "(" + str(move_node_id_b) + ")"
                script_line = "Replace " + target_node_str + " with " + replace_node_str

                # script_line = "Replace " + str(move_node_id_a) + " with " + str(target_node_id_b)
                merged_ast_script.append(script_line)
                for script_line in merged_ast_script:
                    if str(target_node_id_b) in script_line and "Insert" in script_line:
                        merged_ast_script.remove(script_line)
                continue
            # if target_node_id_b in inserted_node_list:
            #     continue
            # print(move_node_type_b)
            # print(move_node_type_a)
            target_node_id_a = mapping_ba[target_node_id_b]
            # print(target_node_id_a)
            target_node_a = Finder.search_ast_node_by_id(ast_node_a, target_node_id_a)
            target_node_str = target_node_a['type'] + "(" + str(target_node_a['id']) + ")"
            # print(target_node_a)
            # print(move_node_type_a)
            # print(move_node_type_b)
            if move_node_type_a != move_node_type_b:
                script_line = "Insert " + move_node_str + " into " + target_node_str + " at " + str(move_position)
            if len(target_node_a['children']) <= move_position:
                script_line = "Insert " + move_node_str + " into " + target_node_str + " at " + str(move_position)

            elif len(target_node_a['children']) > move_position:
                possible_replacement_node = target_node_a['children'][move_position]
                # print(possible_replacement_node)
                replacement_node_id = possible_replacement_node['id']
                del_op = "Delete " + str(possible_replacement_node['type']) + "(" + str(replacement_node_id) + ")\n"
                # print(del_op)
                if del_op in ast_script:
                    # print(del_op)
                    replace_node_str = str(move_node_b['type']) + "(" + str(move_node_b['id']) + ")"
                    target_node_str = str(possible_replacement_node['type']) + "(" + str(replacement_node_id) + ")"
                    script_line = "Replace " + target_node_str + " with " + replace_node_str
                    # print(script_line)
                    deleted_node_list.append(replacement_node_id)
                    child_id_list = Extractor.extract_child_id_list(possible_replacement_node)
                    deleted_node_list = deleted_node_list + child_id_list

            else:
                replacing_node = target_node_a['children'][move_position]
                replacing_node_id = replacing_node['id']
                replacing_node_str = replacing_node['type'] + "(" + str(replacing_node['id']) + ")"
                script_line = "Replace " + replacing_node_str + " with " + move_node_str
                deleted_node_list.append(replacing_node_id)
                child_id_list = Extractor.extract_child_id_list(replacing_node)
                deleted_node_list = deleted_node_list + child_id_list
                # print(replacing_node_id)
                inserted_node_list.append(replacing_node_id)
            # print(script_line)
            merged_ast_script.append(script_line)
        elif "Update" in script_line:
            # print(script_line)
            # update_line = str(script_line).replace("Update", "Replace").replace(" to ", " with ")
            # print(update_line)
            target_node_str = (script_line.split(" to ")[0]).replace("Update ", "")
            target_node_id = int((target_node_str.split("(")[1]).split(")")[0])
            target_node = Finder.search_ast_node_by_id(ast_node_a, target_node_id)
            replace_node_str = script_line.split(" to ")[1]
            replace_node_id = int((replace_node_str.split("(")[1]).split(")")[0])
            replace_node = Finder.search_ast_node_by_id(ast_node_b, replace_node_id)

            if "TypeLoc" in script_line:
                continue
            if replace_node_id not in inserted_node_list:
                merged_ast_script.append(script_line)

    second_merged_ast_script = list()
    inserted_node_list = dict()
    for script_line in merged_ast_script:
        # print(script_line)
        if "Replace" in script_line:
            # print(script_line)
            node_id_a = int(((script_line.split(" with ")[0]).split("(")[1]).split(")")[0])
            node_id_b = int(((script_line.split(" with ")[1]).split("(")[1]).split(")")[0])
            node_a = Finder.search_ast_node_by_id(ast_node_a, node_id_a)
            parent_node_id_a = int(node_a['parent_id'])
            parent_node_a = Finder.search_ast_node_by_id(ast_node_a, parent_node_id_a)
            if len(parent_node_a['children']) > 0:
                count = 0
                for child_node in parent_node_a['children']:
                    replace_op = "Replace " + child_node['type'] + "(" + str(child_node['id']) + ")"
                    count += sum(replace_op in s for s in merged_ast_script)
                if count > 1:
                    node_b = Finder.search_ast_node_by_id(ast_node_b, node_id_b)
                    parent_node_id_b = int(node_b['parent_id'])
                    parent_node_b = Finder.search_ast_node_by_id(ast_node_b, parent_node_id_b)
                    parent_node_str_a = parent_node_a['type'] + "(" + str(parent_node_a['id']) + ")"
                    parent_node_str_b = parent_node_b['type'] + "(" + str(parent_node_b['id']) + ")"
                    new_op = "Replace " + parent_node_str_a + " with " + parent_node_str_b + "\n"
                    if new_op not in second_merged_ast_script:
                        second_merged_ast_script.append(new_op)
                else:
                    second_merged_ast_script.append(script_line)
            else:
                second_merged_ast_script.append(script_line)
        elif "Update" in script_line:
            update_line = str(script_line).replace("Update", "Replace").replace(" to ", " with ")
            # print(update_line)
            second_merged_ast_script.append(update_line)

        elif "Insert" in script_line:
            node_id_a = int(((script_line.split(" into ")[0]).split("(")[1]).split(")")[0])
            node_id_b = int(((script_line.split(" into ")[1]).split("(")[1]).split(")")[0])
            new_insert_node = Finder.search_ast_node_by_id(ast_node_b, node_id_a)
            if node_id_b not in inserted_node_list:
                inserted_node_list[node_id_b] = list()
            inserted_node_list_target = inserted_node_list[node_id_b]
            if not inserted_node_list_target:
                inserted_node_list[node_id_b] = [node_id_a]
                second_merged_ast_script.append(script_line)
            else:
                is_duplicate = False
                for inserted_node_id in inserted_node_list_target:
                    inserted_node = Finder.search_ast_node_by_id(ast_node_b, inserted_node_id)
                    if (inserted_node['type'] == new_insert_node['type']) and \
                        (inserted_node['start line'] == new_insert_node['start line'])and \
                        (inserted_node['parent_id'] == new_insert_node['parent_id']):
                        is_duplicate = True
                        break
                if not is_duplicate:
                    inserted_node_list[node_id_b].append(node_id_a)
                    second_merged_ast_script.append(script_line)

        else:
            second_merged_ast_script.append(script_line)

    return second_merged_ast_script


def merge_segmentation_list(segmentation_list_a, segmentation_list_b):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\t\t\tmerging segmentation list")
    enum_list_a, function_list_a, macro_list_a, \
    struct_list_a, type_def_list_a, def_list_a, decl_list_a, definition_list_a = segmentation_list_a

    enum_list_b, function_list_b, macro_list_b, \
    struct_list_b, type_def_list_b, def_list_b, decl_list_b, definition_list_b = segmentation_list_b

    enum_list = set(enum_list_a + enum_list_b)
    function_list = set(function_list_a + function_list_b)
    macro_list = set(macro_list_a + macro_list_b)
    struct_list = set(struct_list_a + struct_list_b)
    type_def_list = set(type_def_list_a + type_def_list_b)
    def_list = set(decl_list_a + def_list_b)
    decl_list = set(decl_list_a + decl_list_b)
    definition_list = definition_list_a
    for identifier in definition_list_b.keys():
        if identifier not in definition_list_a.keys():
            definition_list[identifier] = definition_list_b[identifier]

    segmentation_list_merged = enum_list, function_list, macro_list, \
                               struct_list, type_def_list, def_list, decl_list, definition_list
    return segmentation_list_merged
