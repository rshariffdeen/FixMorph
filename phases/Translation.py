import time
from common import Definitions
from common.Utilities import execute_command, error_exit
from tools import Emitter
from ast import Parser


def id_from_string(simplestring):
    return int(simplestring.split("(")[-1][:-1])


def get_id(node_ref):
    return int(node_ref.split("(")[-1][:-1])


def get_type(node_ref):
    return node_ref.split("(")[0]


def inst_comp(i):
    return Definitions.order.index(i)


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
    Print.blue("Generating JSON temp files for each pertinent file...")
    ASTlists = dict()
    try:
        gen_json(file_a, Definitions.Pa.name, ASTlists)
        gen_json(file_b, Definitions.Pb.name, ASTlists)
        gen_json(file_c, Definitions.Pc.name, ASTlists)
    except Exception as e:
        err_exit(e, "Error parsing with crochet-diff. Did you bear make?")
    return ASTlists


def ASTdump(file, output):
    extra_arg = ""
    if file[-1] == "h":
        extra_arg = " --"
    c = Definitions.DIFF_COMMAND + " -s=" + Definitions.DIFF_SIZE + " -ast-dump-json " + \
        file + extra_arg + " 2> output/errors_AST_dump > " + output
    exec_com(c)


def gen_json(file, name, ASTlists):
    Print.blue("\t\tClang AST parse " + file + " in " + name + "...")
    json_file = "output/json_" + name
    ASTdump(file, json_file)
    ASTlists[name] = Parser.AST_from_file(json_file)


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
        parent_b = json_ast_dump[Definitions.Pa.name][node_a.parent_id]
        parent_c = json_ast_dump[Definitions.Pc.name][node_c.parent_id]
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
        parent_a = json_ast_dump[Definitions.Pa.name][node_a.parent_id]
        parent_c = json_ast_dump[Definitions.Pc.name][node_c.parent_id]
        if match_nodes(parent_a, parent_c):
            return match_path(parent_a, parent_c, json_ast_dump)
        else:
            return False
    else:
        return False


def get_candidate_node_list(node_ref, json_ast_dump):
    candidate_node_list = list()
    node_id = get_id(node_ref)
    node_a = json_ast_dump[Definitions.Pa.name][node_id]
    Print.blue(node_a)
    parent_id = node_a.parent_id
    while parent_id is not None:
        parent = json_ast_dump[Definitions.Pa.name][parent_id]
        Print.blue(str(parent.id) + " - " + parent.type)
        parent_id = parent.parent_id

    for node_c in json_ast_dump[Definitions.Pc.name]:
        if match_nodes(node_a, node_c):
            if match_path(node_a, node_c, json_ast_dump):
                if node_c not in candidate_node_list:
                    candidate_node_list.append(node_c)

    for node in candidate_node_list:
        Print.rose("Node: " + str(node.id))
        parent_id = node.parent_id
        while parent_id is not None:
            parent = json_ast_dump[Definitions.Pc.name][parent_id]
            Print.rose(str(parent.id) + " - " + parent.type)
            parent_id = parent.parent_id

    return candidate_node_list


