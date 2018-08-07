#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time
import Common
from Utils import exec_com, err_exit, find_files, clean, get_extensions
import Project
import Print
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
                    err_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return node_map


def generate_script_for_header_files(files_list_to_patch):
    generated_script_list = dict()
    for (file_a, file_c, var_map) in files_list_to_patch:
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
        generated_data = (original_script, inserted_node_list, json_ast_dump, map_ab, map_ac)
        generated_script_list[(file_a, file_b, file_c)] = generated_data
    Common.generated_script_for_header_files = generated_script_list


def generate_script_for_c_files(file_list_to_patch):
    generated_script_list = dict()
    for (vec_f_a, vec_f_c, var_map) in file_list_to_patch:
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
        generated_data = (original_script, inserted_node_list, json_ast_dump, map_ab, map_ac)
        generated_script_list[(vec_f_a, vec_f_b, vec_f_c)] = generated_data
    Common.generated_script_for_c_files = generated_script_list



def restore_files():
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


def extract():
    Print.title("Generating GumTree script for patch")
    # Using all previous structures to transplant patch
    safe_exec(generate_script_for_header_files, "generating script for header files", Common.header_file_list_to_patch)
    safe_exec(generate_script_for_c_files, "generating script for C files", Common.c_file_list_to_patch)

