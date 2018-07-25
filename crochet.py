#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time
from Utils import exec_com, err_exit, find_files, clean, get_extensions
import Project
import Print
import ASTVector
import ASTgen
import ASTparser


Pa = None
Pb = None
Pc = None
crash = None

crochet_patch = "crochet-patch "
crochet_diff = "crochet-diff "
clang_check = "clang-check "
clang_format = "clang-format -style=LLVM "
interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

UPDATE = "Update"
MOVE = "Move"
INSERT = "Insert"
DELETE = "Delete"
MATCH = "Match"
TO = " to "
AT = " at "
INTO = " into "
AND = "and"
order = [UPDATE, DELETE, MOVE, INSERT]

changes = dict()
n_changes = 0


def initialize():
    global Pa, Pb, Pc, crash
    with open('crochet.conf', 'r', errors='replace') as file:
        args = [i.strip() for i in file.readlines()]
    if (len(args) < 3):
        err_exit("Insufficient arguments: Pa, Pb, and Pc source paths " + \
                 "required.")
    Pa = Project.Project(args[0], "Pa")
    Pb = Project.Project(args[1], "Pb")
    Pc = Project.Project(args[2], "Pc")
    if len(args) >= 4:
        if os.path.isfile(args[3]):
            if len(args[3]) >= 4 and args[3][:-3] == ".sh":
                crash = args[3]
            else:
                Print.yellow("Script must be path to a shell (.sh) file." + \
                             "Running anyway.")
        else:
            Print.yellow("No script for crash provided. Running anyway.")
    else:
            Print.yellow("No script for crash provided. Running anyway.")
    clean()


def find_diff_files():
    global Pa, Pb
    extensions = get_extensions(Pa.path, "output/files1")
    extensions = extensions.union(get_extensions(Pb.path, "output/files2"))
    with open('output/exclude_pats', 'w', errors='replace') as exclusions:
        for pattern in extensions:
            exclusions.write(pattern + "\n")
    c = "diff -ENBbwqr " + Pa.path + " " + Pb.path + \
        " -X output/exclude_pats | grep -P '\.c and ' > output/diff"
    exec_com(c, False)

    
