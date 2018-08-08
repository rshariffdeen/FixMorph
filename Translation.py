import os
import sys
import time
import Common
import Initialization
import Detection
from Utils import exec_com, err_exit, find_files, clean, get_extensions
import Project
import Print
import ASTVector
import ASTgen
import ASTparser


def id_from_string(simplestring):
    return int(simplestring.split("(")[-1][:-1])


def get_id(node_ref):
    return int(node_ref.split("(")[-1][:-1])


def get_type(node_ref):
    return node_ref.split("(")[0]


def inst_comp(i):
    return Common.order.index(i)


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
        gen_json(file_a, Common.Pa.name, ASTlists)
        gen_json(file_b, Common.Pb.name, ASTlists)
        gen_json(file_c, Common.Pc.name, ASTlists)
    except Exception as e:
        err_exit(e, "Error parsing with crochet-diff. Did you bear make?")
    return ASTlists


def ASTdump(file, output):
    extra_arg = ""
    if file[-1] == "h":
        extra_arg = " --"
    c = Common.DIFF_COMMAND + " -s=" + Common.DIFF_SIZE + " -ast-dump-json " + \
        file + extra_arg + " 2> output/errors_AST_dump > " + output
    exec_com(c)


def gen_json(file, name, ASTlists):
    Print.blue("\t\tClang AST parse " + file + " in " + name + "...")
    json_file = "output/json_" + name
    ASTdump(file, json_file)
    ASTlists[name] = ASTparser.AST_from_file(json_file)


def match_nodes(node_b, node_c):
    check_operator_type_list = ["BinaryOperator", "UnaryOperator"]

    if node_b.type != node_c.type:
        return False
    else:
        if node_b.type in check_operator_type_list:
            if node_b.value != node_c.value:
                return False
            else:
                return True
        elif "Decl" in node_b.type or "Expr" in node_b.type or node_b.type == "Macro":
            if node_b.value != node_c.value:
                return False
            else:
                return True
        else:
            return True
    return False


def match_children(node_b, node_c, json_ast_dump):
    if node_b.parent_id is None and node_c.parent_id is None:
        return True
    elif node_b.parent_id is not None and node_c.parent_id is not None:
        parent_b = json_ast_dump[Common.Pb.name][node_b.parent_id]
        parent_c = json_ast_dump[Common.Pc.name][node_c.parent_id]
        if match_nodes(parent_b, parent_c):
            return match_path(parent_b, parent_c, json_ast_dump)
        else:
            return False
    else:
        return False


def match_path(node_b, node_c, json_ast_dump):
    if node_b.parent_id is None and node_c.parent_id is None:
        return True
    elif node_b.parent_id is not None and node_c.parent_id is not None:
        parent_b = json_ast_dump[Common.Pb.name][node_b.parent_id]
        parent_c = json_ast_dump[Common.Pc.name][node_c.parent_id]
        if match_nodes(parent_b, parent_c):
            return match_path(parent_b, parent_c, json_ast_dump)
        else:
            return False
    else:
        return False


def get_candidate_node_list(node_ref, json_ast_dump):
    candidate_node_list = list()
    node_id = get_id(node_ref)
    node_b = json_ast_dump[Common.Pb.name][node_id]
    print(node_b)

    for node_c in json_ast_dump[Common.Pc.name]:
        if match_nodes(node_b, node_c):
            if match_path(node_b, node_c, json_ast_dump):
                if node_c not in candidate_node_list:
                    candidate_node_list.append(node_c)

    for node in candidate_node_list:
        print("Node: " + str(node.id))
        parent_id = node.parent_id
        while parent_id is not None:
            parent = json_ast_dump[Common.Pc.name][parent_id]
            print(str(parent.id) + " - " + parent.type)
            parent_id = parent.parent_id

    return candidate_node_list


