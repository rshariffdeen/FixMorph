import sys
from app.common import definitions, values, utilities
from app.common.utilities import execute_command, error_exit, get_source_name_from_slice
from app.tools import emitter, finder, logger
from app.ast import ast_parser, ast_generator


def id_from_string(simplestring):
    return int(simplestring.split("(")[-1][:-1])


def get_id(node_ref):
    return int(node_ref.split("(")[-1][:-1])


def get_type(node_ref):
    return node_ref.split("(")[0]


def inst_comp(i):
    return definitions.order.index(i)


def order_comp(inst1, inst2):
    # if inst1[0] in order[0:3]:
    #     l1 = inst1[1]
    # elif inst1[0] in order[3:5]:
    #     l1 = inst1[2]

    # if inst2[0] in order[0:3]:
    #     l2 = inst2[1]
    # elif inst2[0] in order[3:5]:
    #     l2 = inst2[2]

    # line1 = int(l1.line)
    # line2 = int(l2.line)
    # if line1 != line2:
    #     return line2 - line1

    # line1 = int(l1.line_end)
    # line2 = int(l2.line_end)
    # if line1 != line2:
    #     return line2 - line1

    # col1 = int(l1.col)
    # col2 = int(l2.col)
    # if col1 != col2:
    #     return col2 - col1

    # col1 = int(l1.col_end)
    # col2 = int(l2.col_end)
    # if col1 != col2:
    #     return col2 - col1

    return inst_comp(inst1[0]) - inst_comp(inst2[0])


def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'

    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


def gen_temp_json(file_a, file_b, file_c):
    ASTlists = dict()
    try:
        if values.DONOR_REQUIRE_MACRO:
            values.PRE_PROCESS_MACRO = values.DONOR_PRE_PROCESS_MACRO
        gen_json(file_a, values.Project_A.name, ASTlists, values.DONOR_REQUIRE_MACRO)
        gen_json(file_b, values.Project_B.name, ASTlists, values.DONOR_REQUIRE_MACRO)
        if values.TARGET_REQUIRE_MACRO:
            values.PRE_PROCESS_MACRO = values.TARGET_PRE_PROCESS_MACRO
        gen_json(file_c, values.Project_C.name, ASTlists, values.TARGET_REQUIRE_MACRO)
    except Exception as e:
        error_exit(e, "Error parsing with crochet-diff. Did you bear make?")
    return ASTlists


def ASTdump(file_path, output, use_macro=False):
    extra_arg = ""
    if file_path[-1] == 'h':
        extra_arg = " --"
    dump_command = definitions.DIFF_COMMAND + " -s=" + definitions.DIFF_SIZE + " -ast-dump-json "
    if use_macro:
        if values.CONF_PATH_A in file_path or values.CONF_PATH_B in file_path:
            dump_command += " " + values.DONOR_PRE_PROCESS_MACRO.replace("--extra-arg-a", "--extra-arg") + "  "
        else:
            dump_command += " " + values.TARGET_PRE_PROCESS_MACRO.replace("--extra-arg-c", "--extra-arg") + "  "

    error_file = definitions.DIRECTORY_OUTPUT + "/errors_AST_dump"
    dump_command += file_path + extra_arg + " 2> " + error_file + " > " + output
    execute_command(dump_command)


def gen_json(file, name, ASTlists, use_macro=False):
    emitter.normal("\t\tClang AST parse " + file + " in " + name)
    json_file = definitions.DIRECTORY_OUTPUT + "/json_" + name
    ASTdump(file, json_file, use_macro)
    ASTlists[name] = ast_parser.AST_from_file(json_file)


def match_nodes(node_a, node_c):
    check_operator_type_list = ["BinaryOperator", "UnaryOperator", "CompoundAssignOperator"]

    if node_a.type != node_c.type:
        return False
    else:
        if node_a.type in check_operator_type_list:
            if node_a.value != node_c.value:
                return False
            else:
                return True
        elif "Decl" in node_a.type or "Expr" in node_a.type or node_a.type == "Macro":
            if node_a.value != node_c.value:
                return False
            else:
                return True
        else:
            return True


def match_children(node_a, node_c, json_ast_dump):
    if node_a.parent_id is None and node_c.parent_id is None:
        return True
    elif node_a.parent_id is not None and node_c.parent_id is not None:
        parent_b = json_ast_dump[values.Project_A.name][node_a.parent_id]
        parent_c = json_ast_dump[values.Project_C.name][node_c.parent_id]
        if match_nodes(parent_b, parent_c):
            return match_path(parent_b, parent_c, json_ast_dump)
        else:
            return False
    else:
        return False


def match_path(node_a, node_c, json_ast_dump):
    if node_a.parent_id is None and node_c.parent_id is None:
        return True
    elif node_a.parent_id is not None and node_c.parent_id is not None:
        parent_a = json_ast_dump[values.Project_A.name][node_a.parent_id]
        parent_c = json_ast_dump[values.Project_C.name][node_c.parent_id]
        if match_nodes(parent_a, parent_c):
            return match_path(parent_a, parent_c, json_ast_dump)
        else:
            return False
    else:
        return False


def get_candidate_node_list(node_ref, json_ast_dump):
    candidate_node_list = list()
    node_id = get_id(node_ref)
    node_a = json_ast_dump[values.Project_A.name][node_id]
    emitter.normal(node_a)
    parent_id = node_a.parent_id
    while parent_id is not None:
        parent = json_ast_dump[values.Project_A.name][parent_id]
        emitter.normal(str(parent.id) + " - " + parent.type)
        parent_id = parent.parent_id

    for node_c in json_ast_dump[values.Project_C.name]:
        if match_nodes(node_a, node_c):
            if match_path(node_a, node_c, json_ast_dump):
                if node_c not in candidate_node_list:
                    candidate_node_list.append(node_c)

    for node in candidate_node_list:
        emitter.rose("Node: " + str(node.id))
        parent_id = node.parent_id
        while parent_id is not None:
            parent = json_ast_dump[values.Project_C.name][parent_id]
            emitter.rose(str(parent.id) + " - " + parent.type)
            parent_id = parent.parent_id

    return candidate_node_list