def transform_script(modified_script, inserted_node_list, json_ast_dump, map_ab, map_ac):
    translated_instruction_list = list()
    inserted_D = list()
    match_BD = dict()
    for i in modified_script:
        operation = i[0]
        # Update nodeA to nodeB (value) -> Update nodeC to nodeD (value)
        if operation == Definitions.UPDATE:
            try:
                target_node_a_txt = i[1]
                update_node_txt = i[2]
                update_node_id = id_from_string(update_node_txt)
                update_node = json_ast_dump[Definitions.Pb.name][update_node_id]
                candidate_node_list = get_candidate_node_list(target_node_a_txt, json_ast_dump)

                if len(candidate_node_list) == 0:
                    Print.warning("Warning: No candidates for " + str(target_node_a_txt) + ", Skipping UPDATE")
                else:
                    for candidate_node in candidate_node_list:
                        if candidate_node.line is None:
                            candidate_node.line = candidate_node.parent.line
                        instruction = get_instruction((Definitions.UPDATE, candidate_node, update_node))
                        translated_instruction_list.append(instruction)
                if target_node_a_txt in map_ac.keys():
                    target_node_txt = map_ac[target_node_a_txt]
                    target_node_id = id_from_string(target_node_txt)
                    target_node = json_ast_dump[Definitions.Pc.name][target_node_id]
                    if target_node.line is None:
                        target_node.line = target_node.parent.line
                    instruction = get_instruction((Definitions.UPDATE, target_node, update_node))
                    translated_instruction_list.append(instruction)

                else:
                    Print.warning("Warning: Match for " + str(target_node_a_txt) + "not found. Skipping UPDATE instruction.")
            except Exception as e:
                err_exit(e, "Something went wrong with UPDATE.")

        # Delete nodeA -> Delete nodeC
        elif operation == Definitions.DELETE:
            Print.blue(i)
            try:
                delete_node_a_txt = i[1]
                candidate_node_list = get_candidate_node_list(delete_node_a_txt, json_ast_dump)
                if len(candidate_node_list) == 0:
                    Print.warning("Warning: No candidates for " + str(delete_node_a_txt) + ", Skipping DELETE")
                else:
                    for candidate_node in candidate_node_list:
                        if candidate_node.line is None:
                            candidate_node.line = candidate_node.parent.line
                        instruction = get_instruction((Definitions.DELETE, candidate_node))
                        Print.rose(instruction)
                        translated_instruction_list.append(instruction)

                if delete_node_a_txt in map_ac.keys():
                    delete_node_txt = map_ac[delete_node_a_txt]
                    delete_node_id = id_from_string(delete_node_txt)
                    delete_node = json_ast_dump[Definitions.Pc.name][delete_node_id]

                    if delete_node.line is None:
                        delete_node.line = delete_node.parent.line
                    instruction = get_instruction((Definitions.DELETE, delete_node))
                    Print.white(instruction)
                    translated_instruction_list.append(instruction)
                    parent_id = delete_node.parent_id
                    while parent_id is not None:
                        parent = json_ast_dump[Definitions.Pc.name][parent_id]
                        print(str(parent.id) + " - " + parent.type)
                        parent_id = parent.parent_id

                else:
                    Print.warning("Warning: Match for " + str(delete_node_a_txt) + "not found. Skipping DELETE instruction.")

            except Exception as e:
                err_exit(e, "Something went wrong with DELETE.")

        # Move nodeA to nodeB at pos -> Move nodeC to nodeD at pos
        elif operation == Definitions.MOVE:
            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeC1 = "?"
                nodeC2 = "?"
                if nodeB1 in map_ab.keys():
                    nodeA1 = map_ab[nodeB1]
                    if nodeA1 in map_ac.keys():
                        nodeC1 = map_ac[nodeA1]
                        nodeC1 = id_from_string(nodeC1)
                        nodeC1 = json_ast_dump[Definitions.Pc.name][nodeC1]
                    else:
                        # TODO: Manage case in which nodeA1 is unmatched
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(nodeA1)
                elif nodeB1 in inserted_node_list:
                    if nodeB1 in match_BD.keys():
                        nodeC1 = match_BD[nodeB1]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(nodeB1)
                if nodeB2 in map_ab.keys():
                    nodeA2 = map_ab[nodeB2]
                    if nodeA2 in map_ac.keys():
                        nodeC2 = map_ac[nodeA2]
                        nodeC2 = id_from_string(nodeC2)
                        nodeC2 = json_ast_dump[Definitions.Pc.name][nodeC2]
                    else:
                        # TODO: Manage case for unmatched nodeA2
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(nodeA2)
                elif nodeB2 in inserted_node_list:
                    if nodeB2 in match_BD.keys():
                        nodeC2 = match_BD[nodeB2]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(nodeB2)
                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = json_ast_dump[Definitions.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeC2_l = map_ac[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = json_ast_dump[Definitions.Pc.name][nodeC2_l]
                                if nodeC2_l in nodeC2.children:
                                    pos = nodeC2.children.index(nodeC2_l)
                                    pos += 1
                                else:
                                    Print.warning("Node not in children.")
                                    Print.warning(nodeC2_l)
                                    Print.warning([i.simple_print() for i in
                                                   nodeC2.children])
                            else:
                                Print.warning("Failed at locating match" + \
                                              " for " + nodeA2_l)
                                Print.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                nodeA2_l = id_from_string(nodeA2_l)
                                nodeA2_l = json_ast_dump[Definitions.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")

                if type(nodeC1) == Parser.AST:
                    if nodeC1.line == None:
                        nodeC1.line = nodeC1.parent.line
                    if type(nodeC2) == Parser.AST:
                        if nodeC2.line == None:
                            nodeC2.line = nodeD.parent.line
                        if nodeC2 in inserted_D:
                            instruction = get_instruction((Definitions.DELETE, nodeC1))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((Definitions.MOVE, nodeC1, nodeC2, pos))
                            translated_instruction_list.append(instruction)
                        inserted_D.append(nodeC1)

                    else:
                        Print.warning("Could not find match for node. " + \
                                      "Ignoring MOVE operation. (D)")
                else:
                    Print.warning("Could not find match for node. " + \
                                  "Ignoring MOVE operation. (C)")
            except Exception as e:
                err_exit(e, "Something went wrong with MOVE.")

        # Update nodeA and move to nodeB at pos -> Move nodeC to nodeD at pos
        elif operation == Definitions.UPDATEMOVE:

            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeC1 = "?"
                nodeC2 = "?"
                if nodeB1 in map_ab.keys():
                    nodeA1 = map_ab[nodeB1]
                    if nodeA1 in map_ac.keys():
                        nodeC1 = map_ac[nodeA1]
                        nodeC1 = id_from_string(nodeC1)
                        nodeC1 = json_ast_dump[Definitions.Pc.name][nodeC1]
                    else:
                        # TODO: Manage case in which nodeA1 is unmatched
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(nodeA1)
                elif nodeB1 in inserted_node_list:
                    if nodeB1 in match_BD.keys():
                        nodeC1 = match_BD[nodeB1]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(nodeB1)
                if nodeB2 in map_ab.keys():
                    nodeA2 = map_ab[nodeB2]
                    if nodeA2 in map_ac.keys():
                        nodeC2 = map_ac[nodeA2]
                        nodeC2 = id_from_string(nodeC2)
                        nodeC2 = json_ast_dump[Definitions.Pc.name][nodeC2]
                    else:
                        # TODO: Manage case for unmatched nodeA2
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(nodeA2)
                elif nodeB2 in inserted_node_list:
                    if nodeB2 in match_BD.keys():
                        nodeC2 = match_BD[nodeB2]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(nodeB2)
                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = json_ast_dump[Definitions.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeC2_l = map_ac[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = json_ast_dump[Definitions.Pc.name][nodeC2_l]
                                if nodeC2_l in nodeC2.children:
                                    pos = nodeC2.children.index(nodeC2_l)
                                    pos += 1
                                else:
                                    Print.warning("Node not in children.")
                                    Print.warning(nodeC2_l)
                                    Print.warning([i.simple_print() for i in
                                                   nodeC2.children])
                            else:
                                Print.warning("Failed at locating match" + \
                                              " for " + nodeA2_l)
                                Print.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                nodeA2_l = id_from_string(nodeA2_l)
                                nodeA2_l = json_ast_dump[Definitions.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")

                if type(nodeC1) == Parser.AST:
                    if nodeC1.line == None:
                        nodeC1.line = nodeC1.parent.line
                    if type(nodeC2) == Parser.AST:
                        if nodeC2.line == None:
                            nodeC2.line = nodeD.parent.line
                        if nodeC2 in inserted_D:
                            instruction = get_instruction((Definitions.DELETE, nodeC1))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((Definitions.UPDATEMOVE, nodeC1, nodeC2, pos))
                            translated_instruction_list.append(instruction)
                        inserted_D.append(nodeC1)

                    else:
                        Print.warning("Could not find match for node. " + \
                                      "Ignoring UPDATEMOVE operation. (D)")
                else:
                    Print.warning("Could not find match for node. " + \
                                  "Ignoring UPDATEMOVE operation. (C)")
            except Exception as e:
                err_exit(e, "Something went wrong with UPDATEMOVE.")

        # Insert nodeB1 to nodeB2 at pos -> Insert nodeD1 to nodeD2 at pos
        elif operation == Definitions.INSERT:
            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeD1 = id_from_string(nodeB1)
                nodeD1 = json_ast_dump[Definitions.Pb.name][nodeD1]
                nodeD2 = id_from_string(nodeB2)
                nodeD2 = json_ast_dump[Definitions.Pb.name][nodeD2]
                # TODO: Is this correct?
                if nodeD2.line != None:
                    nodeD1.line = nodeD2.line
                else:
                    nodeD1.line = nodeD2.parent.line
                if nodeB2 in map_ab.keys():
                    nodeA2 = map_ab[nodeB2]
                    if nodeA2 in map_ac.keys():
                        nodeD2 = map_ac[nodeA2]
                        nodeD2 = id_from_string(nodeD2)
                        nodeD2 = json_ast_dump[Definitions.Pc.name][nodeD2]
                elif nodeB2 in match_BD.keys():
                    nodeD2 = match_BD[nodeB2]
                else:
                    Print.warning("Warning: node for insertion not" + \
                                  " found. Skipping INSERT operation.")

                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = json_ast_dump[Definitions.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeD2_l = map_ac[nodeA2_l]
                                nodeD2_l = id_from_string(nodeD2_l)
                                nodeD2_l = json_ast_dump[Definitions.Pc.name][nodeD2_l]
                                if nodeD2_l in nodeD2.children:
                                    pos = nodeD2.children.index(nodeD2_l)
                                    pos += 1
                                else:
                                    Print.warning("Node not in children.")
                                    Print.warning(nodeD2_l)
                                    Print.warning([i.simple_print() for i in
                                                   nodeD2.children])
                            else:
                                Print.warning("Failed at locating match" + \
                                              " for " + nodeA2_l)
                                Print.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                nodeA2_l = id_from_string(nodeA2_l)
                                nodeA2_l = json_ast_dump[Definitions.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1

                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")
                if type(nodeD1) == Parser.AST:
                    match_BD[nodeB1] = nodeD1
                    inserted_D.append(nodeD1)
                    nodeD1.children = []
                    if nodeD1.line == None:
                        nodeD1.line = nodeD1.parent.line
                    if type(nodeD2) == Parser.AST:
                        if nodeD2.line == None:
                            nodeD2.line = nodeD2.parent.line
                        if nodeD2 not in inserted_D:
                            instruction = get_instruction((Definitions.INSERT, nodeD1, nodeD2, pos))
                            translated_instruction_list.append(instruction)
            except Exception as e:
                err_exit(e, "Something went wrong with INSERT.")

    return translated_instruction_list


def transform_script_gumtree(modified_script, inserted_node_list, json_ast_dump, map_ab, map_ac):
    translated_instruction_list = list()
    inserted_node_list_d = list()
    deleted_node_list_d = dict()
    map_bd = dict()
    for instruction in modified_script:
        operation = instruction[0]
        # Update nodeA to nodeB (value) -> Update nodeC to nodeD (value)
        if operation == Definitions.UPDATE:
            try:
                txt_target_node_a = instruction[1]
                txt_update_node = instruction[2]
                target_node = "?"
                update_node_id = id_from_string(txt_update_node)
                update_node = json_ast_dump[Definitions.Pb.name][update_node_id]

                if txt_target_node_a in map_ac.keys():
                    txt_target_node = map_ac[txt_target_node_a]
                    target_node_id = id_from_string(txt_target_node)
                    target_node = json_ast_dump[Definitions.Pc.name][target_node_id]

                    if target_node.line is None:
                        target_node.line = target_node.parent.line
                    instruction = get_instruction((Definitions.UPDATE, target_node, update_node))
                    translated_instruction_list.append(instruction)

                else:
                    Print.warning("Warning: Match for " + str(txt_target_node_a) + "not found. Skipping UPDATE instruction.")

            except Exception as e:
                err_exit(e, "Something went wrong with UPDATE.")

        # Delete nodeA -> Delete nodeC
        elif operation == Definitions.DELETE:
            try:
                txt_delete_node_a = instruction[1]
                delete_node = "?"
                if txt_delete_node_a in map_ac.keys():
                    txt_delete_node = map_ac[txt_delete_node_a]
                    delete_node_id = id_from_string(txt_delete_node)
                    delete_node = json_ast_dump[Definitions.Pc.name][delete_node_id]
                    instruction = get_instruction((Definitions.DELETE, delete_node))
                    if delete_node.line is None:
                        delete_node.line = delete_node.parent.line
                    deleted_node_list_d[delete_node.id] = delete_node
                    if delete_node.parent_id:
                        if deleted_node_list_d.get(delete_node.parent_id) is None:
                            translated_instruction_list.append(instruction)
                    else:
                        translated_instruction_list.append(instruction)

                else:
                    Print.warning("Warning: Match for " + str(txt_delete_node_a) + \
                                  "not found. Skipping DELETE instruction.")
            except Exception as e:
                err_exit(e, "Something went wrong with DELETE.")
            # Move nodeA to nodeB at pos -> Move nodeC to nodeD at pos
        elif operation == Definitions.MOVE:
            try:
                txt_move_node_b = instruction[1]
                txt_target_node_b = instruction[2]
                offset = int(instruction[3])
                move_node = "?"
                target_node = "?"
                if txt_move_node_b in map_ab.keys():
                    txt_move_node_a = map_ab[txt_move_node_b]
                    if txt_move_node_a in map_ac.keys():
                        txt_move_node = map_ac[txt_move_node_a]
                        mode_node_id = id_from_string(txt_move_node)
                        move_node = json_ast_dump[Definitions.Pc.name][mode_node_id]
                    else:
                        # TODO: Manage case in which txt_move_node_a is unmatched
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(txt_move_node_a)
                elif txt_move_node_b in inserted_node_list:
                    if txt_move_node_b in map_bd.keys():
                        move_node = map_bd[txt_move_node_b]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(txt_move_node_b)
                if txt_target_node_b in map_ab.keys():
                    txt_target_node_a = map_ab[txt_target_node_b]
                    if txt_target_node_a in map_ac.keys():
                        txt_target_node = map_ac[txt_target_node_a]
                        target_node_id = id_from_string(txt_target_node)
                        target_node = json_ast_dump[Definitions.Pc.name][target_node_id]
                    else:
                        # TODO: Manage case for unmatched nodeA2
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(txt_target_node_a)
                elif txt_target_node_b in inserted_node_list:
                    if txt_target_node_b in map_bd.keys():
                        target_node = map_bd[txt_target_node_b]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(txt_target_node_b)
                try:
                    target_node_b_id = id_from_string(txt_target_node_b)
                    target_node_b = json_ast_dump[Definitions.Pb.name][target_node_b_id]
                    if offset != 0:
                        previous_child_node_b = target_node_b.children[offset - 1]
                        previous_child_node_b = previous_child_node_b.simple_print()
                        if previous_child_node_b in map_ab.keys():
                            previous_child_node_a = map_ab[previous_child_node_b]
                            if previous_child_node_a in map_ac.keys():
                                previous_child_c = map_ac[previous_child_node_a]
                                previous_child_c = id_from_string(previous_child_c)
                                previous_child_c = json_ast_dump[Definitions.Pc.name][previous_child_c]
                                if previous_child_c in target_node.children:
                                    offset = target_node.children.index(previous_child_c)
                                    offset += 1
                                else:
                                    Print.warning("Node not in children.")
                                    Print.warning(previous_child_c)
                                    Print.warning([instruction.simple_print() for instruction in
                                                   target_node.children])
                            else:
                                Print.warning("Failed at locating match" + \
                                              " for " + previous_child_node_a)
                                Print.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                previous_child_node_a = id_from_string(previous_child_node_a)
                                previous_child_node_a = json_ast_dump[Definitions.Pa.name][previous_child_node_a]
                                parent = previous_child_node_a.parent
                                if parent != None:
                                    offset = parent.children.index(previous_child_node_a)
                                    offset += 1
                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")

                if type(move_node) == Parser.AST:
                    if move_node.line is None:
                        move_node.line = move_node.parent.line
                    if type(target_node) == Parser.AST:
                        if target_node.line is None:
                            target_node.line = target_node.parent.line
                        if target_node in inserted_node_list_d:
                            instruction = get_instruction((Definitions.DELETE, move_node))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((Definitions.MOVE, move_node, target_node, offset))
                            translated_instruction_list.append(instruction)
                        inserted_node_list_d.append(move_node)

                    else:
                        Print.warning("Could not find match for node. " + \
                                      "Ignoring MOVE operation. (D)")
                else:
                    Print.warning("Could not find match for node. " + \
                                  "Ignoring MOVE operation. (C)")
            except Exception as e:
                err_exit(e, "Something went wrong with MOVE.")

            # Update nodeA and move to nodeB at pos -> Move nodeC to nodeD at pos
        elif operation == Definitions.UPDATEMOVE:

            try:
                txt_move_node_b = instruction[1]
                txt_target_node_b = instruction[2]
                offset = int(instruction[3])
                move_node = "?"
                target_node = "?"
                if txt_move_node_b in map_ab.keys():
                    txt_move_node_a = map_ab[txt_move_node_b]
                    if txt_move_node_a in map_ac.keys():
                        txt_move_node = map_ac[txt_move_node_a]
                        move_node_id = id_from_string(txt_move_node)
                        move_node = json_ast_dump[Definitions.Pc.name][move_node_id]
                    else:
                        # TODO: Manage case in which txt_move_node_a is unmatched
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(txt_move_node_a)
                elif txt_move_node_b in inserted_node_list:
                    if txt_move_node_b in map_bd.keys():
                        move_node = map_bd[txt_move_node_b]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(txt_move_node_b)
                if txt_target_node_b in map_ab.keys():
                    txt_target_node_a = map_ab[txt_target_node_b]
                    if txt_target_node_a in map_ac.keys():
                        txt_target_node = map_ac[txt_target_node_a]
                        target_node_id = id_from_string(txt_target_node)
                        target_node = json_ast_dump[Definitions.Pc.name][target_node_id]
                    else:
                        # TODO: Manage case for unmatched txt_target_node_a
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(txt_target_node_a)
                elif txt_target_node_b in inserted_node_list:
                    if txt_target_node_b in map_bd.keys():
                        target_node = map_bd[txt_target_node_b]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(txt_target_node_b)
                try:
                    target_node_b_id = id_from_string(txt_target_node_b)
                    target_node_b = json_ast_dump[Definitions.Pb.name][target_node_b_id]
                    if offset != 0:
                        previous_child_node_b = target_node_b.children[offset - 1]
                        previous_child_node_b = previous_child_node_b.simple_print()
                        if previous_child_node_b in map_ab.keys():
                            previous_child_node_a = map_ab[previous_child_node_b]
                            if previous_child_node_a in map_ac.keys():
                                previous_child_c = map_ac[previous_child_node_a]
                                previous_child_c = id_from_string(previous_child_c)
                                previous_child_c = json_ast_dump[Definitions.Pc.name][previous_child_c]
                                if previous_child_c in target_node.children:
                                    offset = target_node.children.index(previous_child_c)
                                    offset += 1
                                else:
                                    Print.warning("Node not in children.")
                                    Print.warning(previous_child_c)
                                    Print.warning([instruction.simple_print() for instruction in
                                                   target_node.children])
                            else:
                                Print.warning("Failed at locating match" + \
                                              " for " + previous_child_node_a)
                                Print.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                previous_child_node_a = id_from_string(previous_child_node_a)
                                previous_child_node_a = json_ast_dump[Definitions.Pa.name][previous_child_node_a]
                                parent = previous_child_node_a.parent
                                if parent != None:
                                    offset = parent.children.index(previous_child_node_a)
                                    offset += 1
                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")

                if type(move_node) == Parser.AST:
                    if move_node.line is None:
                        move_node.line = move_node.parent.line
                    if type(target_node) == Parser.AST:
                        if target_node.line is None:
                            target_node.line = target_node.parent.line
                        if target_node in inserted_node_list_d:
                            instruction = get_instruction((Definitions.DELETE, move_node))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((Definitions.UPDATEMOVE, move_node, target_node, offset))
                            translated_instruction_list.append(instruction)

                        inserted_node_list_d.append(move_node)

                    else:
                        Print.warning("Could not find match for node. " + \
                                      "Ignoring UPDATEMOVE operation. (D)")
                else:
                    Print.warning("Could not find match for node. " + \
                                  "Ignoring UPDATEMOVE operation. (C)")
            except Exception as e:
                err_exit(e, "Something went wrong with UPDATEMOVE.")

        # Insert nodeB1 to nodeB2 at pos -> Insert nodeD1 to nodeD2 at pos
        elif operation == Definitions.INSERT:
            try:
                txt_insert_node = instruction[1]
                txt_target_node_b = instruction[2]
                offset = int(instruction[3])
                insert_node_id = id_from_string(txt_insert_node)
                insert_node = json_ast_dump[Definitions.Pb.name][insert_node_id]
                target_node_b_id = id_from_string(txt_target_node_b)
                target_node_b = json_ast_dump[Definitions.Pb.name][target_node_b_id]
                # TODO: Is this correct?
                if target_node_b.line is not None:
                    insert_node.line = target_node_b.line
                else:
                    insert_node.line = target_node_b.parent.line

                if txt_target_node_b in map_ab.keys():
                    txt_target_node_a = map_ab[txt_target_node_b]
                    if txt_target_node_a in map_ac.keys():
                        txt_target_node = map_ac[txt_target_node_a]
                        target_node_id = id_from_string(txt_target_node)
                        target_node = json_ast_dump[Definitions.Pc.name][target_node_id]
                elif txt_target_node_b in map_bd.keys():
                    target_node = map_bd[txt_target_node_b]
                else:
                    Print.warning("Warning: node for insertion not" + \
                                  " found. Skipping INSERT operation.")

                try:
                    if offset != 0:
                        previous_child_node_b = target_node_b.children[offset - 1]
                        previous_child_node_b = previous_child_node_b.simple_print()
                        if previous_child_node_b in map_ab.keys():
                            previous_child_node_a = map_ab[previous_child_node_b]
                            if previous_child_node_a in map_ac.keys():
                                previous_child_node_c = map_ac[previous_child_node_a]
                                previous_child_node_c = id_from_string(previous_child_node_c)
                                previous_child_node_c = json_ast_dump[Definitions.Pc.name][previous_child_node_c]
                                if previous_child_node_c in target_node.children:
                                    offset = target_node.children.index(previous_child_node_c)
                                    offset += 1
                                else:
                                    if offset + 1 < len(target_node_b.children):
                                        next_child_node_b = target_node_b.children[offset + 1]
                                        next_child_node_b = next_child_node_b.simple_print()
                                        if next_child_node_b in map_ab.keys():
                                            next_child_node_a = map_ab[next_child_node_b]
                                            if next_child_node_a in map_ac.keys():
                                                next_child_node_c = map_ac[next_child_node_a]
                                                next_child_node_c = id_from_string(next_child_node_c)
                                                next_child_node_c = json_ast_dump[Definitions.Pc.name][next_child_node_c]
                                                if next_child_node_c in target_node.children:
                                                    offset = target_node.children.index(next_child_node_c)
                                                else:
                                                    Print.warning("Node not in children.")
                                                    Print.warning(instruction)
                                                    Print.warning(next_child_node_c)
                                                    Print.warning([child.simple_print() for child in target_node.children])
                                                    target_node = json_ast_dump[
                                                        Definitions.Pc.name][next_child_node_c.parent_id]
                                                    offset = target_node.children.index(next_child_node_c)

                            else:
                                Print.warning("Failed at locating match" + \
                                              " for " + previous_child_node_a)
                                Print.warning("Trying to get pos anyway.")
                                # This is more likely to be correct
                                previous_child_node_a = id_from_string(previous_child_node_a)
                                previous_child_node_a = json_ast_dump[Definitions.Pa.name][previous_child_node_a]
                                parent = previous_child_node_a.parent
                                if parent is not None:
                                    offset = parent.children.index(previous_child_node_a)
                                    offset += 1

                        elif offset + 1 < len(target_node_b.children):
                            next_child_node_b = target_node_b.children[offset + 1]
                            next_child_node_b = next_child_node_b.simple_print()
                            if next_child_node_b in map_ab.keys():
                                next_child_node_a = map_ab[next_child_node_b]
                                if next_child_node_a in map_ac.keys():
                                    next_child_node_c = map_ac[next_child_node_a]
                                    next_child_node_c = id_from_string(next_child_node_c)
                                    next_child_node_c = json_ast_dump[Definitions.Pc.name][next_child_node_c]
                                    if next_child_node_c in target_node.children:
                                        offset = target_node.children.index(next_child_node_c)
                                    else:
                                        Print.warning("Node not in children.")
                                        Print.warning(instruction)
                                        Print.warning(next_child_node_c)
                                        Print.warning([child.simple_print() for child in target_node.children])
                                        target_node = json_ast_dump[Definitions.Pc.name][next_child_node_c.parent_id]
                                        offset = target_node.children.index(next_child_node_c)

                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")
                if type(insert_node) == Parser.AST:
                    map_bd[txt_insert_node] = insert_node
                    inserted_node_list_d.append(insert_node)
                    insert_node.children = []
                    if insert_node.line == None:
                        insert_node.line = insert_node.parent.line
                    if type(target_node) == Parser.AST:
                        if target_node.line == None:
                            target_node.line = target_node.parent.line
                        if target_node not in inserted_node_list_d:
                            instruction = get_instruction((Definitions.INSERT, insert_node, target_node, offset))
                            translated_instruction_list.append(instruction)
            except Exception as e:
                err_exit(e, "Something went wrong with INSERT.")

    return translated_instruction_list


def simplify_patch(instruction_AB, match_BA, ASTlists):
    modified_AB = []
    inserted = []
    # Print.white("Original script from Pa to Pb")
    for i in instruction_AB:
        inst = i[0]
        if inst == Definitions.DELETE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[Definitions.Pa.name][nodeA]
            # Print.white("\t" + Common.DELETE + " - " + str(nodeA))
            modified_AB.append((Definitions.DELETE, nodeA))
        elif inst == Definitions.UPDATE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[Definitions.Pa.name][nodeA]
            nodeB = id_from_string(i[2])
            nodeB = ASTlists[Definitions.Pb.name][nodeB]
            # Print.white("\t" + Common.UPDATE + " - " + str(nodeA) + " - " + str(nodeB))
            modified_AB.append((Definitions.UPDATE, nodeA, nodeB))
        elif inst == Definitions.MOVE:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Definitions.Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Definitions.Pb.name][nodeB2]
            pos = i[3]
            # Print.white("\t" + Common.MOVE + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((Definitions.MOVE, nodeB1, nodeB2, pos))
            else:
                if i[1] in match_BA.keys():
                    nodeA = match_BA[i[1]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[Definitions.Pa.name][nodeA]
                    modified_AB.append((Definitions.DELETE, nodeA))
                else:
                    Print.warning("Warning: node " + str(nodeB1) + \
                                  "could not be matched. " + \
                                  "Skipping MOVE instruction...")
                    Print.warning(i)
        elif inst == Definitions.UPDATEMOVE:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Definitions.Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Definitions.Pb.name][nodeB2]
            pos = i[3]
            # Print.white("\t" + Common.UPDATEMOVE + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((Definitions.UPDATEMOVE, nodeB1, nodeB2, pos))
            else:
                if i[1] in match_BA.keys():
                    nodeA = match_BA[i[1]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[Definitions.Pa.name][nodeA]
                    modified_AB.append((Definitions.DELETE, nodeA))
                else:
                    Print.warning("Warning: node " + str(nodeB1) + \
                                  "could not be matched. " + \
                                  "Skipping MOVE instruction...")
                    Print.warning(i)
        elif inst == Definitions.INSERT:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Definitions.Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Definitions.Pb.name][nodeB2]
            pos = i[3]
            # Print.white("\t" + Common.INSERT + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((Definitions.INSERT, nodeB1, nodeB2, pos))
    return modified_AB


def remove_overlapping_delete(modified_AB):
    reduced_AB = set()
    n_i = len(modified_AB)
    for i in range(n_i):
        inst1 = modified_AB[i]
        if inst1[0] == Definitions.DELETE:
            for j in range(i + 1, n_i):
                inst2 = modified_AB[j]
                if inst2[0] == Definitions.DELETE:
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
        if inst1 == Definitions.INSERT or inst1 == Definitions.MOVE or inst1 == Definitions.UPDATEMOVE:
            node_into_1 = modified_script[i][2]
            k = i + 1
            for j in range(i + 1, len(modified_script)):
                k = j
                inst2 = modified_script[j][0]
                if inst2 != Definitions.INSERT and inst2 != Definitions.MOVE:
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
    for i in modified_script:
        inst = i[0]
        if inst == Definitions.DELETE:
            nodeA = i[1].simple_print()
            instruction_AB.append((Definitions.DELETE, nodeA))
        elif inst == Definitions.UPDATE:
            nodeA = i[1].simple_print()
            nodeB = i[2].simple_print()
            instruction_AB.append((Definitions.UPDATE, nodeA, nodeB))
        elif inst == Definitions.INSERT:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((Definitions.INSERT, nodeB1, nodeB2, pos))
        elif inst == Definitions.MOVE:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((Definitions.MOVE, nodeB1, nodeB2, pos))
        elif inst == Definitions.UPDATEMOVE:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((Definitions.UPDATEMOVE, nodeB1, nodeB2, pos))
    return instruction_AB


def get_instruction(instruction_data):
    operation = instruction_data[0]
    instruction = ""

    if operation == Definitions.UPDATE:
        nodeC = instruction_data[1]
        nodeD = instruction_data[2]
        instruction = Definitions.UPDATE + " " + nodeC.simple_print() + Definitions.TO + nodeD.simple_print()

    elif operation == Definitions.DELETE:
        nodeC = instruction_data[1]
        instruction = Definitions.DELETE + " " + nodeC.simple_print()

    elif operation == Definitions.MOVE:
        nodeD1 = instruction_data[1].simple_print()
        nodeD2 = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = Definitions.MOVE + " " + nodeD1 + Definitions.INTO + nodeD2 + Definitions.AT + pos

    elif operation == Definitions.INSERT:
        nodeB = instruction_data[1].simple_print()
        nodeC = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = Definitions.INSERT + " " + nodeB + Definitions.INTO + nodeC + Definitions.AT + pos

    elif operation == Definitions.UPDATEMOVE:
        nodeD1 = instruction_data[1].simple_print()
        nodeD2 = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = Definitions.UPDATEMOVE + " " + nodeD1 + Definitions.INTO + nodeD2 + Definitions.AT + pos

    return instruction


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Print.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Print.success("\n\tSuccessful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Print.error("Crash during " + description + ", after " + duration + " seconds.")
        err_exit(exception, "Unexpected error during " + description + ".")
    return result


def translate():
    Print.title("Translate GumTree Script")
    Print.sub_title("Translating scripts for header files")
    translated_script_list = dict()
    for file_list, generated_data in Definitions.generated_script_for_header_files.items():
        # Generate AST as json files
        json_ast_dump = gen_temp_json(file_list[0], file_list[1], file_list[2])

        original_script = list()
        for instruction in generated_data[0]:
            instruction_line = ""
            for token in instruction:
                instruction_line += token + " "
            original_script.append(instruction_line)
        # Simplify instructions to a smaller representative sequence of them
        modified_script = simplify_patch(generated_data[0], generated_data[2], json_ast_dump)
        # Sort in reverse order and depending on instruction for application
        modified_script.sort(key=cmp_to_key(order_comp))
        # Delete overlapping DELETE operations
        # modified_AB = remove_overlapping_delete(modified_AB)
        # Adjusting position for MOVE and INSERT operations
        # modified_AB = adjust_pos(modified_AB)
        # Printing modified simplified script
        Print.success("\tModified Script:")
        for j in [" - ".join([str(k) for k in i]) for i in modified_script]:
            Print.success("\t" + j)
        # We rewrite the instruction as a script (str) instead of nodes
        modified_script = rewrite_as_script(modified_script)
        # We get the matching nodes from Pa to Pc into a dict
        variable_map = Definitions.variable_map[file_list]
        translated_script = transform_script_gumtree(modified_script, generated_data[1], json_ast_dump, generated_data[2],
                                             variable_map)
        translated_script_list[file_list] = (translated_script, original_script)

    Print.sub_title("Translating scripts for C files")
    for file_list, generated_data in Definitions.generated_script_for_c_files.items():
        json_ast_dump = gen_temp_json(file_list[0], file_list[1], file_list[2])

        original_script = list()
        for instruction in generated_data[0]:
            instruction_line = ""
            for token in instruction:
                instruction_line += token + " "
            original_script.append(instruction_line)

        # for instruction in generated_data[0]:
        #     original_script.append(get_instruction(instruction))
        # Simplify instructions to a smaller representative sequence of them
        modified_script = simplify_patch(generated_data[0], generated_data[2], json_ast_dump)
        # Sort in reverse order and depending on instruction for application
        modified_script.sort(key=cmp_to_key(order_comp))
        # Delete overlapping DELETE operations
        # modified_AB = remove_overlapping_delete(modified_AB)
        # Adjusting position for MOVE and INSERT operations
        # modified_script = adjust_pos(modified_script)
        # Printing modified simplified script
        # Print.success("\tModified Script:")
        # for j in [" - ".join([str(k) for k in i]) for i in modified_script]:
        #     Print.success("\t" + j)
        # We rewrite the instruction as a script (str) instead of nodes
        modified_script = rewrite_as_script(modified_script)
        # We get the matching nodes from Pa to Pc into a dict
        variable_map = Definitions.variable_map[file_list]
        translated_script = transform_script_gumtree(modified_script, generated_data[1], json_ast_dump,
                                                     generated_data[2], variable_map)
        translated_script_list[file_list] = (translated_script, original_script)

    Definitions.translated_script_for_files = translated_script_list