def gen_diff():
    # TODO: Include cases where a file is added or removed
    global Pa, Pb
    nums = "0123456789"
    Print.blue("Finding differing files...")
    find_diff_files()
    
    Print.blue("Starting fine-grained diff...\n")
    with open('output/diff', 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            diff_line = diff_line.split(" ")
            file_a = diff_line[1]
            file_b = diff_line[3]
            c = "diff -ENBbwr " + file_a + " " + file_b + " > output/file_diff"
            exec_com(c, False)
            pertinent_lines = []
            pertinent_lines_b = []
            with open('output/file_diff', 'r', errors='replace') as file_diff:
                file_line = file_diff.readline().strip()
                while file_line:
                    # In file_diff, line starts with a number, <, >, or -.
                    if file_line[0] in nums:
                        # change (delete + add)
                        if 'c' in file_line:
                            l = file_line.split('c')
                        elif 'd' in file_line:
                            l = file_line.split('d')
                        elif 'a' in file_line:
                            l = file_line.split('a')
                        # range for file_a
                        a = l[0].split(',')
                        start_a = int(a[0])
                        end_a = int(a[-1])
                        # range for file_b
                        b = l[1].split(',')
                        start_b = int(b[0])
                        end_b = int(b[-1])
                        # Pertinent lines in file_a
                        pertinent_lines.append((start_a, end_a))
                        pertinent_lines_b.append((start_b, end_b))
                    file_line = file_diff.readline().strip()
            try:
                Print.blue("\tProject Pa...")
                ASTgen.find_affected_funcs(Pa, file_a, pertinent_lines)
                Print.blue("")
                Print.blue("\tProject Pb...")
                ASTgen.find_affected_funcs(Pb, file_b, pertinent_lines_b)
            except Exception as e:
                err_exit(e, "HERE")
                        
            diff_line = diff.readline().strip()
    
    
def gen_ASTs():
    # Generates an AST file for each .c file
    find_files(Pc.path, "*.c", "output/Cfiles")
    with open("output/Cfiles", 'r', errors='replace') as files:
        file = files.readline().strip()
        while file:
            # Parses it to remove useless information (for us) and gen vects
            try:
                ASTgen.parseAST(file, Pc)
            except Exception as e:
                err_exit(e, "Unexpected error in parseAST with file:", file)
            file = files.readline().strip()

    
def get_vector_list(proj):
    Print.blue("Getting vectors for " + proj.name + "...")
    filepath = "output/vectors_" + proj.name
    find_files(proj.path, "*.vec",  filepath)
    with open(filepath, "r", errors='replace') as file:
        files = [vec.strip() for vec in file.readlines()]
    vecs = []
    for i in range(len(files)):
        with open(files[i], 'r', errors='replace') as vec:
            fl = vec.readline()
            if fl:
                v = [int(s) for s in vec.readline().strip().split(" ")]
                v = ASTVector.ASTVector.normed(v)
                vecs.append((files[i],v))
    return vecs
                
    
def compare():
    global Pa, Pc
    vecs_A = get_vector_list(Pa)
    vecs_C = get_vector_list(Pc)
    
    Print.blue("Variable mapping...\n")
    to_patch = []
    
    UNKNOWN = "#UNKNOWN#"
    factor = 2
    
    for i in vecs_A:
        best = vecs_C[0]
        best_d = ASTVector.ASTVector.dist(i[1], best[1])
        dist = dict()
        
        # Get best match candidate
        for j in vecs_C:
            d = ASTVector.ASTVector.dist(i[1],j[1])
            dist[j[0]] = d
            if d < best_d:
                best = j
                best_d = d
        
        # Get all pertinent matches (at d < factor*best_d) (with factor=2?)
        candidates = [best]
        candidates_d = [best_d]
        for j in vecs_C:
            if j != best:
                d = dist[j[0]]
                if d <= factor*best_d:
                    candidates.append(j)
                    candidates_d.append(d)
                
        count_unknown = [0 for i in candidates]
        count_vars = [0 for i in candidates]
        var_maps = []
        
        # We go up to -4 to remove the ".vec" part [filepath.function.vec]
        fa = i[0].replace(Pa.path, "")[:-4].split(".")
        f_a = fa[-1]
        file_a = ".".join(fa[:-1])
        
        # TODO: Correct once I have appropriate only function comparison
        for k in range(len(candidates)):
            candidate = candidates[k]
            fc = candidate[0].replace(Pc.path, "")[:-4].split(".")
            f_c = fc[-1]
            file_c = ".".join(fc[:-1])
            d_c = str(candidates_d[k])
            Print.blue("\tPossible match for " + f_a + " in $Pa/" + file_a + \
                       ":")
            Print.blue("\t\tFunction: " + f_c + " in $Pc/" + file_c)
            Print.blue("\t\tDistance: " + d_c + "\n")
            Print.blue("\tVariable mapping from " + f_a + " to " + f_c + ":")
            try:
                var_map = detect_matching_variables(f_a, file_a, f_c, file_c)
                var_maps.append(var_map)
            except Exception as e:
                err_exit(e, "Unexpected error while matching variables.")
            with open('output/var-map', 'r', errors='replace') as mapped:
                mapping = mapped.readline().strip()
                while mapping:
                    Print.grey("\t\t" + mapping)
                    if UNKNOWN in mapping:
                        count_unknown[k] += 1
                    count_vars[k] += 1
                    mapping = mapped.readline().strip()
        
        best_count = count_unknown[0]
        best = candidates[0]
        best_d = candidates_d[0]
        best_prop = 1
        var_map = var_maps[0]
        for k in range(1, len(count_unknown)):
            if count_vars[k] > 0:
                if count_unknown[k] < best_count:
                    best_count = count_unknown[k]
                    best = candidates[k]
                    best_d = candidates_d[k]
                    best_prop = count_unknown[k]/count_vars[k]
                    var_map = var_maps[k]
                elif count_unknown[k] == best_count:
                    prop = count_unknown[k]/count_vars[k]
                    if prop < best_prop:
                        best = candidates[k]
                        best_d = candidates_d[k]
                        best_prop = prop
                        var_map = var_maps[k]
                    elif prop == best_prop:
                        if candidates_d[k] <= best_d:
                            best = candidates[k]
                            best_d = candidates_d[k]
                            var_map = var_maps[k]
        
        fc = best[0].replace(Pc.path, "")[:-4].split(".")
        f_c = fc[-1]
        file_c = ".".join(fc[:-1])
        d_c = str(best_d)
        Print.green("\t\tBest match for " + f_a + " in $Pa/" + file_a + ":")
        Print.blue("\t\tFunction: " + f_c + " in $Pc/" + file_c)
        Print.blue("\t\tDistance: " + d_c + "\n")
                
        to_patch.append((Pa.funcs[Pa.path + file_a][f_a],
                         Pc.funcs[Pc.path + file_c][f_c], var_map))
    return to_patch
    
    
def generate_ast_map(source_a, source_b):
                   
    c = crochet_diff + "-dump-matches " + source_a + " " + \
        source_b + " 2>> output/errors_clang_diff " \
        "| grep -P '^Match (" + "|".join(interesting) + ")\(' " + \
        "| grep '^Match ' > output/ast-map"
    try:
        exec_com(c, True)   
    except Exception as e:
        err_exit(e, "Unexpected error in generate_ast_map.")


def detect_matching_variables(f_a, file_a, f_c, file_c):
    
    try:
        generate_ast_map(Pa.path + "/" + file_a, Pc.path + "/" + file_c)
    except Exception as e:
        err_exit(e, "Error at generate_ast_map.")
    
    #Print.yellow(Pa.funcs)
    function_a = Pa.funcs[Pa.path + file_a][f_a]
    #Print.yellow(function_a)
    variable_list_a = function_a.variables + function_a.params
    while '' in variable_list_a:
        variable_list_a.remove('')
        
    #Print.white(variable_list_a)
    
    a_names = [i.split(" ")[-1] for i in variable_list_a]
        
    function_c = Pc.funcs[Pc.path + file_c][f_c]
    variable_list_c = function_c.variables + function_c.params
    while '' in variable_list_c:
        variable_list_c.remove('')
    
    #Print.white(variable_list_c)
    
    json_file_A = Pa.path + "/" + file_a + ".ASTalt"
    ast_A = ASTparser.AST_from_file(json_file_A)
    json_file_C = Pc.path + "/" + file_c + ".ASTalt"
    ast_C = ASTparser.AST_from_file(json_file_C)
    
    ast_map = dict()
    try:
        with open("output/ast-map", "r", errors='replace') as ast_map_file:
            map_line = ast_map_file.readline().strip()
            while map_line:
                nodeA, nodeB = clean_parse(map_line, " to ")
                
                var_a = nodeA.split("(")[1][:-1]
                var_a = ast_A[int(var_a)].value_calc(Pa.path + "/" + file_a)
                
                var_c = nodeB.split("(")[1][:-1]
                var_c = ast_C[int(var_c)].value_calc(Pc.path + "/" + file_c)
                
                if var_a in a_names:
                    if var_a not in ast_map.keys():
                        ast_map[var_a] = dict()
                    if var_c in ast_map[var_a].keys():
                        ast_map[var_a][var_c] += 1
                    else:
                        ast_map[var_a][var_c] = 1
                map_line = ast_map_file.readline().strip()
    except Exception as e:
        err_exit(e, "Unexpected error while parsing ast-map")

    UNKNOWN = "#UNKNOWN#"
    variable_mapping = dict()
    try:
        while variable_list_a:
            var_a = variable_list_a.pop()
            if var_a not in variable_mapping.keys():
                a_name = var_a.split(" ")[-1]
                if a_name in ast_map.keys():
                    max_match = -1
                    best_match = None
                    for var_c in ast_map[a_name].keys():
                        if max_match == -1:
                            max_match = ast_map[a_name][var_c]
                            best_match = var_c
                        elif ast_map[a_name][var_c] > max_match:
                            max_match = ast_map[a_name][var_c]
                            best_match = var_c
                    if best_match:
                        for var_c in variable_list_c:
                            c_name = var_c.split(" ")[-1]
                            if c_name == best_match:
                                variable_mapping[var_a] = var_c
                if var_a not in variable_mapping.keys():
                    variable_mapping[var_a] = UNKNOWN
    except Exception as e:
        err_exit(e, "Unexpected error while mapping vars.")

    try:
        with open("output/var-map", "w", errors='replace') as var_map_file:
            for var_a in variable_mapping.keys():
                var_map_file.write(var_a + " -> " + variable_mapping[var_a] + \
                                   "\n")
    except Exception as e:
        err_exit(e, "ASdasdas")
    
    return variable_mapping
            

def gen_json(vec_f, proj, ASTlists):
    Print.blue("\t\tClang AST parse " + vec_f.function + " in " + proj.name + \
               "...")
    json_file = "output/json_" + proj.name
    ASTdump(vec_f.file, json_file)
    ASTlists[proj.name] = ASTparser.AST_from_file(json_file)
    
    
def clean_parse(content, separator):
    if content.count(separator) == 1:
        return content.split(separator)
    i = 0
    while i < len(content):
        if content[i] == "\"":
            i += 1
            while i < len(content)-1:
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
    half = len(nodes)//2
    node1 = separator.join(nodes[:half])
    node2 = separator.join(nodes[half:])
    return [node1, node2]
    

def ASTdump(file, output):
    c = crochet_diff + "-ast-dump-json " + file + \
        " 2> output/errors_AST_dump > " + output
    exec_com(c)
    

def ASTscript(file1, file2, output, only_matches=False):
    c = crochet_diff + "-s 2147483647 -dump-matches " + file1 + \
        " " + file2 + " 2> output/errors_clang_diff "
    if only_matches:
        c += "| grep '^Match ' "
    c += " > " + output
    exec_com(c, True)
    

def inst_comp(i):
    return min(order.index(i), 2)
    
    
def order_comp(inst1, inst2):
    
    if inst1[0] in order[0:2]:
        l1 = inst1[1]
    elif inst1[0] in order[2:4]:
        l1 = inst1[2]
        
    if inst2[0] in order[0:2]:
        l2 = inst2[1]
    elif inst2[0] in order[2:4]:
        l2 = inst2[2]
        
    line1 = int(l1.line)
    line2 = int(l2.line)
    if line1 != line2:
        return line2 - line1
    
    line1 = int(l1.line_end)
    line2 = int(l2.line_end)
    if line1 != line2:
        return line2 - line1
    
    col1 = int(l1.col)
    col2 = int(l2.col)
    if col1 != col2:
        return col2 - col1
        
    col1 = int(l1.col_end)
    col2 = int(l2.col_end)
    if col1 != col2:
        return col2 - col1
    
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


def script_node(node):
    return node.type + "(" + str(node.id) + ")"
    
    
def patch_instruction(inst):
    #Print.white("\t" + " - ".join([str(j) for j in inst]))

    c = ""
    
    instruction = inst[0]
    
    if instruction == UPDATE:
        nodeC = inst[1]
        nodeD = inst[2]
        c = UPDATE + " " + script_node(nodeC) + TO + script_node(nodeD)
            
    elif instruction == DELETE:
        nodeC = inst[1]
        c = DELETE + " " + script_node(nodeC)
        
    elif instruction == MOVE:
        nodeD1 = script_node(inst[1])
        nodeD2 = script_node(inst[2])
        pos = str(inst[3])
        c = MOVE + " " + nodeD1 + INTO + nodeD2 + AT + pos
    
    elif instruction == INSERT:
        nodeB = script_node(inst[1])
        nodeC = script_node(inst[2])
        pos = str(inst[3])
        c = INSERT + " " + nodeB + INTO + nodeC + AT + pos
        
    Print.green(c)
    script_path = "output/script"
    if not (os.path.isfile(script_path)):
        with open(script_path, 'w') as script:
            script.write(c)
    else:
        with open(script_path, 'a') as script:
            script.write("\n" + c)

    
def transplantation(to_patch):
    for (vec_f_a, vec_f_c, var_map) in to_patch:
        try:
            vec_f_b_file = vec_f_a.file.replace(Pa.path, Pb.path)
            if not vec_f_b_file in Pb.funcs.keys():
                err_exit("Error: File not found among affected.", vec_f_b_file)
            if vec_f_a.function in Pb.funcs[vec_f_b_file].keys():
                vec_f_b = Pb.funcs[vec_f_b_file][vec_f_a.function]
            else:
                err_exit("Error: Function not found among affected.",
                         vec_f_a.function, vec_f_b_file,
                         Pb.funcs[vec_f_b_file].keys())
            ASTlists = dict()
        except Exception as e:
            err_exit(e, vec_f_b_file, vec_f_a, Pa.path, Pb.path,
                     vec_f_a.function)
        
        Print.blue("Generating temp files for each pertinent function...")
        
        try:
            gen_json(vec_f_a, Pa, ASTlists)
            gen_json(vec_f_b, Pb, ASTlists)
            gen_json(vec_f_c, Pc, ASTlists)
        except:
            err_exit("Error parsing with crochet-diff. Remember to bear make.")
            
        Print.blue("Generating edit script: " + Pa.name + TO + Pb.name + "...")
        try:
            ASTscript(vec_f_a.file, vec_f_b.file, "output/diff_script_AB")
        except Exception as e:
            err_exit(e, "Unexpected fail at generating diff_script_AB.")
        
        Print.blue("Finding common structures in " + Pa.name + " w.r.t. " + \
                   Pc.name + "...")
        try:
            ASTscript(vec_f_a.file, vec_f_c.file, "output/diff_script_AC")
        except Exception as e:
            err_exit(e, "Unexpected fail at generating diff_script_AC.")
                      
        Print.blue("Generating edit script: " + Pc.name + TO + "Pd...")

        instruction_AB = list()
        inserted_B = list()
        match_BA = dict()
        with open('output/diff_script_AB', 'r', errors='replace') as script_AB:
            line = script_AB.readline().strip()
            while line:
                line = line.split(" ")
                if len(line) > 3 and line[0] == UPDATE and line[1] == AND and \
                   line[2] == MOVE:
                    instruction = line[2]
                    #Print.yellow(line)
                    content = " ".join(line[3:])
                    nodeA, nodeB = clean_parse(content, INTO)
                    instruction_AB.append((UPDATE, match_BA[nodeA], nodeA))
                else:
                    instruction = line[0]
                    content = " ".join(line[1:])
                # Match nodeA to nodeB
                if instruction == MATCH:
                    try:
                        nodeA, nodeB = clean_parse(content, TO)
                        match_BA[nodeB] = nodeA
                    except Exception as e:
                        err_exit(e, "Something went wrong in MATCH (AB).",
                                 line, instruction, content)
                # Update nodeA to nodeB (only care about value)
                elif instruction == UPDATE:
                    try:
                        nodeA, nodeB = clean_parse(content, TO)
                        instruction_AB.append((instruction, nodeA, nodeB))
                    except Exception as e:
                        err_exit(e, "Something went wrong in UPDATE.")
                # Delete nodeA
                elif instruction == DELETE:
                    try:
                        nodeA = content
                        instruction_AB.append((instruction, nodeA))
                    except Exception as e:
                        err_exit(e, "Something went wrong in DELETE.")
                # Move nodeA into nodeB at pos
                elif instruction == MOVE:
                    try:
                        nodeA, nodeB = clean_parse(content, INTO)
                        nodeB_at = nodeB.split(AT)
                        nodeB = AT.join(nodeB_at[:-1])
                        pos = nodeB_at[-1]
                        instruction_AB.append((instruction, nodeA, nodeB, pos))
                    except Exception as e:
                        err_exit(e, "Something went wrong in MOVE.")
                # Insert nodeB1 into nodeB2 at pos
                elif instruction == INSERT:
                    try:
                        nodeB1, nodeB2 = clean_parse(content, INTO)
                        nodeB2_at = nodeB2.split(AT)
                        nodeB2 = AT.join(nodeB2_at[:-1])
                        pos = nodeB2_at[-1]
                        instruction_AB.append((instruction, nodeB1, nodeB2,
                                              pos))
                        inserted_B.append(nodeB1)
                    except Exception as e:
                        err_exit(e, "Something went wrong in INSERT.")
                line = script_AB.readline().strip()
        
        modified_AB = []
        inserted = []
        Print.white("Original patch from Pa to Pb")
        for i in instruction_AB:
            inst = i[0]
            if inst == DELETE:
                nodeA = i[1].split("(")[-1][:-1]
                nodeA = ASTlists[Pa.name][int(nodeA)]
                Print.white("\t" + DELETE + " - " + str(nodeA))
                modified_AB.append((DELETE, nodeA))
            elif inst == UPDATE:
                nodeA = i[1].split("(")[-1][:-1]
                nodeA = ASTlists[Pa.name][int(nodeA)]
                nodeB = i[2].split("(")[-1][:-1]
                nodeB = ASTlists[Pb.name][int(nodeB)]
                Print.white("\t" + UPDATE + " - " + str(nodeA) + " - " + \
                            str(nodeB))
                modified_AB.append((UPDATE, nodeA, nodeB))
            elif inst == MOVE:
                nodeB1 = i[1].split("(")[-1][:-1]
                nodeB1 = ASTlists[Pb.name][int(nodeB1)]
                nodeB2 = i[2].split("(")[-1][:-1]
                nodeB2 = ASTlists[Pb.name][int(nodeB2)]
                pos = i[3]
                Print.white("\t" + MOVE + " - " + str(nodeB1) + " - " + \
                            str(nodeB2) + " - " + str(pos))
                inserted.append(nodeB1)
                if nodeB2 not in inserted:
                    modified_AB.append((MOVE, nodeB1, nodeB2, pos))
                else:
                    if i[1] in match_BA.keys():
                        nodeA = match_BA[i[1]]
                        nodeA = nodeA.split("(")[-1][:-1]
                        nodeA = ASTlists[Pa.name][int(nodeA)]
                        modified_AB.append((DELETE, nodeA))
                    else:
                        Print.yellow("Warning: node " + str(nodeB1) + \
                                     "could not be matched. " + \
                                     "Skipping MOVE instruction...")
                        Print.yellow(i)
            elif inst == INSERT:
                nodeB1 = i[1].split("(")[-1][:-1]
                nodeB1 = ASTlists[Pb.name][int(nodeB1)]
                nodeB2 = i[2].split("(")[-1][:-1]
                nodeB2 = ASTlists[Pb.name][int(nodeB2)]
                pos = i[3]
                Print.white("\t" + INSERT + " - " + str(nodeB1) + " - " + \
                            str(nodeB2) + " - " + str(pos))
                inserted.append(nodeB1)
                if nodeB2 not in inserted:
                    modified_AB.append((INSERT, nodeB1, nodeB2, pos))
        
        #Sort in reverse order and depending on instruction for application
        modified_AB.sort(key=cmp_to_key(order_comp))
        # Delete overlapping DELETE operations
        reduced_AB = set()
        n_inst = len(modified_AB)
        for i in range(n_inst):
            inst1 = modified_AB[i]
            if inst1[0] == DELETE:
                for j in range(i+1, n_inst):
                    inst2 = modified_AB[j]
                    if inst2[0] == DELETE:
                        node1 = inst1[1]
                        node2 = inst2[1]
                        if node1.contains(node2):
                            reduced_AB.add(j)
                        elif node2.contains(node1):
                            reduced_AB.add(i)
        modified_AB = [modified_AB[i] for i in range(n_inst)
                          if i not in reduced_AB]
        # Adjusting position for MOVE and INSERT operations
        i = 0
        while i < len(modified_AB) - 1:
            inst1 = modified_AB[i][0]
            if inst1 == INSERT or inst1 == MOVE:
                j = i
                node1 = modified_AB[i][2]
                while j < len(modified_AB) - 1:
                    j += 1
                    inst2 = modified_AB[j][0]
                    if inst2 != INSERT and inst2 != MOVE:
                        break
                    node2 = modified_AB[j][2]
                    if node1 != node2:
                        break
                    pos1 = int(modified_AB[j-1][3])
                    pos2 = int(modified_AB[j][3])
                    if pos2 != pos1 + 1:
                        break
                for k in range(i, j):
                    inst = modified_AB[k][0]
                    nodeB1 = modified_AB[k][1]
                    nodeB2 = modified_AB[k][2]
                    # We put pos of i to all of them up to j-1
                    pos = modified_AB[i][3]
                    modified_AB[k] = (inst, nodeB1, nodeB2, pos)
                i = j-1 
            i += 1
        Print.green("Modified simplified script:")
        for j in [" - ".join([str(k) for k in i]) for i in modified_AB]:
            Print.white("\t" + j)
            
        instruction_AB = []
        for i in modified_AB:
            inst = i[0]
            if inst == DELETE:
                nodeA = str(i[1].type) + "(" + str(i[1].id) + ")"
                instruction_AB.append((DELETE, nodeA))
            elif inst == UPDATE:
                nodeA = str(i[1].type) + "(" + str(i[1].id) + ")"
                nodeB = str(i[2].type) + "(" + str(i[2].id) + ")"
                instruction_AB.append((UPDATE, nodeA, nodeB))
            elif inst == INSERT:
                nodeB1 = str(i[1].type) + "(" + str(i[1].id) + ")"
                nodeB2 = str(i[2].type) + "(" + str(i[2].id) + ")"
                pos = int(i[3])
                instruction_AB.append((INSERT, nodeB1, nodeB2, pos))
            elif inst == MOVE:
                nodeB1 = str(i[1].type) + "(" + str(i[1].id) + ")"
                nodeB2 = str(i[2].type) + "(" + str(i[2].id) + ")"
                pos = int(i[3])
                instruction_AB.append((MOVE, nodeB1, nodeB2, pos))
        
        match_AC = dict()
        with open('output/diff_script_AC', 'r', errors='replace') as script_AC:
            line = script_AC.readline().strip()
            while line:
                line = line.split(" ")
                instruction = line[0]
                content = " ".join(line[1:])
                if instruction == MATCH:
                    try:
                        nodeA, nodeC = clean_parse(content, TO)
                        match_AC[nodeA] = nodeC
                    except Exception as e:
                        err_exit(e, "Something went wrong in MATCH (AC).",
                                 line, instruction, content)
                line = script_AC.readline().strip()
        
        instruction_CD = list()
        inserted_D = list()
        match_BD = dict()        
        for i in instruction_AB:
            instruction = i[0]
            # Update nodeA to nodeB (value) -> Update nodeC to nodeD (value)
            if instruction == UPDATE:
                try:
                    nodeA = i[1]
                    nodeB = i[2]
                    nodeC = "?"
                    nodeD = nodeB.split("(")[-1][:-1]
                    nodeD = ASTlists[Pb.name][int(nodeD)]
                    if nodeA in match_AC.keys():
                        nodeC = match_AC[nodeA]
                        nodeC = nodeC.split("(")[-1][:-1]
                        nodeC = ASTlists[Pc.name][int(nodeC)]
                        if nodeC.line == None:
                            nodeC.line = nodeC.parent.line
                        instruction_CD.append((UPDATE, nodeC, nodeD))
                    else:
                        Print.yellow("Warning: Match for " + str(nodeA) + \
                                     "not found. Skipping UPDATE instruction.")
                except Exception as e:
                    err_exit(e, "Something went wrong with UPDATE.")
            # Delete nodeA -> Delete nodeC
            elif instruction == DELETE:
                try:
                    nodeA = i[1]
                    nodeC = "?"
                    if nodeA in match_AC.keys():
                        nodeC = match_AC[nodeA]
                        nodeC = nodeC.split("(")[-1][:-1]
                        nodeC = ASTlists[Pc.name][int(nodeC)]
                        if nodeC.line == None:
                            nodeC.line = nodeC.parent.line
                        instruction_CD.append((DELETE, nodeC))
                    else:
                        Print.yellow("Warning: Match for " + str(nodeA) + \
                                     "not found. Skipping DELETE instruction.")
                except Exception as e:
                    err_exit(e, "Something went wrong with DELETE.")
            # Move nodeA to nodeB at pos -> Move nodeC to nodeD at pos
            elif instruction == MOVE:
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
                            if "(" in nodeC1:
                                nodeC1 = nodeC1.split("(")[-1][:-1]
                                nodeC1 = ASTlists[Pc.name][int(nodeC1)]
                        else:
                            # TODO: Manage case in which nodeA1 is unmatched
                            Print.yellow("Node in Pa not found in Pc: (1)")
                            Print.yellow(nodeA1)
                    elif nodeB1 in inserted_B:
                        if nodeB1 in match_BD.keys():
                            nodeC1 = match_BD[nodeB1]
                        else:
                            # TODO: Manage case for node not found
                            Print.yellow("Node to be moved was not found. (2)")
                            Print.yellow(nodeB1)
                    if nodeB2 in match_BA.keys():
                        nodeA2 = match_BA[nodeB2]
                        if nodeA2 in match_AC.keys():
                            nodeC2 = match_AC[nodeA2]
                            if "(" in nodeC2:
                                nodeC2 = nodeC2.split("(")[-1][:-1]
                                nodeC2 = ASTlists[Pc.name][int(nodeC2)]
                        else:
                            # TODO: Manage case for unmatched nodeA2
                            Print.yellow("Node in Pa not found in Pc: (1)")
                            Print.yellow(nodeA2)
                    elif nodeB2 in inserted_B:
                        if nodeB2 in match_BD.keys():
                            nodeC2 = match_BD[nodeB2]
                        else:
                            # TODO: Manage case for node not found
                            Print.yellow("Node to be moved was not found. (2)")
                            Print.yellow(nodeB2)
                    try:
                        m = 0
                        true_B2 = nodeB2.split("(")[-1][:-1]
                        true_B2 = ASTlists[Pb.name][int(true_B2)]
                        M = len(true_B2.children)
                        if pos != 0 and pos < M-1:
                            nodeB2_l = true_B2.children[pos-1]
                            nodeB2_r = true_B2.children[pos+1]
                            if nodeB2_l in match_BA.keys():
                                nodeA2_l = match_BA[nodeB2_l]
                                if nodeA2_l in match_AC.keys():
                                    nodeC2_l = match_AC[nodeA2_l]
                                    if nodeC2_l in nodeC2.children:
                                        m = nodeC2.children.index(nodeC2_l)
                                        pos = m + 1
                            elif nodeB2_r in match_BA.keys():
                                nodeA2_r = match_BA[nodeB2_r]
                                if nodeA2_r in match_AC.keys():
                                    nodeC2_r = match_AC[nodeA2_r]
                                    if nodeC2_r in nodeC2.children:
                                        M = nodeC2.children.index(nodeC2_r)
                                        pos = M
                        elif pos >= M - 1:
                            pos += len(nodeC2.children) - M + 1
                    except Exception as e:
                        err_exit(e, "Failed at locating pos.")
                    
                    if type(nodeC1) == ASTparser.AST:
                        if nodeC1.line == None:
                            nodeC1.line = nodeC1.parent.line
                        if type(nodeC2) == ASTparser.AST:
                            if nodeC2.line == None:
                                nodeC2.line = nodeD.parent.line
                            if nodeC2 in inserted_D:
                                instruction_CD.append((DELETE, nodeC1))
                            else:
                                instruction_CD.append((MOVE, nodeC1, nodeC2,
                                                       pos))
                            inserted_D.append(nodeC1)
                            
                        else:
                            Print.yellow("Could not find match for node. " + \
                                         "Ignoring MOVE operation. (D)")
                    else:
                        Print.yellow("Could not find match for node. " + \
                                     "Ignoring MOVE operation. (C)")
                except Exception as e:
                    err_exit(e, "Something went wrong with MOVE.")
            
            # Insert nodeB1 to nodeB2 at pos -> Insert nodeD1 to nodeD2 at pos
            elif instruction == INSERT:
                try:
                    nodeB1 = i[1]
                    nodeB2 = i[2]
                    pos = int(i[3])
                    nodeD1 = nodeB1.split("(")[-1][:-1]
                    nodeD1 = ASTlists[Pb.name][int(nodeD1)]
                    # TODO: Edit nodeD1 to get right structures
                    nodeD2 = nodeB2.split("(")[-1][:-1]
                    nodeD2 = ASTlists[Pb.name][int(nodeD2)]
                    # TODO: Is this correct?
                    if nodeD2.line != None:
                        nodeD1.line = nodeD2.line
                    else:
                        nodeD1.line = nodeD2.parent.line
                    # TODO: Edit nodeD2 to get right structures
                    
                    if nodeB2 in match_BA.keys():
                        nodeA2 = match_BA[nodeB2]
                        if nodeA2 in match_AC.keys():
                            nodeD2 = match_AC[nodeA2]
                            nodeD2 = nodeD2.split("(")[-1][:-1]
                            nodeD2 = ASTlists[Pc.name][int(nodeD2)]
                            # TODO: Edit nodeD2 to get right structures
                    elif nodeB2 in match_BD.keys():
                        nodeD2 = match_BD[nodeB2]
                    else:
                        Print.yellow("Warning: node for insertion not" + \
                                     " found. Skipping INSERT operation.")
                    try:
                        m = 0
                        true_B2 = nodeB2.split("(")[-1][:-1]
                        true_B2 = ASTlists[Pb.name][int(true_B2)]
                        M = len(true_B2.children)
                        if pos != 0 and pos < M-1:
                            nodeB2_l = true_B2.children[pos-1]
                            nodeB2_r = true_B2.children[pos+1]
                            if nodeB2_l in match_BA.keys():
                                nodeA2_l = match_BA[nodeB2_l]
                                if nodeA2_l in match_AC.keys():
                                    nodeD2_l = match_AC[nodeA2_l]
                                    if nodeD2_l in nodeD2.children:
                                        m = nodeD2.children.index(nodeD2_l)
                                        pos = m + 1
                            elif nodeB2_r in match_BA.keys():
                                nodeA2_r = match_BA[nodeB2_r]
                                if nodeA2_r in match_AC.keys():
                                    nodeD2_r = match_AC[nodeA2_r]
                                    if nodeD2_r in nodeD2.children:
                                        M = nodeD2.children.index(nodeD2_r)
                                        pos = M
                        elif pos >= M - 1:
                            pos += len(nodeD2.children) - M + 1
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
                                instruction_CD.append((INSERT, nodeD1, nodeD2,
                                                       pos))
                except Exception as e:
                    err_exit(e, "Something went wrong with INSERT.")
        
        Print.white("Proposed patch from Pc to Pd")
        
        for i in instruction_CD:
            patch_instruction(i)
        
        patch(vec_f_a.file, vec_f_b.file, vec_f_c.file)
        
def patch(file_a, file_b, file_c):
    global changes, n_changes
    # This is to have an id of the file we're patching
    n_changes += 1
    # Check for an edit script
    if not (os.path.isfile("output/script")):
        err_exit("No script was generated. Exiting with error.")
        
    output_file = "output/" + str(n_changes) + "_temp.c"
    c = ""
    # We add file_c into our dict (changes) to be able to backup and copy it
    if file_c not in changes.keys():
        filename = file_c.split("/")[-1]
        backup_file = str(n_changes) + "_" + filename
        changes[file_c] = backup_file
        c += "cp " + file_c + " Backup_Folder/" + backup_file + "; "
    # We apply the patch using the script and crochet-patch
    c += crochet_patch + "-script=output/script -source=" + file_a + \
        " -destination=" + file_b + " -target=" + file_c + \
        " 2> output/errors > " + output_file + "; "
    c += "cp " + output_file + " " + file_c
    exec_com(c)
    # We fix basic syntax errors that could have been introduced by the patch
    c2 = clang_check + "-fixit " + file_c + " 2> output/syntax_errors"
    exec_com(c2)
    # We check that everything went fine, otherwise, we restore everything
    try:
        c3 = clang_check + file_c
        exec_com(c3)
    except Exception as e:
        Print.red("Clang-check could not repair syntax errors.")
        restore_files()
        err_exit(e, "Crochet failed.")
    # We format the file to be with proper spacing (needed?)
    c3 = clang_format + file_c + " > " + output_file + "; "
    c3 += "cp " + output_file + " " + file_c + ";"
    exec_com(c3)
    
    # We rename the script so that it won't be there for other files
    c4 = "mv output/script output/" + str(n_changes) + "_script"
    exec_com(c4)
    
    
def restore_files():
    Print.yellow("Restoring files...")
    for file in changes.keys():
        backup_file = changes[file]
        c = "cp Backup_Folder/" + backup_file + " " + file
        exec_com(c)
    Print.yellow("Files restored")
    
    
def verification():
    if crash != None:
        try:
            Pc.make(bear=False)
        except Exception as e:
            Print.yellow("Make failed.")
            Print.yellow(e)
            restore_files()
            err_exit("Crochet failed at patching. Project did not compile" + \
                     "after changes. Exiting.")
        try:
            c = "sh " + crash
            exec_com(c)
        except Exception as e:
            Print.yellow("Crash gave an error.")
            Print.yellow(e)
            restore_files()
            err_exit("Crochet failed at patching. Project did not compile" + \
                     "after changes. Exiting.")
    # TODO: Remove this part when we don't care anymore
    restore_files()
            
            

def safe_exec(function, title, *args):
    start = time.time()
    Print.title("Starting " + title + "...")
    descr = title[0].lower() + title[1:]
    try:
        if not args:
            a = function()
        else:
            a = function(*args)
        runtime = str(time.time() - start)
        Print.rose("Successful " + descr + ", after " + runtime + " seconds.")
    except Exception as e:
        runtime = str(time.time() - start)
        Print.red("Crash during " + descr + ", after " + runtime + " seconds.")
        err_exit(e, "Unexpected error during " + descr + ".")
    return a
              
              
def run_crochet():
    global Pa, Pb, Pc
    # Little crochet introduction
    Print.start()
    
    # Time for final running time
    start = time.time()
    
    # Prepare projects directories by getting paths and cleaning residual files
    safe_exec(initialize, "projects initialization and cleaning")
    
    # Generates vectors for pertinent functions (modified from Pa to Pb)
    safe_exec(gen_diff, "search for affected functions and vector generation")
              
    # Generates vectors for all functions in Pc
    safe_exec(gen_ASTs, "vector generation for functions in Pc")

    # Pairwise vector comparison for matching
    to_patch = safe_exec(compare, "pairwise vector comparison for matching")
    
    # Using all previous structures to transplant patch
    safe_exec(transplantation, "patch transplantation", to_patch)
    
    # Verification by compiling and re-running crash
    safe_exec(verification, "program verification")
    
    # Final clean
    Print.title("Cleaning residual files generated by Crochet...")
    
    # Final running time and exit message
    runtime = str(time.time() - start)
    Print.exit_msg(runtime)
    
    
if __name__=="__main__":
    #test_parsing()
    try:
        run_crochet()
    except KeyboardInterrupt as e:
        err_exit("Program Interrupted by User")