def extract_child_id_list(ast_object):
    id_list = list()
    for child_node in ast_object.children:
        if ast_object.type == "IfStmt" and child_node.type == "CompoundStmt":
            continue
        child_id = int(child_node.id)
        id_list.append(child_id)
        grand_child_list = extract_child_id_list(child_node)
        if grand_child_list:
            id_list = id_list + grand_child_list
    if id_list:
        id_list = list(set(id_list))
    return id_list


def transform_script_gumtree(modified_script, inserted_node_list, json_ast_dump, map_ba, map_ac, neighbor_id_c):
    translated_instruction_list = list()
    inserted_node_list_d = list()
    replace_node_list_d = list()
    update_list_d = list()
    deleted_node_list_d = dict()
    map_bd = dict()
    emitter.normal("\ttranslating transformation script")
    for instruction in modified_script:
        operation = instruction[0]
        # Update nodeA to nodeB (value) -> Update nodeC to nodeD (value)
        if operation == definitions.UPDATE:
            try:
                txt_target_node_a = instruction[1]
                txt_update_node = instruction[2]
                target_node = "?"
                update_node_id = id_from_string(txt_update_node)
                target_node_id = id_from_string(txt_target_node_a)
                if target_node_id in replace_node_list_d:
                    continue
                if int(update_node_id) in update_list_d:
                    continue
                update_node = json_ast_dump[values.Project_B.name][update_node_id]

                if txt_target_node_a in map_ac.keys():
                    txt_target_node = map_ac[txt_target_node_a]
                    target_node_id = id_from_string(txt_target_node)
                    target_node = json_ast_dump[values.Project_C.name][target_node_id]
                    if int(target_node_id) < neighbor_id_c:
                        continue
                    if update_node.type != target_node.type:
                        instruction = get_instruction((definitions.REPLACE, target_node, update_node))
                        translated_instruction_list.append(instruction)
                        continue
                    elif deleted_node_list_d.get(target_node.parent_id):
                        instruction = get_instruction((definitions.REPLACE, target_node.parent, update_node))
                        translated_instruction_list.append(instruction)
                        continue

                    if target_node.line is None:
                        target_node.line = target_node.parent.line

                    if target_node.parent.type == "FunctionDecl":
                        continue

                    instruction = get_instruction((definitions.UPDATE, target_node, update_node))
                    translated_instruction_list.append(instruction)

                else:
                    emitter.warning("Warning: Match for " + str(txt_target_node_a) + "not found. Skipping UPDATE instruction.")

            except Exception as e:
                error_exit(e, "Something went wrong with UPDATE.")

        elif operation == definitions.REPLACE:
            try:
                txt_target_node_a = instruction[1]
                txt_update_node = instruction[2]
                target_node = "?"
                target_node_id = id_from_string(txt_target_node_a)
                update_node_id = id_from_string(txt_update_node)
                if int(update_node_id) in update_list_d:
                    continue
                if target_node_id in replace_node_list_d:
                    continue
                replace_node_list_d.append(target_node_id)
                target_node_a = json_ast_dump[values.Project_A.name][target_node_id]
                child_id_list = extract_child_id_list(target_node_a)
                for id in child_id_list:
                    replace_node_list_d.append(id)
                update_node = json_ast_dump[values.Project_B.name][update_node_id]

                if txt_target_node_a in map_ac.keys():
                    txt_target_node = map_ac[txt_target_node_a]
                    target_node_id = id_from_string(txt_target_node)
                    target_node = json_ast_dump[values.Project_C.name][target_node_id]
                    if int(target_node_id) < neighbor_id_c:
                        continue
                    if target_node.line is None:
                        target_node.line = target_node.parent.line
                    instruction = get_instruction((definitions.REPLACE, target_node, update_node))
                    translated_instruction_list.append(instruction)

                else:
                    emitter.warning(
                        "Warning: Match for " + str(txt_target_node_a) + "not found. Skipping REPLACE instruction.")

            except Exception as e:
                error_exit(e, "Something went wrong with UPDATE.")

        # Delete nodeA -> Delete nodeC
        elif operation == definitions.DELETE:
            try:
                txt_delete_node_a = instruction[1]
                delete_node = "?"
                if txt_delete_node_a in map_ac.keys():
                    txt_delete_node = map_ac[txt_delete_node_a]
                    delete_node_id = id_from_string(txt_delete_node)
                    if int(delete_node_id) < neighbor_id_c:
                        continue
                    delete_node = json_ast_dump[values.Project_C.name][delete_node_id]
                    if delete_node.type == "CompoundStmt":
                        parent_node = json_ast_dump[values.Project_C.name][delete_node.parent_id]
                        if parent_node.type == "FunctionDecl":
                            continue
                    instruction = get_instruction((definitions.DELETE, delete_node))
                    if delete_node.line is None:
                        delete_node.line = delete_node.parent.line
                    deleted_node_list_d[delete_node.id] = delete_node
                    if delete_node.parent_id:
                        if deleted_node_list_d.get(delete_node.parent_id) is None:
                            translated_instruction_list.append(instruction)
                    else:
                        translated_instruction_list.append(instruction)

                else:
                    emitter.warning("Warning: Match for " + str(txt_delete_node_a) + "not found. Skipping DELETE instruction.")
            except Exception as e:
                error_exit(e, "Something went wrong with DELETE.")
            # Move nodeA to nodeB at pos -> Move nodeC to nodeD at pos
        elif operation == definitions.MOVE:
            try:
                txt_move_node_b = instruction[1]
                txt_target_node_b = instruction[2]
                offset = int(instruction[3])
                move_node = "?"
                target_node = "?"
                if txt_move_node_b in map_ba.keys():
                    txt_move_node_a = map_ba[txt_move_node_b]
                    if txt_move_node_a in map_ac.keys():
                        txt_move_node = map_ac[txt_move_node_a]
                        mode_node_id = id_from_string(txt_move_node)
                        move_node = json_ast_dump[values.Project_C.name][mode_node_id]
                    else:
                        # TODO: Manage case in which txt_move_node_a is unmatched
                        emitter.warning("Node in Pa not found in Pc: (1)")
                        emitter.warning(txt_move_node_a)
                elif txt_move_node_b in inserted_node_list:
                    if txt_move_node_b in map_bd.keys():
                        move_node = map_bd[txt_move_node_b]
                    else:
                        # TODO: Manage case for node not found
                        emitter.warning("Node to be moved was not found. (2)")
                        emitter.warning(txt_move_node_b)
                if txt_target_node_b in map_ba.keys():
                    txt_target_node_a = map_ba[txt_target_node_b]
                    if txt_target_node_a in map_ac.keys():
                        txt_target_node = map_ac[txt_target_node_a]
                        target_node_id = id_from_string(txt_target_node)
                        if int(target_node_id) < neighbor_id_c:
                            continue
                        target_node = json_ast_dump[values.Project_C.name][target_node_id]
                    else:
                        # TODO: Manage case for unmatched nodeA2
                        emitter.warning("Node in Pa not found in Pc: (1)")
                        emitter.warning(txt_target_node_a)
                elif txt_target_node_b in inserted_node_list:
                    if txt_target_node_b in map_bd.keys():
                        target_node = map_bd[txt_target_node_b]
                    else:
                        # TODO: Manage case for node not found
                        emitter.warning("Node to be moved was not found. (2)")
                        emitter.warning(txt_target_node_b)
                try:
                    target_node_b_id = id_from_string(txt_target_node_b)
                    target_node_b = json_ast_dump[values.Project_B.name][target_node_b_id]
                    if offset != 0:
                        previous_child_node_b = target_node_b.children[offset - 1]
                        previous_child_node_b = previous_child_node_b.simple_print()
                        if previous_child_node_b in map_ba.keys():
                            previous_child_node_a = map_ba[previous_child_node_b]
                            if previous_child_node_a in map_ac.keys():
                                previous_child_c = map_ac[previous_child_node_a]
                                previous_child_c = id_from_string(previous_child_c)
                                previous_child_c = json_ast_dump[values.Project_C.name][previous_child_c]
                                if previous_child_c in target_node.children:
                                    offset = target_node.children.index(previous_child_c)
                                    offset += 1
                                else:
                                    emitter.warning("Node not in children.")
                                    emitter.warning(str(instruction))
                                    continue
                                    # emitter.warning([instruction.simple_print() for instruction in
                                    #                  target_node.children])
                            else:
                                emitter.warning("Failed at locating match" + \
                                              " for " + previous_child_node_a)
                                emitter.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                previous_child_node_a = id_from_string(previous_child_node_a)
                                previous_child_node_a = json_ast_dump[values.Project_A.name][previous_child_node_a]
                                parent = previous_child_node_a.parent
                                if parent != None:
                                    offset = parent.children.index(previous_child_node_a)
                                    offset += 1
                        else:
                            emitter.warning("Failed at match for child.")
                except Exception as e:
                    error_exit(e, "Failed at locating pos.")

                if type(move_node) == ast_parser.AST:
                    if move_node.line is None:
                        move_node.line = move_node.parent.line
                    if type(target_node) == ast_parser.AST:
                        if target_node.line is None:
                            target_node.line = target_node.parent.line
                        if target_node in inserted_node_list_d:
                            if target_node.type not in ["LabelStmt"]:
                                posTarget = target_node.parent.children.index(target_node)
                                posOld = move_node.parent.children.index(move_node)
                                if posOld == posTarget:
                                    instruction = get_instruction((definitions.REPLACE, move_node, target_node))
                                else:
                                    instruction = get_instruction((definitions.DELETE, move_node))
                                translated_instruction_list.append(instruction)
                            else:
                                #TODO: complete logic
                                instruction = get_instruction((definitions.MOVE, move_node, target_node, offset))
                        else:
                            instruction = get_instruction((definitions.MOVE, move_node, target_node, offset))
                            translated_instruction_list.append(instruction)
                        inserted_node_list_d.append(move_node)

                    else:
                        emitter.warning("Could not find match for node. " + \
                                      "Ignoring MOVE operation. (D)")
                else:
                    emitter.warning("Could not find match for node. " + \
                                  "Ignoring MOVE operation. (C)")
            except Exception as e:
                error_exit(e, "Something went wrong with MOVE.")

            # Update nodeA and move to nodeB at pos -> Move nodeC to nodeD at pos
        elif operation == definitions.UPDATEMOVE:

            try:
                txt_move_node_b = instruction[1]
                txt_target_node_b = instruction[2]
                offset = int(instruction[3])
                move_node = "?"
                target_node = "?"
                if txt_move_node_b in map_ba.keys():
                    txt_move_node_a = map_ba[txt_move_node_b]
                    if txt_move_node_a in map_ac.keys():
                        txt_move_node = map_ac[txt_move_node_a]
                        move_node_id = id_from_string(txt_move_node)
                        move_node = json_ast_dump[values.Project_C.name][move_node_id]
                    else:
                        # TODO: Manage case in which txt_move_node_a is unmatched
                        emitter.warning("Node in Pa not found in Pc: (1)")
                        emitter.warning(txt_move_node_a)
                elif txt_move_node_b in inserted_node_list:
                    if txt_move_node_b in map_bd.keys():
                        move_node = map_bd[txt_move_node_b]
                    else:
                        # TODO: Manage case for node not found
                        emitter.warning("Node to be moved was not found. (2)")
                        emitter.warning(txt_move_node_b)
                if txt_target_node_b in map_ba.keys():
                    txt_target_node_a = map_ba[txt_target_node_b]
                    if txt_target_node_a in map_ac.keys():
                        txt_target_node = map_ac[txt_target_node_a]
                        target_node_id = id_from_string(txt_target_node)
                        if int(target_node_id) < neighbor_id_c:
                            continue
                        target_node = json_ast_dump[values.Project_C.name][target_node_id]
                    else:
                        # TODO: Manage case for unmatched txt_target_node_a
                        emitter.warning("Node in Pa not found in Pc: (1)")
                        emitter.warning(txt_target_node_a)
                elif txt_target_node_b in inserted_node_list:
                    if txt_target_node_b in map_bd.keys():
                        target_node = map_bd[txt_target_node_b]
                    else:
                        # TODO: Manage case for node not found
                        emitter.warning("Node to be moved was not found. (2)")
                        emitter.warning(txt_target_node_b)
                try:
                    target_node_b_id = id_from_string(txt_target_node_b)
                    target_node_b = json_ast_dump[values.Project_B.name][target_node_b_id]
                    if offset != 0:
                        previous_child_node_b = target_node_b.children[offset - 1]
                        previous_child_node_b = previous_child_node_b.simple_print()
                        if previous_child_node_b in map_ba.keys():
                            previous_child_node_a = map_ba[previous_child_node_b]
                            if previous_child_node_a in map_ac.keys():
                                previous_child_c = map_ac[previous_child_node_a]
                                previous_child_c = id_from_string(previous_child_c)
                                previous_child_c = json_ast_dump[values.Project_C.name][previous_child_c]
                                if previous_child_c in target_node.children:
                                    offset = target_node.children.index(previous_child_c)
                                    offset += 1
                                else:
                                    emitter.warning("Node not in children.")
                                    emitter.warning(str(instruction))
                                    # emitter.warning([instruction.simple_print() for instruction in
                                    #                  target_node.children])
                            else:
                                emitter.warning("Failed at locating match for (update move) " + previous_child_node_a)
                                emitter.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                previous_child_node_a = id_from_string(previous_child_node_a)
                                previous_child_node_a = json_ast_dump[values.Project_A.name][previous_child_node_a]
                                parent = previous_child_node_a.parent
                                if parent != None:
                                    offset = parent.children.index(previous_child_node_a)
                                    offset += 1
                        else:
                            emitter.warning("Failed at match for child.")
                except Exception as e:
                    emitter.warning("Failed at locating pos.")
                    return translated_instruction_list
                if type(move_node) == ast_parser.AST:
                    if move_node.line is None:
                        move_node.line = move_node.parent.line
                    if type(target_node) == ast_parser.AST:
                        if target_node.line is None:
                            target_node.line = target_node.parent.line
                        if target_node in inserted_node_list_d:
                            instruction = get_instruction((definitions.DELETE, move_node))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((definitions.UPDATEMOVE, move_node, target_node, offset))
                            translated_instruction_list.append(instruction)

                        inserted_node_list_d.append(move_node)

                    else:
                        emitter.warning("Could not find match for node. " + \
                                      "Ignoring UPDATEMOVE operation. (D)")
                else:
                    emitter.warning("Could not find match for node. " + \
                                  "Ignoring UPDATEMOVE operation. (C)")
            except Exception as e:
                error_exit(e, "Something went wrong with UPDATEMOVE.")

        # Insert nodeB1 to nodeB2 at pos -> Insert nodeD1 to nodeD2 at pos
        elif operation == definitions.INSERT:
            try:
                txt_insert_node = instruction[1]
                txt_target_node_b = instruction[2]
                offset = int(instruction[3])
                insert_node_id = id_from_string(txt_insert_node)
                insert_node = json_ast_dump[values.Project_B.name][insert_node_id]
                update_list_d = update_list_d + extract_child_id_list(insert_node)
                target_node_b_id = id_from_string(txt_target_node_b)
                target_node_b = json_ast_dump[values.Project_B.name][target_node_b_id]
                if int(target_node_b_id) in update_list_d:
                    continue
                target_node = "?"
                # TODO: Is this correct?
                if target_node_b.line is not None:
                    insert_node.line = target_node_b.line
                else:
                    insert_node.line = target_node_b.parent.line

                if txt_target_node_b in map_ba.keys():
                    txt_target_node_a = map_ba[txt_target_node_b]
                    if txt_target_node_a in map_ac.keys():
                        txt_target_node = map_ac[txt_target_node_a]
                        target_node_id = id_from_string(txt_target_node)
                        target_node = json_ast_dump[values.Project_C.name][target_node_id]
                    else:
                        emitter.warning("Warning: node for insertion not found. Skipping INSERT operation.")
                        continue
                elif txt_target_node_b in map_bd.keys():
                    target_node = map_bd[txt_target_node_b]
                else:
                    emitter.warning("Warning: node for insertion not found. Skipping INSERT operation.")
                    continue
                try:
                    if offset != 0:
                        previous_child_node_b = target_node_b.children[offset - 1]
                        previous_child_node_b = previous_child_node_b.simple_print()
                        if previous_child_node_b in map_ba.keys():
                            previous_child_node_a = map_ba[previous_child_node_b]
                            if previous_child_node_a in map_ac.keys():
                                previous_child_node_c = map_ac[previous_child_node_a]
                                previous_child_node_c = id_from_string(previous_child_node_c)
                                previous_child_node_c = json_ast_dump[values.Project_C.name][previous_child_node_c]
                                if previous_child_node_c in target_node.children:
                                    offset = target_node.children.index(previous_child_node_c)
                                    offset += 1
                                else:
                                    if offset + 1 < len(target_node_b.children):
                                        next_child_node_b = target_node_b.children[offset + 1]
                                        next_child_node_b = next_child_node_b.simple_print()
                                        if next_child_node_b in map_ba.keys():
                                            next_child_node_a = map_ba[next_child_node_b]
                                            if next_child_node_a in map_ac.keys():
                                                next_child_node_c = map_ac[next_child_node_a]
                                                next_child_node_c = id_from_string(next_child_node_c)
                                                next_child_node_c = json_ast_dump[values.Project_C.name][next_child_node_c]
                                                if next_child_node_c in target_node.children:
                                                    offset = target_node.children.index(next_child_node_c)
                                                else:
                                                    emitter.warning("Node not in children.")
                                                    emitter.warning(str(instruction))
                                                    # emitter.warning(next_child_node_c)
                                                    # emitter.warning([child.simple_print() for child in target_node.children])
                                                    target_node = json_ast_dump[
                                                        values.Project_C.name][next_child_node_c.parent_id]
                                                    offset = target_node.children.index(next_child_node_c)

                            else:
                                emitter.warning("Failed at locating match for(insert) " + previous_child_node_a)
                                emitter.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                previous_child_node_a = id_from_string(previous_child_node_a)
                                previous_child_node_a = json_ast_dump[values.Project_A.name][previous_child_node_a]
                                parent_a = previous_child_node_a.parent
                                if parent_a is not None:
                                    offset = parent_a.children.index(previous_child_node_a)
                                    matching_parent_c = map_ac[parent_a.simple_print()]
                                    matching_parent_id = id_from_string(matching_parent_c)
                                    target_node = json_ast_dump[values.Project_C.name][matching_parent_id]
                                    offset += 1

                        elif offset + 1 < len(target_node_b.children):
                            next_child_node_b = target_node_b.children[offset + 1]
                            next_child_node_b = next_child_node_b.simple_print()
                            if next_child_node_b in map_ba.keys():
                                next_child_node_a = map_ba[next_child_node_b]
                                if next_child_node_a in map_ac.keys():
                                    next_child_node_c = map_ac[next_child_node_a]
                                    next_child_node_c = id_from_string(next_child_node_c)
                                    next_child_node_c = json_ast_dump[values.Project_C.name][next_child_node_c]
                                    if next_child_node_c in target_node.children:
                                        offset = target_node.children.index(next_child_node_c)
                                    else:
                                        emitter.warning("Node not in children.")
                                        emitter.warning(str(instruction))
                                        # emitter.warning(next_child_node_c)
                                        # emitter.warning([child.simple_print() for child in target_node.children])
                                        target_node = json_ast_dump[values.Project_C.name][next_child_node_c.parent_id]
                                        offset = target_node.children.index(next_child_node_c)

                        else:
                            emitter.warning("Failed at match for child.")
                except Exception as e:
                    error_exit(e, "Failed at locating pos.")
                if type(insert_node) == ast_parser.AST:
                    map_bd[txt_insert_node] = insert_node
                    inserted_node_list_d.append(insert_node)
                    insert_node.children = []
                    if insert_node.line == None:
                        insert_node.line = insert_node.parent.line
                    if target_node is not None and type(target_node) == ast_parser.AST:
                        if target_node.line == None:
                            target_node.line = target_node.parent.line
                        if int(target_node.id) < neighbor_id_c:
                            continue
                        if target_node not in inserted_node_list_d:
                            if int(offset) > len(target_node.children):
                                offset = len(target_node.children)
                            instruction = get_instruction((definitions.INSERT, insert_node, target_node, offset))
                            translated_instruction_list.append(instruction)
            except Exception as e:
                emitter.warning("Something went wrong with INSERT.")

    return translated_instruction_list