def transform_script(modified_script, inserted_node_list, json_ast_dump, map_ab, map_ac):
    translated_instruction_list = list()
    inserted_D = list()
    match_BD = dict()
    for i in modified_script:
        operation = i[0]
        # Update nodeA to nodeB (value) -> Update nodeC to nodeD (value)
        if operation == Common.UPDATE:
            try:
                nodeA = i[1]
                nodeB = i[2]
                nodeC = "?"
                nodeD = id_from_string(nodeB)
                nodeD = json_ast_dump[Common.Pb.name][nodeD]
                candidate_list = get_candidate_node_list(nodeA, json_ast_dump)
                if len(candidate_list) != 0:
                    for nodeC in candidate_list:
                        if nodeC.line == None:
                            nodeC.line = nodeC.parent.line
                        instruction = get_instruction((Common.UPDATE, nodeC, nodeD))
                        translated_instruction_list.append(instruction)
                else:
                    Print.warning("Warning: Match for " + str(nodeA) + "not found. Skipping UPDATE instruction.")
            except Exception as e:
                err_exit(e, "Something went wrong with UPDATE.")

        # Delete nodeA -> Delete nodeC
        elif operation == Common.DELETE:
            try:
                nodeA = i[1]
                nodeC = "?"
                if nodeA in map_ac.keys():
                    nodeC = map_ac[nodeA]
                    nodeC = id_from_string(nodeC)
                    candidate_list = get_candidate_node_list(nodeA, json_ast_dump)
                    if len(candidate_list) != 0:
                        for nodeC in candidate_list:
                            if nodeC.line == None:
                                nodeC.line = nodeC.parent.line
                            instruction = get_instruction((Common.DELETE, nodeC))
                            translated_instruction_list.append(instruction)
                    else:
                        Print.warning("Warning: Match for " + str(nodeA) + "not found. Skipping UPDATE instruction.")

                else:
                    Print.warning("Warning: Match for " + str(nodeA) + \
                                  "not found. Skipping DELETE instruction.")
            except Exception as e:
                err_exit(e, "Something went wrong with DELETE.")
        # Move nodeA to nodeB at pos -> Move nodeC to nodeD at pos
        elif operation == Common.MOVE:
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
                        nodeC1 = json_ast_dump[Common.Pc.name][nodeC1]
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
                        nodeC2 = json_ast_dump[Common.Pc.name][nodeC2]
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
                    true_B2 = json_ast_dump[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeC2_l = map_ac[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = json_ast_dump[Common.Pc.name][nodeC2_l]
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
                                nodeA2_l = json_ast_dump[Common.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")

                if type(nodeC1) == ASTparser.AST:
                    if nodeC1.line == None:
                        nodeC1.line = nodeC1.parent.line
                    if type(nodeC2) == ASTparser.AST:
                        if nodeC2.line == None:
                            nodeC2.line = nodeD.parent.line
                        if nodeC2 in inserted_D:
                            instruction = get_instruction((Common.DELETE, nodeC1))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((Common.MOVE, nodeC1, nodeC2, pos))
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
        elif operation == Common.UPDATEMOVE:

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
                        nodeC1 = json_ast_dump[Common.Pc.name][nodeC1]
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
                        nodeC2 = json_ast_dump[Common.Pc.name][nodeC2]
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
                    true_B2 = json_ast_dump[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeC2_l = map_ac[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = json_ast_dump[Common.Pc.name][nodeC2_l]
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
                                nodeA2_l = json_ast_dump[Common.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")

                if type(nodeC1) == ASTparser.AST:
                    if nodeC1.line == None:
                        nodeC1.line = nodeC1.parent.line
                    if type(nodeC2) == ASTparser.AST:
                        if nodeC2.line == None:
                            nodeC2.line = nodeD.parent.line
                        if nodeC2 in inserted_D:
                            instruction = get_instruction((Common.DELETE, nodeC1))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((Common.UPDATEMOVE, nodeC1, nodeC2, pos))
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
        elif operation == Common.INSERT:
            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeD1 = id_from_string(nodeB1)
                nodeD1 = json_ast_dump[Common.Pb.name][nodeD1]
                nodeD2 = id_from_string(nodeB2)
                nodeD2 = json_ast_dump[Common.Pb.name][nodeD2]
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
                        nodeD2 = json_ast_dump[Common.Pc.name][nodeD2]
                elif nodeB2 in match_BD.keys():
                    nodeD2 = match_BD[nodeB2]
                else:
                    Print.warning("Warning: node for insertion not" + \
                                  " found. Skipping INSERT operation.")

                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = json_ast_dump[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeD2_l = map_ac[nodeA2_l]
                                nodeD2_l = id_from_string(nodeD2_l)
                                nodeD2_l = json_ast_dump[Common.Pc.name][nodeD2_l]
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
                                nodeA2_l = json_ast_dump[Common.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1

                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")
                if type(nodeD1) == ASTparser.AST:
                    match_BD[nodeB1] = nodeD1
                    inserted_D.append(nodeD1)
                    nodeD1.children = []
                    if nodeD1.line == None:
                        nodeD1.line = nodeD1.parent.line
                    if type(nodeD2) == ASTparser.AST:
                        if nodeD2.line == None:
                            nodeD2.line = nodeD2.parent.line
                        if nodeD2 not in inserted_D:
                            instruction = get_instruction((Common.INSERT, nodeD1, nodeD2, pos))
                            translated_instruction_list.append(instruction)
            except Exception as e:
                err_exit(e, "Something went wrong with INSERT.")

    return translated_instruction_list


def transform_script_gumtree(modified_script, inserted_node_list, json_ast_dump, map_ab, map_ac):
    translated_instruction_list = list()
    inserted_D = list()
    match_BD = dict()
    for i in modified_script:
        operation = i[0]
        # Update nodeA to nodeB (value) -> Update nodeC to nodeD (value)
        if operation == Common.UPDATE:
            try:
                nodeA = i[1]
                nodeB = i[2]
                nodeC = "?"
                nodeD = id_from_string(nodeB)
                nodeD = json_ast_dump[Common.Pb.name][nodeD]

                if nodeA in map_ac.keys():
                    nodeC = map_ac[nodeA]
                    nodeC = id_from_string(nodeC)
                    nodeC = json_ast_dump[Common.Pc.name][nodeC]

                    if nodeC.line == None:
                        nodeC.line = nodeC.parent.line
                    instruction = get_instruction((Common.UPDATE, nodeC, nodeD))
                    translated_instruction_list.append(instruction)

                else:
                    Print.warning("Warning: Match for " + str(nodeA) + "not found. Skipping UPDATE instruction.")

            except Exception as e:
                err_exit(e, "Something went wrong with UPDATE.")

        # Delete nodeA -> Delete nodeC
        elif operation == Common.DELETE:
            try:
                nodeA = i[1]
                nodeC = "?"
                if nodeA in map_ac.keys():
                    nodeC = map_ac[nodeA]
                    nodeC = id_from_string(nodeC)
                    nodeC = json_ast_dump[Common.Pc.name][nodeC]
                    if nodeC.line == None:
                        nodeC.line = nodeC.parent.line
                    instruction = get_instruction((Common.DELETE, nodeC))
                    translated_instruction_list.append(instruction)
                else:
                    Print.warning("Warning: Match for " + str(nodeA) + \
                                  "not found. Skipping DELETE instruction.")
            except Exception as e:
                err_exit(e, "Something went wrong with DELETE.")
            # Move nodeA to nodeB at pos -> Move nodeC to nodeD at pos
        elif operation == Common.MOVE:
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
                        nodeC1 = json_ast_dump[Common.Pc.name][nodeC1]
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
                        nodeC2 = json_ast_dump[Common.Pc.name][nodeC2]
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
                    true_B2 = json_ast_dump[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeC2_l = map_ac[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = json_ast_dump[Common.Pc.name][nodeC2_l]
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
                                nodeA2_l = json_ast_dump[Common.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")

                if type(nodeC1) == ASTparser.AST:
                    if nodeC1.line == None:
                        nodeC1.line = nodeC1.parent.line
                    if type(nodeC2) == ASTparser.AST:
                        if nodeC2.line == None:
                            nodeC2.line = nodeC2.parent.line
                        if nodeC2 in inserted_D:
                            instruction = get_instruction((Common.DELETE, nodeC1))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((Common.MOVE, nodeC1, nodeC2, pos))
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
        elif operation == Common.UPDATEMOVE:

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
                        nodeC1 = json_ast_dump[Common.Pc.name][nodeC1]
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
                        nodeC2 = json_ast_dump[Common.Pc.name][nodeC2]
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
                    true_B2 = json_ast_dump[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeC2_l = map_ac[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = json_ast_dump[Common.Pc.name][nodeC2_l]
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
                                nodeA2_l = json_ast_dump[Common.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")

                if type(nodeC1) == ASTparser.AST:
                    if nodeC1.line == None:
                        nodeC1.line = nodeC1.parent.line
                    if type(nodeC2) == ASTparser.AST:
                        if nodeC2.line == None:
                            nodeC2.line = nodeC2.parent.line
                        if nodeC2 in inserted_D:
                            instruction = get_instruction((Common.DELETE, nodeC1))
                            translated_instruction_list.append(instruction)
                        else:
                            instruction = get_instruction((Common.UPDATEMOVE, nodeC1, nodeC2, pos))
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
        elif operation == Common.INSERT:
            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeD1 = id_from_string(nodeB1)
                nodeD1 = json_ast_dump[Common.Pb.name][nodeD1]
                nodeD2 = id_from_string(nodeB2)
                nodeD2 = json_ast_dump[Common.Pb.name][nodeD2]
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
                        nodeD2 = json_ast_dump[Common.Pc.name][nodeD2]
                elif nodeB2 in match_BD.keys():
                    nodeD2 = match_BD[nodeB2]
                else:
                    Print.warning("Warning: node for insertion not" + \
                                  " found. Skipping INSERT operation.")

                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = json_ast_dump[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in map_ab.keys():
                            nodeA2_l = map_ab[nodeB2_l]
                            if nodeA2_l in map_ac.keys():
                                nodeD2_l = map_ac[nodeA2_l]
                                nodeD2_l = id_from_string(nodeD2_l)
                                nodeD2_l = json_ast_dump[Common.Pc.name][nodeD2_l]
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
                                nodeA2_l = json_ast_dump[Common.Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1

                        else:
                            Print.warning("Failed at match for child.")
                except Exception as e:
                    err_exit(e, "Failed at locating pos.")
                if type(nodeD1) == ASTparser.AST:
                    match_BD[nodeB1] = nodeD1
                    inserted_D.append(nodeD1)
                    nodeD1.children = []
                    if nodeD1.line == None:
                        nodeD1.line = nodeD1.parent.line
                    if type(nodeD2) == ASTparser.AST:
                        if nodeD2.line == None:
                            nodeD2.line = nodeD2.parent.line
                        if nodeD2 not in inserted_D:
                            instruction = get_instruction((Common.INSERT, nodeD1, nodeD2, pos))
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
        if inst == Common.DELETE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[Common.Pa.name][nodeA]
            # Print.white("\t" + Common.DELETE + " - " + str(nodeA))
            modified_AB.append((Common.DELETE, nodeA))
        elif inst == Common.UPDATE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[Common.Pa.name][nodeA]
            nodeB = id_from_string(i[2])
            nodeB = ASTlists[Common.Pb.name][nodeB]
            # Print.white("\t" + Common.UPDATE + " - " + str(nodeA) + " - " + str(nodeB))
            modified_AB.append((Common.UPDATE, nodeA, nodeB))
        elif inst == Common.MOVE:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Common.Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Common.Pb.name][nodeB2]
            pos = i[3]
            # Print.white("\t" + Common.MOVE + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((Common.MOVE, nodeB1, nodeB2, pos))
            else:
                if i[1] in match_BA.keys():
                    nodeA = match_BA[i[1]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[Common.Pa.name][nodeA]
                    modified_AB.append((Common.DELETE, nodeA))
                else:
                    Print.warning("Warning: node " + str(nodeB1) + \
                                  "could not be matched. " + \
                                  "Skipping MOVE instruction...")
                    Print.warning(i)
        elif inst == Common.UPDATEMOVE:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Common.Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Common.Pb.name][nodeB2]
            pos = i[3]
            # Print.white("\t" + Common.UPDATEMOVE + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((Common.UPDATEMOVE, nodeB1, nodeB2, pos))
            else:
                if i[1] in match_BA.keys():
                    nodeA = match_BA[i[1]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[Common.Pa.name][nodeA]
                    modified_AB.append((Common.DELETE, nodeA))
                else:
                    Print.warning("Warning: node " + str(nodeB1) + \
                                  "could not be matched. " + \
                                  "Skipping MOVE instruction...")
                    Print.warning(i)
        elif inst == Common.INSERT:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Common.Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Common.Pb.name][nodeB2]
            pos = i[3]
            # Print.white("\t" + Common.INSERT + " - " + str(nodeB1) + " - " + str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((Common.INSERT, nodeB1, nodeB2, pos))
    return modified_AB


def remove_overlapping_delete(modified_AB):
    reduced_AB = set()
    n_i = len(modified_AB)
    for i in range(n_i):
        inst1 = modified_AB[i]
        if inst1[0] == Common.DELETE:
            for j in range(i + 1, n_i):
                inst2 = modified_AB[j]
                if inst2[0] == Common.DELETE:
                    node1 = inst1[1]
                    node2 = inst2[1]
                    if node1.contains(node2):
                        reduced_AB.add(j)
                    elif node2.contains(node1):
                        reduced_AB.add(i)
    modified_AB = [modified_AB[i] for i in range(n_i) if i not in reduced_AB]
    return modified_AB


def adjust_pos(modified_AB):
    i = 0
    while i < len(modified_AB) - 1:
        inst1 = modified_AB[i][0]
        if inst1 == Common.INSERT or inst1 == Common.MOVE or inst1 == Common.UPDATEMOVE:
            node_into_1 = modified_AB[i][2]
            k = i + 1
            for j in range(i + 1, len(modified_AB)):
                k = j
                inst2 = modified_AB[j][0]
                if inst2 != Common.INSERT and inst2 != Common.MOVE:
                    k -= 1
                    break
                node_into_2 = modified_AB[j][2]
                if node_into_1 != node_into_2:
                    k -= 1
                    break
                pos_at_1 = int(modified_AB[j - 1][3])
                pos_at_2 = int(modified_AB[j][3])
                if pos_at_1 < pos_at_2 - 1:
                    k -= 1
                    break
            k += 1
            for l in range(i, k):
                inst = modified_AB[l][0]
                node1 = modified_AB[l][1]
                node2 = modified_AB[l][2]
                pos = int(modified_AB[i][3])
                modified_AB[l] = (inst, node1, node2, pos)
            i = k
        else:
            i += 1
    return modified_AB


def rewrite_as_script(modified_AB):
    instruction_AB = []
    for i in modified_AB:
        inst = i[0]
        if inst == Common.DELETE:
            nodeA = i[1].simple_print()
            instruction_AB.append((Common.DELETE, nodeA))
        elif inst == Common.UPDATE:
            nodeA = i[1].simple_print()
            nodeB = i[2].simple_print()
            instruction_AB.append((Common.UPDATE, nodeA, nodeB))
        elif inst == Common.INSERT:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((Common.INSERT, nodeB1, nodeB2, pos))
        elif inst == Common.MOVE:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((Common.MOVE, nodeB1, nodeB2, pos))
        elif inst == Common.UPDATEMOVE:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((Common.UPDATEMOVE, nodeB1, nodeB2, pos))
    return instruction_AB


def get_instruction(instruction_data):
    operation = instruction_data[0]
    instruction = ""

    if operation == Common.UPDATE:
        nodeC = instruction_data[1]
        nodeD = instruction_data[2]
        instruction = Common.UPDATE + " " + nodeC.simple_print() + Common.TO + nodeD.simple_print()

    elif operation == Common.DELETE:
        nodeC = instruction_data[1]
        instruction = Common.DELETE + " " + nodeC.simple_print()

    elif operation == Common.MOVE:
        nodeD1 = instruction_data[1].simple_print()
        nodeD2 = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = Common.MOVE + " " + nodeD1 + Common.INTO + nodeD2 + Common.AT + pos

    elif operation == Common.INSERT:
        nodeB = instruction_data[1].simple_print()
        nodeC = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = Common.INSERT + " " + nodeB + Common.INTO + nodeC + Common.AT + pos

    elif operation == Common.UPDATEMOVE:
        nodeD1 = instruction_data[1].simple_print()
        nodeD2 = instruction_data[2].simple_print()
        pos = str(instruction_data[3])
        instruction = Common.UPDATEMOVE + " " + nodeD1 + Common.INTO + nodeD2 + Common.AT + pos

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
    for file_list, generated_data in Common.generated_script_for_header_files.items():
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
        variable_map = Common.variable_map[file_list]
        translated_script = transform_script_gumtree(modified_script, generated_data[1], json_ast_dump, generated_data[2],
                                             variable_map)
        translated_script_list[file_list] = (translated_script, original_script)

    Print.sub_title("Translating scripts for C files")
    for file_list, generated_data in Common.generated_script_for_c_files.items():
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
        # modified_AB = adjust_pos(modified_AB)
        # Printing modified simplified script
        # Print.success("\tModified Script:")
        # for j in [" - ".join([str(k) for k in i]) for i in modified_script]:
        #     Print.success("\t" + j)
        # We rewrite the instruction as a script (str) instead of nodes
        modified_script = rewrite_as_script(modified_script)
        # We get the matching nodes from Pa to Pc into a dict
        variable_map = Common.variable_map[file_list]
        translated_script = transform_script_gumtree(modified_script, generated_data[1], json_ast_dump,
                                                     generated_data[2], variable_map)
        translated_script_list[file_list] = (translated_script, original_script)

    Common.translated_script_for_files = translated_script_list
