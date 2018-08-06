#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
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


CONF_FILE_NAME = "crochet.conf"
PATCH_COMMAND = "crochet-patch"
PATCH_SIZE = "1000"
DIFF_SIZE = "crochet-diff "
DIFF_COMMAND = "1000"
SYNTAX_CHECK_COMMAND = "clang-check "
STYLE_FORMAT_COMMAND = "clang-format -style=LLVM "


interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

UPDATEMOVE = "UpdateMove"
UPDATE = "Update"
MOVE = "Move"
INSERT = "Insert"
DELETE = "Delete"
MATCH = "Match"
TO = " to "
AT = " at "
INTO = " into "
AND = "and"
order = [UPDATE, UPDATEMOVE, DELETE, MOVE, INSERT]

changes = dict()
n_changes = 0


def initialize():
    global Pa, Pb, Pc, crash, CONF_FILE_NAME

    if len(sys.argv) > 1:
        CONF_FILE_NAME = sys.argv[1]

    with open(CONF_FILE_NAME, 'r', errors='replace') as conf_file:
        args = [i.strip() for i in conf_file.readlines()]

    if len(args) < 3:
        err_exit("Insufficient arguments: Pa, Pb, and Pc source paths required.")

    Pa = Project.Project(args[0], "Pa")
    Pb = Project.Project(args[1], "Pb")
    Pc = Project.Project(args[2], "Pc")

    if len(args) >= 4:
        if os.path.isfile(args[3]):
            if len(args[3]) >= 4 and args[3][:-3] == ".sh":
                crash = args[3]
            else:
                Print.yellow("Script must be path to a shell (.sh) file. Running anyway.")
        else:
            Print.yellow("No script for crash provided. Running anyway.")
    else:
            Print.yellow("No script for crash provided. Running anyway.")
    clean()


def find_diff_files():
    global Pa, Pb
    extensions = get_extensions(Pa.path, "output/files1")
    extensions = extensions.union(get_extensions(Pb.path, "output/files2"))
    excluded = 'output/excluded'
    with open(excluded, 'w', errors='replace') as exclusions:
        for pattern in extensions:
            exclusions.write(pattern + "\n")
    # TODO: Include cases where a file is added or removed
    c = "diff -ENZBbwqr " + Pa.path + " " + Pb.path + " -X " + excluded + \
        "> output/diff; "
    c += "cat output/diff | grep -P '\.c and ' > output/diff_C; "
    c += "cat output/diff | grep -P '\.h and ' > output/diff_H; "
    exec_com(c, False)

    