def simplify_patch(instruction_AB, match_BA, ASTlists):
    modified_AB = []
    inserted = []
    deleted = []
    updated = []
    replacing = []
    replaced = []
    insert_pos_list = dict()
    emitter.normal("\tsimplifying transformation script")
    # Emitter.white("Original script from Pa to Pb")
    for i in instruction_AB:
        inst = i[0]
        if inst == definitions.DELETE:
            nodeA = id_from_string(i[1])
            deleted.append(nodeA)
            nodeA = ASTlists[values.Project_A.name][nodeA]
            is_replace = False
            if nodeA.parent_id:
                if nodeA.parent_id in replaced:
                    replaced.append(nodeA.id)
                    continue
                if nodeA.id in replaced:
                    continue
                parentA = ASTlists[values.Project_A.name][int(nodeA.parent_id)]
                index = None
                iterator = 0
                for child in parentA.children:
                    if child == nodeA:
                        index = iterator
                    iterator = iterator + 1

                for instruction in modified_AB:
                    if instruction[0] == definitions.INSERT and instruction[2].id == parentA.id and int(instruction[3]) == index:
                            modified_AB.remove(instruction)
                            is_replace = True
                            if instruction[1].id not in replacing:
                                modified_AB.append((definitions.REPLACE, nodeA, instruction[1]))
                                replaced.append(nodeA.id)
                                replacing.append(instruction[1].id)
                            break
            # Emitter.white("\t" + Common.DELETE + " - " + str(nodeA))
            if not is_replace:
                modified_AB.append((definitions.DELETE, nodeA))
        elif inst == definitions.UPDATE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[values.Project_A.name][nodeA]
            nodeB = id_from_string(i[2])
            nodeB = ASTlists[values.Project_B.name][nodeB]
            # Emitter.white("\t" + Common.UPDATE + " - " + str(nodeA) + " - " + str(nodeB))

            if nodeA.parent_id:
                if nodeA.parent_id in replaced:
                    replaced.append(nodeA.id)
                    continue
            # remove for ID:
            if nodeA.type in ["CompoundStmt"]:
                continue

            if nodeA.value == nodeB.value and nodeA.type not in ["CompoundStmt", "IfStmt", "GCCAsmStmt"]:
                if nodeA.type == "IntegerLiteral":
                    if nodeA.col_end == nodeB.col_end:
                        emitter.warning("skipping update for value and length match")
                        continue
                elif nodeA.type in ["VarDecl"]:
                    # initializer is removed
                    if len(nodeA.children) > len(nodeB.children):
                        modified_AB.append((definitions.DELETE, nodeA.children[1]))
                        deleted.append(nodeA.children[1].id)
                        continue
                else:
                    emitter.warning("skipping update for value match")
                    continue

            if nodeB.parent_id in updated:
                updated.append(nodeB.id)
                continue
            parentB = ASTlists[values.Project_B.name][int(nodeB.parent_id)]
            if parentB in inserted:
                index = 0
                del_id = -1
                replace_node = None
                for i in modified_AB:
                    if i[0] == definitions.INSERT:
                        if i[1].id == nodeB.parent_id:
                            del_id = modified_AB.index(i)
                            replace_node = i[1]
                            break
                if del_id > 0:
                    del modified_AB[del_id]
                modified_AB.append((definitions.REPLACE, nodeA ,replace_node))

            if nodeA.id in replaced:
                continue

            if nodeB.type != nodeA.type:
                modified_AB.append((definitions.REPLACE, nodeA, nodeB))
                continue

            if nodeB.type != "BinaryOperator":
                updated.append(nodeB.id)

            modified_AB.append((definitions.UPDATE, nodeA, nodeB))
        elif inst == definitions.MOVE:
            if values.diff_del_only:
                continue
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[values.Project_B.name][nodeB1]

            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[values.Project_B.name][nodeB2]
            pos = i[3]
            # Emitter.white("\t" + Common.MOVE + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            nodeA1 = match_BA[i[1]]
            nodeA1 = id_from_string(nodeA1)
            nodeA1 = ASTlists[values.Project_A.name][nodeA1]
            if nodeA1.id in deleted:
                continue
            if i[2] in match_BA.keys():
                nodeA2 = match_BA[i[2]]
                nodeA2 = id_from_string(nodeA2)
                nodeA2 = ASTlists[values.Project_A.name][nodeA2]
                if nodeA1 in nodeA2.children:
                    if int(pos) == nodeA2.children.index(nodeA1):
                        continue
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                if nodeB2.type in ["UnaryOperator", "BinaryOperator", "FunctionDecl", "IfStmt"]:
                    nodeA2 = match_BA[i[2]]
                    nodeA2 = id_from_string(nodeA2)
                    nodeA2 = ASTlists[values.Project_A.name][nodeA2]
                    replaced_node = nodeA2.children[int(pos)]
                    if nodeB1.id not in replacing and replaced_node.parent_id not in replaced:
                        replaced.append(replaced_node.id)
                        replacing.append(nodeB1.id)
                        for child in replaced_node.children:
                            replaced.append(child.id)
                        modified_AB.append((definitions.REPLACE, replaced_node, nodeB1))
                else:
                    modified_AB.append((definitions.MOVE, nodeB1, nodeB2, pos))
            else:
                # if nodeB2.type == "IfStmt":
                #     modified_AB.append((definitions.DELETE, nodeA1))
                #     continue
                if i[1] in match_BA.keys():
                    nodeA = match_BA[i[1]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[values.Project_A.name][nodeA]
                    if nodeB2.id not in replacing:
                        posTarget = nodeB2.parent.children.index(nodeB2)
                        posOld = nodeA.parent.children.index(nodeA)
                        if posOld == posTarget:
                            replaced.append(nodeA.id)
                            replacing.append(nodeB2.id)
                            modified_AB.append((definitions.REPLACE, nodeA, nodeB2))
                            for instruction in modified_AB:
                                if instruction[0] == definitions.INSERT and instruction[1].id == nodeB2.id:
                                    modified_AB.remove(instruction)
                        else:
                            modified_AB.append((definitions.DELETE, nodeA))
                            child_id_list = extract_child_id_list(nodeA)
                            for child_id in child_id_list:
                                child_node = ASTlists[values.Project_A.name][child_id]
                                modified_AB.append((definitions.DELETE, child_node))
                    else:
                        modified_AB.append((definitions.DELETE, nodeA))
                else:
                    emitter.warning("Warning: node " + str(nodeB1) + \
                                  "could not be matched. " + \
                                  "Skipping MOVE instruction...")
                    emitter.warning(i)
        elif inst == definitions.UPDATEMOVE:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[values.Project_B.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[values.Project_B.name][nodeB2]
            pos = i[3]
            # Emitter.white("\t" + Common.UPDATEMOVE + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((definitions.UPDATEMOVE, nodeB1, nodeB2, pos))
            else:
                if i[1] in match_BA.keys():
                    nodeA = match_BA[i[1]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[values.Project_A.name][nodeA]
                    modified_AB.append((definitions.DELETE, nodeA))
                else:
                    emitter.warning("Warning: node " + str(nodeB1) + \
                                  "could not be matched. " + \
                                  "Skipping MOVE instruction...")
                    emitter.warning(i)
        elif inst == definitions.INSERT:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[values.Project_B.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[values.Project_B.name][nodeB2]
            pos = i[3]
            adjusted_pos = int(pos)
            # Emitter.white("\t" + Common.INSERT + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 in inserted:
                if nodeB2.type == "IfStmt":
                    if adjusted_pos == 0:
                        continue
                    parent_node = nodeB2.parent
                    if parent_node.type == "IfStmt":
                        compound_node = parent_node.parent
                        adjusted_pos = compound_node.children.index(parent_node)
                    else:
                        compound_node = nodeB2.parent
                        adjusted_pos = compound_node.children.index(nodeB2)
                    nodeB2 = compound_node
                else:
                    continue

            if nodeB2.id not in insert_pos_list.keys():
                insert_pos_list[nodeB2.id] = dict()
            inserted_pos_node_list = insert_pos_list[nodeB2.id]
            if nodeB2.type != "ForStmt":
                if int(pos) - 1 in inserted_pos_node_list.keys():
                    adjusted_pos = inserted_pos_node_list[int(pos) - 1]
            inserted_pos_node_list[int(pos)] = adjusted_pos
            if nodeB2.type in ["UnaryOperator", "ConditionalOperator"]:
                nodeA = match_BA[i[2]]
                nodeA = id_from_string(nodeA)
                nodeA = ASTlists[values.Project_A.name][nodeA]
                replace_node = nodeA.children[0]
                # replace_node = nodeB2.children[0]
                if replace_node.parent_id not in replaced:
                    replaced.append(replace_node.id)
                    modified_AB.append((definitions.REPLACE, replace_node, nodeB1))
            elif nodeB2.type in ["IfStmt"]:
                if adjusted_pos == 0:
                    nodeA = match_BA[i[2]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[values.Project_A.name][nodeA]
                    replace_node = nodeA.children[0]
                    if replace_node.parent_id not in replaced:
                        replaced.append(replace_node.id)
                        modified_AB.append((definitions.REPLACE, replace_node, nodeB1))
                else:
                    modified_AB.append((definitions.INSERT, nodeB1, nodeB2, adjusted_pos))
            elif nodeB2.type in ["ForStmt"]:
                if adjusted_pos in [3, 2]:
                    nodeA = match_BA[i[2]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[values.Project_A.name][nodeA]
                    replace_node = nodeA.children[adjusted_pos]
                    if replace_node.parent_id not in replaced:
                        replaced.append(replace_node.id)
                        modified_AB.append((definitions.REPLACE, replace_node, nodeB1))
                else:
                    modified_AB.append((definitions.INSERT, nodeB1, nodeB2, adjusted_pos))
            elif nodeB2.type in ["BinaryOperator"]:
                target_node_b = nodeB2
                nodeA = match_BA[i[2]]
                nodeA = id_from_string(nodeA)
                nodeA = ASTlists[values.Project_A.name][nodeA]
                target_node_a = nodeA
                replace_node = target_node_a.children[int(pos)]
                if replace_node.parent_id not in replaced and nodeB1.id not in replacing:
                    replaced.append(replace_node.id)
                    for child in replace_node.children:
                        replaced.append(child.id)
                    replacing.append(nodeB1.id)
                    modified_AB.append((definitions.REPLACE, replace_node, nodeB1))
            elif nodeB2.type in ["CompoundAssignOperator"]:
                if i[2] in match_BA.keys():
                    nodeA = match_BA[i[2]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[values.Project_A.name][nodeA]
                    replace_node = nodeA.children[int(pos)]
                    if replace_node.parent_id not in replaced:
                        replaced.append(replace_node.id)
                        modified_AB.append((definitions.REPLACE, replace_node, nodeB1))
            elif nodeB2.type in ["LabelStmt"]:
                if nodeB2 not in inserted:
                    modified_AB.append((definitions.INSERT, nodeB1, nodeB2, adjusted_pos))
                else:
                    compound_node = nodeB2.parent
                    insert_pos = compound_node.children.index(nodeB2)
                    modified_AB.append((definitions.INSERT, nodeB1, compound_node, insert_pos))

            elif nodeB2 not in inserted:
                modified_AB.append((definitions.INSERT, nodeB1, nodeB2, adjusted_pos))
    return modified_AB


def remove_overlapping_delete(modified_AB):
    reduced_AB = set()
    n_i = len(modified_AB)
    for i in range(n_i):
        inst1 = modified_AB[i]
        if inst1[0] == definitions.DELETE:
            for j in range(i + 1, n_i):
                inst2 = modified_AB[j]
                if inst2[0] == definitions.DELETE:
                    node1 = inst1[1]
                    node2 = inst2[1]
                    if node1.contains(node2):
                        reduced_AB.add(j)
                    elif node2.contains(node1):
                        reduced_AB.add(i)
    modified_AB = [modified_AB[i] for i in range(n_i) if i not in reduced_AB]
    return modified_AB


def adjust_pos(modified_script):
    i = 0
    while i < len(modified_script) - 1:
        inst1 = modified_script[i][0]
        if inst1 == definitions.INSERT or inst1 == definitions.MOVE or inst1 == definitions.UPDATEMOVE:
            node_into_1 = modified_script[i][2]
            k = i + 1
            for j in range(i + 1, len(modified_script)):
                k = j
                inst2 = modified_script[j][0]
                if inst2 != definitions.INSERT and inst2 != definitions.MOVE:
                    k -= 1
                    break
                node_into_2 = modified_script[j][2]
                if node_into_1 != node_into_2:
                    k -= 1
                    break
                pos_at_1 = int(modified_script[j - 1][3])
                pos_at_2 = int(modified_script[j][3])
                if pos_at_1 < pos_at_2 - 1:
                    k -= 1
                    break
            k += 1
            for l in range(i, k):
                inst = modified_script[l][0]
                node1 = modified_script[l][1]
                node2 = modified_script[l][2]
                pos = int(modified_script[i][3])
                modified_script[l] = (inst, node1, node2, pos)
            i = k
        else:
            i += 1
    return modified_script


def rewrite_as_script(modified_script):
    instruction_AB = []
    delete_instruction_list = dict()
    for i in modified_script:
        inst = i[0]
        if inst == definitions.DELETE:
            nodeA = i[1].simple_print()
            delete_instruction_list[int(get_id(nodeA))] = (definitions.DELETE, nodeA)
        elif inst == definitions.UPDATE:
            nodeA = i[1].simple_print()
            nodeB = i[2].simple_print()
            instruction_AB.append((definitions.UPDATE, nodeA, nodeB))
        elif inst == definitions.REPLACE:
            nodeA = i[1].simple_print()
            nodeB = i[2].simple_print()
            instruction_AB.append((definitions.REPLACE, nodeA, nodeB))
        elif inst == definitions.INSERT:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((definitions.INSERT, nodeB1, nodeB2, pos))
        elif inst == definitions.MOVE:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((definitions.MOVE, nodeB1, nodeB2, pos))
        elif inst == definitions.UPDATEMOVE:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((definitions.UPDATEMOVE, nodeB1, nodeB2, pos))

    # insert sorted delete insturctions
    for node_id in sorted(delete_instruction_list.keys()):
        instruction_AB.insert(0,delete_instruction_list[node_id])
    return instruction_AB


def get_instruction(instruction_data):
    operation = instruction_data[0]
    instruction = ""

    if operation == definitions.UPDATE:
        nodeC = instruction_data[1]
        nodeD = instruction_data[2]
        instruction = definitions.UPDATE + " " + nodeC.simple_print() + definitions.TO + nodeD.simple_print()

    elif operation == definitions.REPLACE:
        nodeC = instruction_data[1]
        nodeD = instruction_data[2]
        instruction = definitions.REPLACE + " " + nodeC.simple_print() + definitions.WITH + nodeD.simple_print()

    elif operation == definitions.DELETE:
        nodeC = instruction_data[1]
        instruction = definitions.DELETE + " " + nodeC.simple_print()

    elif operation == definitions.MOVE:
        nodeD1 = instruction_data[1].simple_print()
        nodeD2 = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = definitions.MOVE + " " + nodeD1 + definitions.INTO + nodeD2 + definitions.AT + pos

    elif operation == definitions.INSERT:
        nodeB = instruction_data[1].simple_print()
        nodeC = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = definitions.INSERT + " " + nodeB + definitions.INTO + nodeC + definitions.AT + pos

    elif operation == definitions.UPDATEMOVE:
        nodeD1 = instruction_data[1].simple_print()
        nodeD2 = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = definitions.UPDATEMOVE + " " + nodeD1 + definitions.INTO + nodeD2 + definitions.AT + pos

    return instruction + "\n"


def translate_script_list(file_list, generated_data):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    translated_script_list = dict()

    slice_file_a = file_list[0]
    slice_file_b = file_list[1]
    slice_file_c = file_list[2]
    vector_source_a = get_source_name_from_slice(slice_file_a)
    vector_source_b = get_source_name_from_slice(slice_file_b)
    vector_source_c = get_source_name_from_slice(slice_file_c)

    utilities.shift_slice_source(slice_file_a, slice_file_c)
    emitter.normal("\tgenerating AST in JSON")
    ast_tree_a = ast_generator.get_ast_json(vector_source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(vector_source_c, values.DONOR_REQUIRE_MACRO, regenerate=True)

    json_ast_dump = gen_temp_json(vector_source_a, vector_source_b, vector_source_c)

    neighbor_ast_a = None
    neighbor_ast_c = None
    neighbor_ast_range = None
    neighbor_type_a, neighbor_name_a, slice_a = str(slice_file_a).split("/")[-1].split(".c.")[-1].split(".")
    neighbor_type_c, neighbor_name_c, slice_c = str(slice_file_c).split("/")[-1].split(".c.")[-1].split(".")
    if neighbor_type_a == "func":
        neighbor_ast_a = finder.search_function_node_by_name(ast_tree_a, neighbor_name_a)
        neighbor_ast_c = finder.search_function_node_by_name(ast_tree_c, neighbor_name_c)
    elif neighbor_type_a == "var":
        # neighbor_name = neighbor_name[:neighbor_name.rfind("_")]
        neighbor_ast_a = finder.search_node(ast_tree_a, "VarDecl", neighbor_name_a)
        neighbor_ast_c = finder.search_node(ast_tree_c, "VarDecl", neighbor_name_c)
    elif neighbor_type_a == "struct":
        neighbor_ast_a = finder.search_node(ast_tree_a, "RecordDecl", neighbor_name_a)
        neighbor_ast_c = finder.search_node(ast_tree_c, "RecordDecl", neighbor_name_c)
    if neighbor_ast_a:
        neighbor_ast_range = (int(neighbor_ast_a['begin']), int(neighbor_ast_a['end']))
    else:
        utilities.error_exit("No neighbor AST Found")

    original_script = list()
    for instruction in generated_data[0]:
        instruction_line = ""
        for token in instruction:
            instruction_line += token + " "
        original_script.append(instruction_line)
    emitter.information(original_script)
    modified_script = simplify_patch(generated_data[0], generated_data[2], json_ast_dump)
    emitter.information(modified_script)
    modified_script.sort(key=cmp_to_key(order_comp))
    modified_script = rewrite_as_script(modified_script)
    emitter.information(modified_script)
    # We get the matching nodes from Pa to Pc into a dict
    map_ac = values.ast_map[(slice_file_a, slice_file_c)]
    translated_script = transform_script_gumtree(modified_script, generated_data[1], json_ast_dump,
                                                 generated_data[2], map_ac, int(neighbor_ast_c['id']))
    emitter.information(translated_script)
    if not translated_script:
        emitter.warning("failed to translate AST transformation")
        emitter.warning("trying to use different if-def combination")
        values.TARGET_REQUIRE_MACRO = not values.TARGET_REQUIRE_MACRO
        # values.ast_map, values.map_namespace_global = mapper.generate_map(values.generated_script_files)
        translated_script = transform_script_gumtree(modified_script, generated_data[1], json_ast_dump,
                                                     generated_data[2], map_ac, int(neighbor_ast_c['id']))
        if not translated_script:
            error_exit("Unable to translate the script")

    translated_script_list[file_list] = (translated_script, original_script)
    utilities.restore_slice_source()
    return translated_script, original_script

