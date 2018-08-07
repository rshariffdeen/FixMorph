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


def getId(NodeRef):
    return int(NodeRef.split("(")[-1][:-1])


def getType(NodeRef):
    return NodeRef.split("(")[0]


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


def clean_parse(content, separator):
    if content.count(separator) == 1:
        return content.split(separator)
    i = 0
    while i < len(content):
        if content[i] == "\"":
            i += 1
            while i < len(content) - 1:
                if content[i] == "\\":
                    i += 2
                elif content[i] == "\"":
                    i += 1
                    break
                else:
                    i += 1
            prefix = content[:i]
            rest = content[i:].split(separator)
            node1 = prefix + rest[0]
            node2 = separator.join(rest[1:])
            return [node1, node2]
        i += 1
    # If all the above fails (it shouldn't), hope for some luck:
    nodes = content.split(separator)
    half = len(nodes) // 2
    node1 = separator.join(nodes[:half])
    node2 = separator.join(nodes[half:])
    return [node1, node2]


def ASTscript(file1, file2, output, only_matches=False):
    extra_arg = ""
    if file1[-2:] == ".h":
        extra_arg = " --"
    c = Common.DIFF_COMMAND + " -s=" + Common.DIFF_SIZE + " -dump-matches " + \
        file1 + " " + file2 + extra_arg + " 2> output/errors_clang_diff "
    if only_matches:
        c += "| grep '^Match ' "
    c += " > " + output
    exec_com(c, True)


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


def patch_instruction(inst):
    instruction = inst[0]
    c = ""

    if instruction == Common.UPDATE:
        nodeC = inst[1]
        nodeD = inst[2]
        c = Common.UPDATE + " " + nodeC.simple_print() + Common.TO + nodeD.simple_print()

    elif instruction == Common.DELETE:
        nodeC = inst[1]
        c = Common.DELETE + " " + nodeC.simple_print()

    elif instruction == Common.MOVE:
        nodeD1 = inst[1].simple_print()
        nodeD2 = inst[2].simple_print()
        pos = str(inst[3])
        c = Common.MOVE + " " + nodeD1 + Common.INTO + nodeD2 + Common.AT + pos

    elif instruction == Common.INSERT:
        nodeB = inst[1].simple_print()
        nodeC = inst[2].simple_print()
        pos = str(inst[3])
        c = Common.INSERT + " " + nodeB + Common.INTO + nodeC + Common.AT + pos

    c = "\t\t" + c
    Print.success(c)
    script_path = "output/script"
    if not (os.path.isfile(script_path)):
        with open(script_path, 'w') as script:
            script.write(c)
    else:
        with open(script_path, 'a') as script:
            script.write("\n" + c)


def gen_edit_script(file_a, file_b, output):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Print.blue("Generating edit script: " + name_a + Common.TO + name_b + "...")
    try:
        ASTscript(file_a, file_b, "output/" + output)
    except Exception as e:
        err_exit(e, "Unexpected fail at generating edit script: " + output)