def gen_diff():
    global Pa, Pb
    # .h and .c files
    Print.blue("Finding differing files...")
    find_diff_files()
    
    # H files
    with open('output/diff_H', 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            diff_line = diff_line.split(" ")
            file_a = diff_line[1]
            file_b = diff_line[3]
            ASTgen.llvm_format(file_a)
            ASTgen.llvm_format(file_b)
            ASTgen.parseAST(file_a, Pa, Deckard=True, h_file=True)
            Print.rose("\t\tFile successfully found: " + \
                       file_a.split("/")[-1] + " from " + Pa.name + " to " + \
                       Pb.name)
            diff_line = diff.readline().strip()
            
    # C files
    Print.blue("Starting fine-grained diff...\n")
    with open('output/diff_C', 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            diff_line = diff_line.split(" ")
            file_a = diff_line[1]
            file_b = diff_line[3]
            ASTgen.llvm_format(file_a)
            ASTgen.llvm_format(file_b)
            c = "diff -ENBZbwr " + file_a + " " + file_b + " > output/C_diff"
            exec_com(c, False)
            pertinent_lines = []
            pertinent_lines_b = []
            with open('output/C_diff', 'r', errors='replace') as file_diff:
                file_line = file_diff.readline().strip()
                while file_line:
                    # We only want lines starting with a line number
                    if 48 <= ord(file_line[0]) <= 57:
                        # add
                        if 'a' in file_line:
                            l = file_line.split('a')
                        # delete
                        elif 'd' in file_line:
                            l = file_line.split('d')
                        # change (delete + add)
                        elif 'c' in file_line:
                            l = file_line.split('c')
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
                ASTgen.find_affected_funcs(Pa, file_a, pertinent_lines)
                ASTgen.find_affected_funcs(Pb, file_b, pertinent_lines_b)
            except Exception as e:
                err_exit(e, "Failed at finding affected functions.")
                        
            diff_line = diff.readline().strip()


def gen_ASTs_ext(ext, output, is_h=False):
    rxt = ext
    Print.blue("Gen vectors for " + rxt + " files in " + Pc.name + "...")
    # Generates an AST file for each file of extension ext
    find_files(Pc.path, ext, output)
    with open(output, 'r', errors='replace') as files:
        file = files.readline().strip()
        while file:
            # Parses it to get useful information and generate vectors
            try:
                ASTgen.parseAST(file, Pc, Deckard=True, h_file=is_h)
            except Exception as e:
                err_exit(e, "Unexpected error in parseAST with file:", file)
            file = files.readline().strip()
    
    
def gen_ASTs():
    # Generates an AST file for each .h file
    gen_ASTs_ext("*\.h", "output/Hfiles", is_h=True)
    # Generates an AST file for each .c file
    gen_ASTs_ext("*\.c", "output/Cfiles", is_h=False)
    

    
def get_vector_list(proj, ext):
    if "c" in ext:
        rxt = "C"
    else:
        rxt = "h"
    Print.blue("Getting vectors for " + rxt + " files in " + proj.name + "...")
    filepath = "output/vectors_" + rxt + "_" + proj.name
    find_files(proj.path, ext,  filepath)
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


def compare_H():
    global Pa, Pc
    h_ext = "*\.h\.vec"
    vecs_A = get_vector_list(Pa, h_ext)
    to_patch = []
    if len(vecs_A) == 0:
        return to_patch
    vecs_C = get_vector_list(Pc, h_ext)
    
    factor = 2
    
    Print.blue("Declaration mapping for *.h files")
    for i in vecs_A:
        best = vecs_C[0]
        best_d = ASTVector.ASTVector.dist(i[1], best[1])
        dist = dict()
        
        for j in vecs_C:
            d = ASTVector.ASTVector.dist(i[1], best[1])
            dist[j[0]] = d
            if d < best_d:
                best = j
                best_d = d
        
        candidates = [best]
        candidates_d = [best_d]
        for j in vecs_C:
            if j != best:
                d = dist[j[0]]
                if d <= factor*best_d:
                    candidates.append(j)
                    candidates_d.append(d)
        
        decl_maps = list()
        match_score = list()
        matches = list()
        
        file_a = i[0].replace(Pa.path, "")[:-4]
        for k in range(len(candidates)):
            candidate = candidates[k]
            file_c = candidate[0].replace(Pc.path, "")[:-4]
            d_c = str(candidates_d[k])
            Print.blue("\tPossible match for " + file_a + " in Pa:")
            Print.blue("\t\tFile: " + file_c + " in Pc")
            Print.blue("\t\tDistance: " + d_c + "\n")
            Print.blue("\tDeclaration mapping from " + file_a + " to " + \
                       file_c + ":")
            try:
                decl_map, match, edit = detect_matching_declarations(file_a, file_c)
                decl_maps.append(decl_map)
                match_score.append((match-edit)/(match+edit))
                matches.append(match)
            except Exception as e:
                err_exit(e, "Unexpected error while matching declarations.")
            with open('output/var-map', 'r', errors='replace') as mapped:
                mapping = mapped.readline().strip()
                while mapping:
                    Print.grey("\t\t" + mapping)
                    mapping = mapped.readline().strip()
        
        best_score = match_score[0]
        best = candidates[0]
        best_d = candidates_d[0]
        best_match = matches[0]
        best_index = [k]

        for k in range(1, len(candidates)):
            score = match_score[k]
            d = candidates_d[k]
            match = matches[k]
            if score > best_score:
                best_score = score
                best_index = [k]
            elif score == best_score:
                if d < best_d:
                    best_d = d
                    best_index = [k]
                elif d == best_d:
                    if match > best_match:
                        best_match = match
                        best_index = [k]
                    else:
                        best_index.append(k)
        # Potentially many identical matches
        M = len(best_index)
        m = min(1, M)
        Print.green("\t" + str(M) + " match" + "es" * m + " for " + file_a)
        for index in best_index:
            file_c = candidates[index][0][:-4].replace(Pc.path, "")
            d_c = str(candidates_d[index])
            decl_map = decl_maps[index]
            Print.green("\t\tMatch for " + file_a + " in Pa:")
            Print.blue("\t\tFile: " + file_c + " in Pc.")
            Print.blue("\t\tDistance: " + d_c + ".\n")
            #Print.green((Pa.path + file_a, Pc.path + file_c, var_map))
            to_patch.append((Pa.path + file_a, Pc.path + file_c, decl_map))
    return to_patch


def compare_C():
    global Pa, Pc
    c_ext = "*\.c\.*\.vec"
    vecs_A = get_vector_list(Pa, c_ext)
    vecs_C = get_vector_list(Pc, c_ext)
    
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
                
        count_unknown = [0]*len(candidates)
        count_vars = [0]*len(candidates)
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
        best_prop = count_unknown[0]/count_vars[0]
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
    c = DIFF_SIZE + "-dump-matches " + source_a + " " + source_b
    if source_a[-1] == "h":
        c += " --"
    c += " 2>> output/errors_clang_diff"
    c += "| grep -P '^Match ' | grep -P '^Match ' > output/ast-map"
    try:
        exec_com(c, True)
    except Exception as e:
        err_exit(e, "Unexpected error in generate_ast_map.")
        
def simple_crochet_diff(source_a, source_b):
    c = DIFF_SIZE + "-dump-matches " + source_a + " " + source_b
    if source_a[-1] == "h":
        c += " --"
    c += " 2>> output/errors_clang_diff > output/ast-map"
    try:
        exec_com(c, True)
    except Exception as e:
        err_exit(e, "Unexpected error in simple_crochet_diff.")

def id_from_string(simplestring):    
    return int(simplestring.split("(")[-1][:-1])

def getId(NodeRef): 
    return int(NodeRef.split("(")[-1][:-1])

def getType(NodeRef):
    return NodeRef.split("(")[0]

def detect_matching_declarations(file_a, file_c):
    
    try:
        simple_crochet_diff(Pa.path + file_a, Pc.path + file_c)
    except Exception as e:
        err_exit(e, "Error at generate_ast_map.")
        
    ast_map = dict()
    
    try:
        with open("output/ast-map", "r", errors="replace") as ast_map_file:
            map_lines = ast_map_file.readlines()
    except Exception as e:
        err_exit(e, "Unexpected error parsing ast-map in detect_matching declarations")
    
    matches = 0
    edits = 0
    for line in map_lines:
        line = line.strip()
        if len(line) > 6 and line[:5] == "Match":
            line = clean_parse(line[6:], TO)
            if "Decl" not in line[0]:
                continue
            matches += 1
            ast_map[line[0]] = line[1]
        else:
            edits += 1

    with open("output/var-map", "w", errors='replace') as var_map_file:
        for var_a in ast_map.keys():
            var_map_file.write(var_a + " -> " + ast_map[var_a] + "\n")
    
    return ast_map, matches, edits
            

def detect_matching_variables(f_a, file_a, f_c, file_c):
    
    try:
        generate_ast_map(Pa.path + file_a, Pc.path + file_c)
    except Exception as e:
        err_exit(e, "Error at generate_ast_map.")
    
    function_a = Pa.funcs[Pa.path + file_a][f_a]
    variable_list_a = function_a.variables.copy()

    while '' in variable_list_a:
        variable_list_a.remove('')
    
    a_names = [i.split(" ")[-1] for i in variable_list_a]

    function_c = Pc.funcs[Pc.path + file_c][f_c]
    variable_list_c = function_c.variables
    while '' in variable_list_c:
        variable_list_c.remove('')
    
    #Print.white(variable_list_c)
    
    json_file_A = Pa.path + file_a + ".AST"
    ast_A = ASTparser.AST_from_file(json_file_A)
    json_file_C = Pc.path + file_c + ".AST"
    ast_C = ASTparser.AST_from_file(json_file_C)

    ast_map = dict()
    try:
        with open("output/ast-map", "r", errors='replace') as ast_map_file:

            map_line = ast_map_file.readline().strip()
            while map_line:
                nodeA, nodeC = clean_parse(map_line, TO)
                
                var_a = id_from_string(nodeA)
                var_a = ast_A[var_a].value_calc(Pa.path + file_a)
                
                var_c = id_from_string(nodeC)
                var_c = ast_C[var_c].value_calc(Pc.path + file_c)
                
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

    with open("output/var-map", "w", errors='replace') as var_map_file:
        for var_a in variable_mapping.keys():
            var_map_file.write(var_a + " -> " + variable_mapping[var_a] + "\n")

    return variable_mapping

def ASTdump(file, output):
    extra_arg = ""
    if file[-1] == "h":
        extra_arg = " --"
    c = DIFF_SIZE + " -s=" + DIFF_COMMAND + " -ast-dump-json " + \
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
    

def ASTscript(file1, file2, output, only_matches=False):
    extra_arg = ""
    if file1[-2:] == ".h":
        extra_arg = " --"
    c = DIFF_SIZE + " -s=" + DIFF_COMMAND + " -dump-matches " + \
        file1 + " " + file2 + extra_arg + " 2> output/errors_clang_diff "
    if only_matches:
        c += "| grep '^Match ' "
    c += " > " + output
    exec_com(c, True)
    

def inst_comp(i):
    return order.index(i)
    
    
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
    
    if instruction == UPDATE:
        nodeC = inst[1]
        nodeD = inst[2]
        c = UPDATE + " " + nodeC.simple_print() + TO + nodeD.simple_print()
            
    elif instruction == DELETE:
        nodeC = inst[1]
        c = DELETE + " " + nodeC.simple_print()
        
    elif instruction == MOVE:
        nodeD1 = inst[1].simple_print()
        nodeD2 = inst[2].simple_print()
        pos = str(inst[3])
        c = MOVE + " " + nodeD1 + INTO + nodeD2 + AT + pos
    
    elif instruction == INSERT:
        nodeB = inst[1].simple_print()
        nodeC = inst[2].simple_print()
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


def gen_edit_script(file_a, file_b, output):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Print.blue("Generating edit script: " + name_a + TO + name_b + "...")
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
            if len(line) > 3 and line[0] == UPDATE and line[1] == AND and \
               line[2] == MOVE:
                instruction = UPDATEMOVE
                content = " ".join(line[3:])
                
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
            # Update nodeA into matching node in B and move into nodeB at pos
            elif instruction == UPDATEMOVE:
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
    return instruction_AB, inserted_B, match_BA
    
def gen_temp_json(file_a, file_b, file_c):
    Print.blue("Generating JSON temp files for each pertinent file...")
    ASTlists = dict()
    try:
        gen_json(file_a, Pa.name, ASTlists)
        gen_json(file_b, Pb.name, ASTlists)
        gen_json(file_c, Pc.name, ASTlists)
    except Exception as e:
        err_exit(e, "Error parsing with crochet-diff. Did you bear make?")
    return ASTlists
    
def simplify_patch(instruction_AB, match_BA, ASTlists):
    modified_AB = []
    inserted = []
    Print.white("Original patch from Pa to Pb")
    for i in instruction_AB:
        inst = i[0]
        if inst == DELETE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[Pa.name][nodeA]
            Print.white("\t" + DELETE + " - " + str(nodeA))
            modified_AB.append((DELETE, nodeA))
        elif inst == UPDATE:
            nodeA = id_from_string(i[1])
            nodeA = ASTlists[Pa.name][nodeA]
            nodeB = id_from_string(i[2])
            nodeB = ASTlists[Pb.name][nodeB]
            Print.white("\t" + UPDATE + " - " + str(nodeA) + " - " + \
                        str(nodeB))
            modified_AB.append((UPDATE, nodeA, nodeB))
        elif inst == MOVE:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Pb.name][nodeB2]
            pos = i[3]
            Print.white("\t" + MOVE + " - " + str(nodeB1) + " - " + \
                        str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((MOVE, nodeB1, nodeB2, pos))
            else:
                if i[1] in match_BA.keys():
                    nodeA = match_BA[i[1]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[Pa.name][nodeA]
                    modified_AB.append((DELETE, nodeA))
                else:
                    Print.yellow("Warning: node " + str(nodeB1) + \
                                 "could not be matched. " + \
                                 "Skipping MOVE instruction...")
                    Print.yellow(i)
        elif inst == UPDATEMOVE:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Pb.name][nodeB2]
            pos = i[3]
            Print.white("\t" + UPDATEMOVE + " - " + str(nodeB1) + " - " + \
                        str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((UPDATEMOVE, nodeB1, nodeB2, pos))
            else:
                if i[1] in match_BA.keys():
                    nodeA = match_BA[i[1]]
                    nodeA = id_from_string(nodeA)
                    nodeA = ASTlists[Pa.name][nodeA]
                    modified_AB.append((DELETE, nodeA))
                else:
                    Print.yellow("Warning: node " + str(nodeB1) + \
                                 "could not be matched. " + \
                                 "Skipping MOVE instruction...")
                    Print.yellow(i)            
        elif inst == INSERT:
            nodeB1 = id_from_string(i[1])
            nodeB1 = ASTlists[Pb.name][nodeB1]
            nodeB2 = id_from_string(i[2])
            nodeB2 = ASTlists[Pb.name][nodeB2]
            pos = i[3]
            Print.white("\t" + INSERT + " - " + str(nodeB1) + " - " + \
                        str(nodeB2) + " - " + str(pos))
            inserted.append(nodeB1)
            if nodeB2 not in inserted:
                modified_AB.append((INSERT, nodeB1, nodeB2, pos))
    return modified_AB
    
def remove_overlapping_delete(modified_AB):
    reduced_AB = set()
    n_i = len(modified_AB)
    for i in range(n_i):
        inst1 = modified_AB[i]
        if inst1[0] == DELETE:
            for j in range(i+1, n_i):
                inst2 = modified_AB[j]
                if inst2[0] == DELETE:
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
        if inst1 == INSERT or inst1 == MOVE or inst1 == UPDATEMOVE:
            node_into_1 = modified_AB[i][2]
            k = i+1
            for j in range(i+1, len(modified_AB)):
                k = j
                inst2 = modified_AB[j][0]
                if inst2 != INSERT and inst2 != MOVE:
                    k -= 1
                    break
                node_into_2 = modified_AB[j][2]
                if node_into_1 != node_into_2:
                    k -= 1
                    break
                pos_at_1 = int(modified_AB[j-1][3])
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
        if inst == DELETE:
            nodeA = i[1].simple_print()
            instruction_AB.append((DELETE, nodeA))
        elif inst == UPDATE:
            nodeA = i[1].simple_print()
            nodeB = i[2].simple_print()
            instruction_AB.append((UPDATE, nodeA, nodeB))
        elif inst == INSERT:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((INSERT, nodeB1, nodeB2, pos))
        elif inst == MOVE:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((MOVE, nodeB1, nodeB2, pos))
        elif inst == UPDATEMOVE:
            nodeB1 = i[1].simple_print()
            nodeB2 = i[2].simple_print()
            pos = int(i[3])
            instruction_AB.append((UPDATEMOVE, nodeB1, nodeB2, pos))    
    return instruction_AB
    
def retrieve_matches():
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
    return match_AC

#node is from the patched program
def findCandidateNode(nodeRef, ASTlists):
    nodeId = getId(nodeRef)
    nodeType = getType(nodeRef)
    node = ASTlists[Pc.name][nodeId]
    print(Pc.name)
    print(node)
    function_c = Pc.funcs[Pc.path + file_c][f_c]
   
    if nodeA in match_AC.keys():
        nodeC = match_AC[nodeA]
        nodeC = id_from_string(nodeC)
        nodeC = ASTlists[Pc.name][nodeC]
        

    
def transform_script(instruction_AB, inserted_B, ASTlists, match_AC, match_BA):
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
                nodeD = id_from_string(nodeB)
                nodeD = ASTlists[Pb.name][nodeD]
                nodeC = findCandidateNode(nodeA, ASTlists)
                if nodeC == null:
                    Print.yellow("Warning: Match for " + str(nodeA) +  "not found. Skipping UPDATE instruction.")
                else:
                    nodeC.line = nodeC.parent.line
                    instruction_CD.append((UPDATE, nodeC, nodeD))  
                
            except Exception as e:
                err_exit(e, "Something went wrong with UPDATE.")

        # Delete nodeA -> Delete nodeC
        elif instruction == DELETE:
            try:
                nodeA = i[1]
                nodeC = "?"
                if nodeA in match_AC.keys():
                    nodeC = match_AC[nodeA]
                    nodeC = id_from_string(nodeC)
                    nodeC = ASTlists[Pc.name][nodeC]
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
                        nodeC1 = id_from_string(nodeC1)
                        nodeC1 = ASTlists[Pc.name][nodeC1]
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
                        nodeC2 = id_from_string(nodeC2)
                        nodeC2 = ASTlists[Pc.name][nodeC2]
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
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = ASTlists[Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos-1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in match_BA.keys():
                            nodeA2_l = match_BA[nodeB2_l]
                            if nodeA2_l in match_AC.keys():
                                nodeC2_l = match_AC[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = ASTlists[Pc.name][nodeC2_l]
                                if nodeC2_l in nodeC2.children:
                                    pos = nodeC2.children.index(nodeC2_l)
                                    pos += 1
                                else:
                                    Print.yellow("Node not in children.")
                                    Print.yellow(nodeC2_l)
                                    Print.yellow([i.simple_print() for i in
                                                  nodeC2.children])
                            else:
                                Print.yellow("Failed at locating match" + \
                                             " for " + nodeA2_l)
                                Print.yellow("Trying to get pos anyway.")
                                # This is more likely to be correct
                                nodeA2_l = id_from_string(nodeA2_l)
                                nodeA2_l = ASTlists[Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                        else:
                            Print.yellow("Failed at match for child.")
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
        
        # Update nodeA and move to nodeB at pos -> Move nodeC to nodeD at pos
        elif instruction == UPDATEMOVE:
            
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
                        nodeC1 = ASTlists[Pc.name][nodeC1]
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
                        nodeC2 = id_from_string(nodeC2)
                        nodeC2 = ASTlists[Pc.name][nodeC2]
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
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = ASTlists[Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos-1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in match_BA.keys():
                            nodeA2_l = match_BA[nodeB2_l]
                            if nodeA2_l in match_AC.keys():
                                nodeC2_l = match_AC[nodeA2_l]
                                nodeC2_l = id_from_string(nodeC2_l)
                                nodeC2_l = ASTlists[Pc.name][nodeC2_l]
                                if nodeC2_l in nodeC2.children:
                                    pos = nodeC2.children.index(nodeC2_l)
                                    pos += 1
                                else:
                                    Print.yellow("Node not in children.")
                                    Print.yellow(nodeC2_l)
                                    Print.yellow([i.simple_print() for i in
                                                  nodeC2.children])
                            else:
                                Print.yellow("Failed at locating match" + \
                                             " for " + nodeA2_l)
                                Print.yellow("Trying to get pos anyway.")
                                # This is more likely to be correct
                                nodeA2_l = id_from_string(nodeA2_l)
                                nodeA2_l = ASTlists[Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                        else:
                            Print.yellow("Failed at match for child.")
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
                            instruction_CD.append((UPDATEMOVE, nodeC1, nodeC2,
                                                   pos))
                        inserted_D.append(nodeC1)
                        
                    else:
                        Print.yellow("Could not find match for node. " + \
                                     "Ignoring UPDATEMOVE operation. (D)")
                else:
                    Print.yellow("Could not find match for node. " + \
                                 "Ignoring UPDATEMOVE operation. (C)")
            except Exception as e:
                err_exit(e, "Something went wrong with UPDATEMOVE.")

        # Insert nodeB1 to nodeB2 at pos -> Insert nodeD1 to nodeD2 at pos
        elif instruction == INSERT:
            try:
                nodeB1 = i[1]
                nodeB2 = i[2]
                pos = int(i[3])
                nodeD1 = id_from_string(nodeB1)
                nodeD1 = ASTlists[Pb.name][nodeD1]
                nodeD2 = id_from_string(nodeB2)
                nodeD2 = ASTlists[Pb.name][nodeD2]
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
                        nodeD2 = ASTlists[Pc.name][nodeD2]
                elif nodeB2 in match_BD.keys():
                    nodeD2 = match_BD[nodeB2]
                else:
                    Print.yellow("Warning: node for insertion not" + \
                                 " found. Skipping INSERT operation.")
                
                try:
                    true_B2 = id_from_string(nodeB2)
                    true_B2 = ASTlists[Pb.name][true_B2]
                    if pos != 0:
                        nodeB2_l = true_B2.children[pos-1]
                        nodeB2_l = nodeB2_l.simple_print()
                        if nodeB2_l in match_BA.keys():
                            nodeA2_l = match_BA[nodeB2_l]
                            if nodeA2_l in match_AC.keys():
                                nodeD2_l = match_AC[nodeA2_l]
                                nodeD2_l = id_from_string(nodeD2_l)
                                nodeD2_l = ASTlists[Pc.name][nodeD2_l]
                                if nodeD2_l in nodeD2.children:
                                    pos = nodeD2.children.index(nodeD2_l)
                                    pos += 1
                                else:
                                    Print.yellow("Node not in children.")
                                    Print.yellow(nodeD2_l)
                                    Print.yellow([i.simple_print() for i in
                                                  nodeD2.children])
                            else:
                                Print.yellow("Failed at locating match" + \
                                             " for " + nodeA2_l)
                                Print.yellow("Trying to get pos anyway.")
                                # This is more likely to be correct
                                nodeA2_l = id_from_string(nodeA2_l)
                                nodeA2_l = ASTlists[Pa.name][nodeA2_l]
                                parent = nodeA2_l.parent
                                if parent != None:
                                    pos = parent.children.index(nodeA2_l)
                                    pos += 1
                                
                        else:
                            Print.yellow("Failed at match for child.")
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
    return instruction_CD


def Htransplantation(to_patch):
    for (file_a, file_c, var_map) in to_patch:
        file_b = file_a.replace(Pa.path, Pb.path)
        if not os.path.isfile(file_b):
            err_exit("Error: File not found.", file_b)
            
        # Generate edit scritps for diff and matching
        gen_edit_script(file_a, file_b, "diff_script_AB")
        gen_edit_script(file_a, file_c, "diff_script_AC")
        
        Print.blue("Generating final edit script for " + file_c.split("/")[-1])
        # Write patch properly
        instruction_AB, inserted_B, match_BA = get_instructions()
        # Generate AST as json files
        ASTlists = gen_temp_json(file_a, file_b, file_c)
        # Simplify instructions to a smaller representative sequence of them
        modified_AB = simplify_patch(instruction_AB, match_BA, ASTlists)
        #Sort in reverse order and depending on instruction for application
        modified_AB.sort(key=cmp_to_key(order_comp))
        # Delete overlapping DELETE operations
        #modified_AB = remove_overlapping_delete(modified_AB)
        # Adjusting position for MOVE and INSERT operations
        #modified_AB = adjust_pos(modified_AB)
        # Printing modified simplified script
        Print.green("Modified simplified script:")
        for j in [" - ".join([str(k) for k in i]) for i in modified_AB]:
            Print.green("\t" + j)
        # We rewrite the instruction as a script (str) instead of nodes
        instruction_AB = rewrite_as_script(modified_AB)
        # We get the matching nodes from Pa to Pc into a dict
        match_AC = retrieve_matches()
        # Transform instructions into ones pertinent to Pc nodes
        instruction_CD = transform_script(instruction_AB, inserted_B, ASTlists,
                                          match_AC, match_BA)
        # Write patch script properly and print in on console
        Print.green("Proposed patch from Pc to Pd")
        for i in instruction_CD:
            patch_instruction(i)
        # Apply the patch (it runs with the script)
        patch(file_a, file_b, file_c)
  
def Ctransplantation(to_patch):
    for (vec_f_a, vec_f_c, var_map) in to_patch:
        try:
            vec_f_b_file = vec_f_a.file.replace(Pa.path, Pb.path)
            if vec_f_b_file not in Pb.funcs.keys():
                err_exit("Error: File not found among affected.", vec_f_b_file)
            if vec_f_a.function in Pb.funcs[vec_f_b_file].keys():
                vec_f_b = Pb.funcs[vec_f_b_file][vec_f_a.function]
            else:
                err_exit("Error: Function not found among affected.",
                         vec_f_a.function, vec_f_b_file,
                         Pb.funcs[vec_f_b_file].keys())
        except Exception as e:
            err_exit(e, vec_f_b_file, vec_f_a, Pa.path, Pb.path,
                     vec_f_a.function)
        
        # Generate edit scritps for diff and matching
        gen_edit_script(vec_f_a.file, vec_f_b.file, "diff_script_AB")
        gen_edit_script(vec_f_a.file, vec_f_c.file, "diff_script_AC")
                      
        Print.blue("Generating final edit script for " + Pc.name)
        # Write patch properly
        instruction_AB, inserted_B, match_BA = get_instructions()
        # Generate AST as json files
        ASTlists = gen_temp_json(vec_f_a.file, vec_f_b.file, vec_f_c.file)
        # Simplify instructions to a smaller representative sequence of them
        modified_AB = simplify_patch(instruction_AB, match_BA, ASTlists)
        #Sort in reverse order and depending on instruction for application
        modified_AB.sort(key=cmp_to_key(order_comp))
        # Delete overlapping DELETE operations
        #modified_AB = remove_overlapping_delete(modified_AB)
        # Adjusting position for MOVE and INSERT operations
        # modified_AB = adjust_pos(modified_AB)
        # Printing modified simplified script
        Print.green("Modified simplified script:")
        for j in [" - ".join([str(k) for k in i]) for i in modified_AB]:
            Print.green("\t" + j)
        # We rewrite the instruction as a script (str) instead of nodes
        instruction_AB = rewrite_as_script(modified_AB)
        # We get the matching nodes from Pa to Pc into a dict
        match_AC = retrieve_matches()
        # Transform instructions into ones pertinent to Pc nodes
        instruction_CD = transform_script(instruction_AB, inserted_B, ASTlists,
                                          match_AC, match_BA)
        # Write patch script properly and print in on console
        Print.green("Proposed patch from Pc to Pd")
        for i in instruction_CD:
            patch_instruction(i)
        # Apply the patch (it runs with the script)
        patch(vec_f_a.file, vec_f_b.file, vec_f_c.file)
        
def patch(file_a, file_b, file_c):
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
    c += PATCH_COMMAND + " -s=" + PATCH_SIZE + \
         " -script=output/script -source=" + file_a + \
         " -destination=" + file_b + " -target=" + file_c
    if file_c[-1] == "h":
        c += " --"
    c += " 2> output/errors > " + output_file + "; "
    c += "cp " + output_file + " " + file_c
    exec_com(c)
    # We fix basic syntax errors that could have been introduced by the patch
    c2 = SYNTAX_CHECK_COMMAND + "-fixit " + file_c
    if file_c[-1] == "h":
        c2 += " --"
    c2 += " 2> output/syntax_errors"
    exec_com(c2)
    # We check that everything went fine, otherwise, we restore everything
    try:
        c3 = SYNTAX_CHECK_COMMAND + file_c
        if file_c[-1] == "h":
            c3 += " --"
        exec_com(c3)
    except Exception as e:
        Print.red("Clang-check could not repair syntax errors.")
        restore_files()
        err_exit(e, "Crochet failed.")
    # We format the file to be with proper spacing (needed?)
    c4 = STYLE_FORMAT_COMMAND + file_c
    if file_c[-1] == "h":
        c4 += " --"
    c4 += " > " + output_file + "; "
    c4 += "cp " + output_file + " " + file_c + ";"
    exec_com(c4)
    
    # We rename the script so that it won't be there for other files
    c5 = "mv output/script output/" + str(n_changes) + "_script"
    exec_com(c5)
    
    
def restore_files():
    global changes
    Print.yellow("Restoring files...")
    for file in changes.keys():
        backup_file = changes[file]
        c = "cp Backup_Folder/" + backup_file + " " + file
        exec_com(c)
    Print.yellow("Files restored")


def show_patch():
    Print.yellow("Original Patch")

    Print.yellow("Generated Patch")



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
            err_exit("Crochet failed at patching. Project still crashed" + \
                     "after changes. Exiting.")
    # TODO: Remove this part when we don't care anymore

    show_patch()
    restore_files()


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Print.title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Print.rose("Successful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Print.red("Crash during " + description + ", after " + duration + " seconds.")
        err_exit(e, "Unexpected error during " + description + ".")
    return result
              
              
def run_patchweave():
    global Pa, Pb, Pc

    Print.start()
    start_time = time.time()
    
    # Prepare projects directories by getting paths and cleaning residual files
    initialization_start_time = time.time()
    safe_exec(initialize, "projects initialization and cleaning")
    initialization_duration = str(time.time() - initialization_start_time)

    function_identification_start_time = time.time()
    # Generates vectors for pertinent functions (modified from Pa to Pb)
    safe_exec(gen_diff, "search for affected functions and vector generation")
    # Generates vectors for all functions in Pc
    safe_exec(gen_ASTs, "vector generation for functions in Pc")
    # Pairwise vector comparison for matching
    patch_for_header_files = safe_exec(compare_H, "pairwise vector comparison for matching")
    patch_for_c_files = safe_exec(compare_C, "pairwise vector comparison for matching")
    function_identification_duration = str(function_identification_start_time - time.time())

    transplantation_start_time = time.time()
    # Using all previous structures to transplant patch
    safe_exec(Htransplantation, "patch transplantation", patch_for_header_files)
    safe_exec(Ctransplantation, "patch transplantation", patch_for_c_files)
    transplantation_duration = str(time.time() - transplantation_start_time)

    # Verification by compiling and re-running crash
    safe_exec(verification, "program verification")
    
    # Final clean
    Print.title("Cleaning residual files generated by Crochet...")
    
    # Final running time and exit message
    run_time = str(time.time() - start_time)
    Print.exit_msg(run_time, initialization_duration, function_identification_duration, transplantation_duration)
    
    
if __name__ == "__main__":
    try:
        run_patchweave()
    except KeyboardInterrupt as e:
        err_exit("Program Interrupted by User")