def get_instructions():
    instruction_AB = list()
    inserted_B = list()
    match_BA = dict()
    with open('output/diff_script_AB', 'r', errors='replace') as script_AB:
        line = script_AB.readline().strip()
        while line:
            line = line.split(" ")
            # Special case: Update and Move nodeA into nodeB2
            if len(line) > 3 and line[0] == Common.UPDATE and line[1] == Common.AND and \
                    line[2] == Common.MOVE:
                instruction = Common.UPDATEMOVE
                content = " ".join(line[3:])

            else:
                instruction = line[0]
                content = " ".join(line[1:])
            # Match nodeA to nodeB
            if instruction == Common.MATCH:
                try:
                    nodeA, nodeB = clean_parse(content, Common.TO)
                    match_BA[nodeB] = nodeA
                except Exception as e:
                    err_exit(e, "Something went wrong in MATCH (AB).",
                             line, instruction, content)
            # Update nodeA to nodeB (only care about value)
            elif instruction == Common.UPDATE:
                try:
                    nodeA, nodeB = clean_parse(content, Common.TO)
                    instruction_AB.append((instruction, nodeA, nodeB))
                except Exception as e:
                    err_exit(e, "Something went wrong in UPDATE.")
            # Delete nodeA
            elif instruction == Common.DELETE:
                try:
                    nodeA = content
                    instruction_AB.append((instruction, nodeA))
                except Exception as e:
                    err_exit(e, "Something went wrong in DELETE.")
            # Move nodeA into nodeB at pos
            elif instruction == Common.MOVE:
                try:
                    nodeA, nodeB = clean_parse(content, Common.INTO)
                    nodeB_at = nodeB.split(Common.AT)
                    nodeB = Common.AT.join(nodeB_at[:-1])
                    pos = nodeB_at[-1]
                    instruction_AB.append((instruction, nodeA, nodeB, pos))
                except Exception as e:
                    err_exit(e, "Something went wrong in MOVE.")
            # Update nodeA into matching node in B and move into nodeB at pos
            elif instruction == Common.UPDATEMOVE:
                try:
                    nodeA, nodeB = clean_parse(content, Common.INTO)
                    nodeB_at = nodeB.split(Common.AT)
                    nodeB = Common.AT.join(nodeB_at[:-1])
                    pos = nodeB_at[-1]
                    instruction_AB.append((instruction, nodeA, nodeB, pos))
                except Exception as e:
                    err_exit(e, "Something went wrong in MOVE.")
                    # Insert nodeB1 into nodeB2 at pos
            elif instruction == Common.INSERT:
                try:
                    nodeB1, nodeB2 = clean_parse(content, Common.INTO)
                    nodeB2_at = nodeB2.split(Common.AT)
                    nodeB2 = Common.AT.join(nodeB2_at[:-1])
                    pos = nodeB2_at[-1]
                    instruction_AB.append((instruction, nodeB1, nodeB2,
                                           pos))
                    inserted_B.append(nodeB1)
                except Exception as e:
                    err_exit(e, "Something went wrong in INSERT.")
            line = script_AB.readline().strip()
    return instruction_AB, inserted_B, match_BA


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


def simplify_patch(instruction_AB, match_BA, ASTlists):
    modified_AB = []
    inserted = []
    Print.white("Original script from Pa to Pb")
    for i in instruction_AB:
        inst = i[0]
        if inst == Common.DELETE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[Common.Pa.name][nodeA]
            Print.white("\t" + Common.DELETE + " - " + str(nodeA))
            modified_AB.append((Common.DELETE, nodeA))
        elif inst == Common.UPDATE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[Common.Pa.name][nodeA]
            nodeB = id_from_string(i[2])
            nodeB = ASTlists[Common.Pb.name][nodeB]
            Print.white("\t" + Common.UPDATE + " - " + str(nodeA) + " - " + \
                        str(nodeB))
            modified_AB.append((Common.UPDATE, nodeA, nodeB))
        elif inst == Common.MOVE:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Common.Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Common.Pb.name][nodeB2]
            pos = i[3]
            Print.white("\t" + Common.MOVE + " - " + str(nodeB1) + " - " + \
                        str(nodeB2) + " - " + str(pos))
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
            Print.white("\t" + Common.UPDATEMOVE + " - " + str(nodeB1) + " - " + \
                        str(nodeB2) + " - " + str(pos))
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
            Print.white("\t" + Common.INSERT + " - " + str(nodeB1) + " - " + \
                        str(nodeB2) + " - " + str(pos))
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


def get_mapping():
    node_map = dict()
    map_file_name = "output/diff_script_AC"
    with open(map_file_name, 'r', errors='replace') as ast_map:
        line = ast_map.readline().strip()
        while line:
            line = line.split(" ")
            operation = line[0]
            content = " ".join(line[1:])
            if operation == Common.MATCH:
                try:
                    node_a, node_c = clean_parse(content, Common.TO)
                    node_map[node_a] = node_c
                except Exception as exception:
                    err_exit(e, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return node_map


# node list is from the patched program
def get_candidate_node_list(node_ref, json_ast_dump):
    candidate_node_list = list()
    node_id = getId(node_ref)
    node_type = getType(node_ref)
    node = json_ast_dump[Pc.name][node_id]
    print(Pc.name)
    print(node)

    if nodeA in match_AC.keys():
        nodeC = match_AC[nodeA]
        nodeC = id_from_string(nodeC)
        nodeC = ASTlists[Pc.name][nodeC]

    return candidate_node_list


def transform_script(generated_data):
    instruction_AB = generated_data[0]
    inserted_B = generated_data[1]
    ASTlists = generated_data[2]
    match_AC = generated_data[3]
    match_BA = generated_data[4]
    instruction_CD = list()
    inserted_D = list()
    match_BD = dict()
    for i in instruction_AB:
        instruction = i[0]
        # Update nodeA to nodeB (value) -> Update nodeC to nodeD (value)
        if instruction == Common.UPDATE:
            try:
                nodeA = i[1]
                nodeB = i[2]
                nodeC = "?"
                nodeD = id_from_string(nodeB)
                nodeD = ASTlists[Common.Pb.name][nodeD]
                nodeC = get_candidate_node_list(nodeA, ASTlists)
                if nodeC == null:
                    Print.warning("Warning: Match for " + str(nodeA) + "not found. Skipping UPDATE instruction.")
                else:
                    nodeC.line = nodeC.parent.line
                    instruction_CD.append((Common.UPDATE, nodeC, nodeD))

            except Exception as e:
                err_exit(e, "Something went wrong with UPDATE.")

        # Delete nodeA -> Delete nodeC
        elif instruction == Common.DELETE:
            try:
                nodeA = i[1]
                nodeC = "?"
                if nodeA in match_AC.keys():
                    nodeC = match_AC[nodeA]
                    nodeC = id_from_string(nodeC)
                    nodeC = ASTlists[Common.Pc.name][nodeC]
                    if nodeC.line == None:
                        nodeC.line = nodeC.parent.line
                    instruction_CD.append((Common.DELETE, nodeC))
                else:
                    Print.warning("Warning: Match for " + str(nodeA) + \
                                  "not found. Skipping DELETE instruction.")
            except Exception as e:
                err_exit(e, "Something went wrong with DELETE.")
        # Move nodeA to nodeB at pos -> Move nodeC to nodeD at pos
        elif instruction == Common.MOVE:
            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeC1 = "?"
                nodeC2 = "?"
                if nodeB1 in match_BA.keys():
                    nodeA1 = match_BA[nodeB1]
                    if nodeA1 in match_AC.keys():
                        nodeC1 = match_AC[nodeA1]
                        nodeC1 = id_from_string(nodeC1)
                        nodeC1 = ASTlists[Common.Pc.name][nodeC1]
                    else:
                        # TODO: Manage case in which nodeA1 is unmatched
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(nodeA1)
                elif nodeB1 in inserted_B:
                    if nodeB1 in match_BD.keys():
                        nodeC1 = match_BD[nodeB1]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(nodeB1)
                if nodeB2 in match_BA.keys():
                    nodeA2 = match_BA[nodeB2]
                    if nodeA2 in match_AC.keys():
                        nodeC2 = match_AC[nodeA2]
                        nodeC2 = id_from_string(nodeC2)
                        nodeC2 = ASTlists[Common.Pc.name][nodeC2]
                    else:
                        # TODO: Manage case for unmatched nodeA2
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(nodeA2)
                elif nodeB2 in inserted_B:
                    if nodeB2 in match_BD.keys():
                        nodeC2 = match_BD[nodeB2]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(nodeB2)
                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = ASTlists[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in match_BA.keys():
                            nodeA2_l = match_BA[nodeB2_l]
                            if nodeA2_l in match_AC.keys():
                                nodeC2_l = match_AC[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = ASTlists[Common.Pc.name][nodeC2_l]
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
                                nodeA2_l = ASTlists[Common.Pa.name][nodeA2_l]
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
                            instruction_CD.append((Common.DELETE, nodeC1))
                        else:
                            instruction_CD.append((Common.MOVE, nodeC1, nodeC2,
                                                   pos))
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
        elif instruction == Common.UPDATEMOVE:

            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeC1 = "?"
                nodeC2 = "?"
                if nodeB1 in match_BA.keys():
                    nodeA1 = match_BA[nodeB1]
                    if nodeA1 in match_AC.keys():
                        nodeC1 = match_AC[nodeA1]
                        nodeC1 = id_from_string(nodeC1)
                        nodeC1 = ASTlists[Common.Pc.name][nodeC1]
                    else:
                        # TODO: Manage case in which nodeA1 is unmatched
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(nodeA1)
                elif nodeB1 in inserted_B:
                    if nodeB1 in match_BD.keys():
                        nodeC1 = match_BD[nodeB1]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(nodeB1)
                if nodeB2 in match_BA.keys():
                    nodeA2 = match_BA[nodeB2]
                    if nodeA2 in match_AC.keys():
                        nodeC2 = match_AC[nodeA2]
                        nodeC2 = id_from_string(nodeC2)
                        nodeC2 = ASTlists[Common.Pc.name][nodeC2]
                    else:
                        # TODO: Manage case for unmatched nodeA2
                        Print.warning("Node in Pa not found in Pc: (1)")
                        Print.warning(nodeA2)
                elif nodeB2 in inserted_B:
                    if nodeB2 in match_BD.keys():
                        nodeC2 = match_BD[nodeB2]
                    else:
                        # TODO: Manage case for node not found
                        Print.warning("Node to be moved was not found. (2)")
                        Print.warning(nodeB2)
                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = ASTlists[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in match_BA.keys():
                            nodeA2_l = match_BA[nodeB2_l]
                            if nodeA2_l in match_AC.keys():
                                nodeC2_l = match_AC[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = ASTlists[Common.Pc.name][nodeC2_l]
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
                                nodeA2_l = ASTlists[Common.Pa.name][nodeA2_l]
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
                            instruction_CD.append((Common.DELETE, nodeC1))
                        else:
                            instruction_CD.append((Common.UPDATEMOVE, nodeC1, nodeC2,
                                                   pos))
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
        elif instruction == Common.INSERT:
            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeD1 = id_from_string(nodeB1)
                nodeD1 = ASTlists[Common.Pb.name][nodeD1]
                nodeD2 = id_from_string(nodeB2)
                nodeD2 = ASTlists[Common.Pb.name][nodeD2]
                # TODO: Is this correct?
                if nodeD2.line != None:
                    nodeD1.line = nodeD2.line
                else:
                    nodeD1.line = nodeD2.parent.line
                if nodeB2 in match_BA.keys():
                    nodeA2 = match_BA[nodeB2]
                    if nodeA2 in match_AC.keys():
                        nodeD2 = match_AC[nodeA2]
                        nodeD2 = id_from_string(nodeD2)
                        nodeD2 = ASTlists[Common.Pc.name][nodeD2]
                elif nodeB2 in match_BD.keys():
                    nodeD2 = match_BD[nodeB2]
                else:
                    Print.warning("Warning: node for insertion not" + \
                                  " found. Skipping INSERT operation.")

                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = ASTlists[Common.Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos - 1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in match_BA.keys():
                            nodeA2_l = match_BA[nodeB2_l]
                            if nodeA2_l in match_AC.keys():
                                nodeD2_l = match_AC[nodeA2_l]
                                nodeD2_l = id_from_string(nodeD2_l)
                                nodeD2_l = ASTlists[Common.Pc.name][nodeD2_l]
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
                                nodeA2_l = ASTlists[Common.Pa.name][nodeA2_l]
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
                            instruction_CD.append((Common.INSERT, nodeD1, nodeD2,
                                                   pos))
            except Exception as e:
                err_exit(e, "Something went wrong with INSERT.")
    return instruction_CD


def generate_script_for_header_files(to_patch):
    for (file_a, file_c, var_map) in to_patch:
        file_b = file_a.replace(Common.Pa.path, Common.Pb.path)
        if not os.path.isfile(file_b):
            err_exit("Error: File not found.", file_b)

        # Generate edit scripts for diff and matching
        gen_edit_script(file_a, file_b, "diff_script_AB")
        gen_edit_script(file_a, file_c, "diff_script_AC")

        Print.blue("Generating final edit script for " + file_c.split("/")[-1])
        # Write patch properly
        original_script, inserted_node_list, map_ab = get_instructions()
        # Generate AST as json files
        json_ast_dump = gen_temp_json(file_a, file_b, file_c)
        # Simplify instructions to a smaller representative sequence of them
        modified_script = simplify_patch(original_script, map_ab, json_ast_dump)
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
        original_script = rewrite_as_script(modified_script)
        # We get the matching nodes from Pa to Pc into a dict
        map_ac = get_mapping()
        # Transform instructions into ones pertinent to Pc nodes
        translated_script = transform_script(original_script, inserted_node_list, json_ast_dump, map_ac, map_ab)
        # Write patch script properly and print in on console
        Print.success("\tTranslated script from Pc to Pd")
        for i in translated_script:
            patch_instruction(i)
        # Apply the patch (it runs with the script)
        apply_patch(file_a, file_b, file_c)


def generate_script_for_c_files(to_patch):
    for (vec_f_a, vec_f_c, var_map) in to_patch:
        try:
            vec_f_b_file = vec_f_a.file.replace(Common.Pa.path, Common.Pb.path)
            if vec_f_b_file not in Common.Pb.functions.keys():
                err_exit("Error: File not found among affected.", vec_f_b_file)
            if vec_f_a.function in Common.Pb.functions[vec_f_b_file].keys():
                vec_f_b = Common.Pb.functions[vec_f_b_file][vec_f_a.function]
            else:
                err_exit("Error: Function not found among affected.", vec_f_a.function, vec_f_b_file,
                         Common.Pb.functions[vec_f_b_file].keys())
        except Exception as e:
            err_exit(e, vec_f_b_file, vec_f_a, Common.Pa.path, Common.Pb.path, vec_f_a.function)

        # Generate edit scripts for diff and matching
        gen_edit_script(vec_f_a.file, vec_f_b.file, "diff_script_AB")
        gen_edit_script(vec_f_a.file, vec_f_c.file, "diff_script_AC")

        Print.blue("Generating final edit script for " + Common.Pc.name)
        # Write patch properly
        original_script, inserted_node_list, map_ab = get_instructions()
        # Generate AST as json files
        json_ast_dump = gen_temp_json(vec_f_a.file, vec_f_b.file, vec_f_c.file)
        # Simplify instructions to a smaller representative sequence of them
        modified_script = simplify_patch(original_script, map_ab, json_ast_dump)
        # Sort in reverse order and depending on instruction for application
        modified_script.sort(key=cmp_to_key(order_comp))
        # Delete overlapping DELETE operations
        # modified_AB = remove_overlapping_delete(modified_AB)
        # Adjusting position for MOVE and INSERT operations
        # modified_AB = adjust_pos(modified_AB)
        # Printing modified simplified script
        Print.success("Modified simplified script:")
        for j in [" - ".join([str(k) for k in i]) for i in modified_script]:
            Print.success("\t" + j)
        # We rewrite the instruction as a script (str) instead of nodes
        original_script = rewrite_as_script(modified_script)
        # We get the matching nodes from Pa to Pc into a dict
        map_ac = get_mapping()
        # Transform instructions into ones pertinent to Pc nodes
        translated_script = transform_script(original_script, inserted_node_list, json_ast_dump, map_ac, map_ab)
        # Write patch script properly and print in on console
        Print.success("\tTranslated script from Pc to Pd")
        for i in translated_script:
            patch_instruction(i)
        # Apply the patch (it runs with the script)
        apply_patch(vec_f_a.file, vec_f_b.file, vec_f_c.file)


def apply_patch(file_a, file_b, file_c):
    global changes, n_changes
    # This is to have an id of the file we're patching
    n_changes += 1
    # Check for an edit script
    if not (os.path.isfile("output/script")):
        err_exit("No script was generated. Exiting with error.")

    output_file = "output/" + str(n_changes) + "_temp." + file_c[-1]
    c = ""
    # We add file_c into our dict (changes) to be able to backup and copy it
    if file_c not in changes.keys():
        filename = file_c.split("/")[-1]
        backup_file = str(n_changes) + "_" + filename
        changes[file_c] = backup_file
        c += "cp " + file_c + " Backup_Folder/" + backup_file + "; "
    # We apply the patch using the script and crochet-patch
    c += Common.PATCH_COMMAND + " -s=" + Common.PATCH_SIZE + \
         " -script=output/script -source=" + file_a + \
         " -destination=" + file_b + " -target=" + file_c
    if file_c[-1] == "h":
        c += " --"
    c += " 2> output/errors > " + output_file + "; "
    c += "cp " + output_file + " " + file_c
    exec_com(c)
    # We fix basic syntax errors that could have been introduced by the patch
    c2 = Common.SYNTAX_CHECK_COMMAND + "-fixit " + file_c
    if file_c[-1] == "h":
        c2 += " --"
    c2 += " 2> output/syntax_errors"
    exec_com(c2)
    # We check that everything went fine, otherwise, we restore everything
    try:
        c3 = Common.Common.SYNTAX_CHECK_COMMAND + file_c
        if file_c[-1] == "h":
            c3 += " --"
        exec_com(c3)
    except Exception as e:
        Print.error("Clang-check could not repair syntax errors.")
        restore_files()
        err_exit(e, "Crochet failed.")
    # We format the file to be with proper spacing (needed?)
    c4 = Common.STYLE_FORMAT_COMMAND + file_c
    if file_c[-1] == "h":
        c4 += " --"
    c4 += " > " + output_file + "; "
    c4 += "cp " + output_file + " " + file_c + ";"
    exec_com(c4)

    # We rename the script so that it won't be there for other files
    c5 = "mv output/script output/" + str(n_changes) + "_script"
    show_patch(file_a, file_b, file_c, output_file, str(n_changes))
    exec_com(c5)


def restore_files():
    global changes
    Print.warning("Restoring files...")
    for file in changes.keys():
        backup_file = changes[file]
        c = "cp Backup_Folder/" + backup_file + " " + file
        exec_com(c)
    Print.warning("Files restored")


def show_patch(file_a, file_b, file_c, file_d, index):
    Print.warning("Original Patch")
    original_patch_file_name = "output/" + index + "-original-patch"
    generated_patch_file_name = "output/" + index + "-generated-patch"
    diff_command = "diff -ENZBbwr " + file_a + " " + file_b + " > " + original_patch_file_name
    exec_com(diff_command)
    with open(original_patch_file_name, 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Print.white("\t" + diff_line)
            diff_line = diff.readline().strip()

    Print.warning("Generated Patch")
    diff_command = "diff -ENZBbwr " + file_c + " " + file_d + " > " + generated_patch_file_name
    exec_com(diff_command)
    with open(generated_patch_file_name, 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Print.success("\t" + diff_line)
            diff_line = diff.readline().strip()


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


def weave():

    Print.title("Applying transformation")
    file_index = 0
    for file_list, generated_data in Common.translated_script_for_files:
        Print.sub_title("Translating file " + file_list[2])
        Print.blue("Original AST script")
        original_script = generated_data[1]
        for i in original_script:
            patch_instruction(i)
        Print.blue("Generated AST script")
        translated_script = generated_data[0]
        for i in translated_script:
            patch_instruction(i)
        apply_patch(file_list[0], file_list[1], file_list[2])
        Print.success("\tSuccessful transformation")
        show_patch(file_list[0], file_list[1], file_list[2], file_index)
        file_index += 1
