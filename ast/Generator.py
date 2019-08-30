# -*- coding: utf-8 -*-

''' Main vector generation functions '''

from common.Utilities import error_exit, execute_command
import Vector
import Parser
from tools import Emitter

crochet_diff = "crochet-diff "
clang_format = "clang-format -style=LLVM "

interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

def gen_vec(proj, proj_attribute, file, f_or_struct, start, end, Deckard=True):
    v = Vector.ASTVector(proj, file, f_or_struct, start, end, Deckard)
    if not v.vector:
        return None
    if file in proj_attribute.keys():
        proj_attribute[file][f_or_struct] = v
    else:
        proj_attribute[file] = dict()
        proj_attribute[file][f_or_struct] = v
    return v

def ASTdump(file, output, h_file=False):
    c = crochet_diff + "-ast-dump-json " + file
    if file[-1] == "h":
        c += " --"
    c += " 2> output/errors_AST_dump > " + output
    a = exec_com(c, False)
    Emitter.warning(a[0])

def gen_json(filepath, h_file=False):
    json_file = filepath + ".AST"
    ASTdump(filepath, json_file, h_file)
    return Parser.AST_from_file(json_file)
    
def llvm_format(file):
    try:
        c = "cp " + file + " output/last.c; "
        exec_com(c, False)
        c = clang_format + file + "> output/temp.c; cp output/temp.c " + file
        exec_com(c, False)
    except Exception as e:
        Emitter.warning(e)
        Emitter.warning("Error in llvm_format with file:")
        Emitter.warning(file)
        Emitter.warning("Restoring and skipping")
        c = "cp output/last.c " + file
        exec_com(c, False)


def parseAST(file_path, project, use_deckard=True, is_header=False):
    llvm_format(file_path)
    # Save functions here
    function_lines = list()
    # Save variables for each function d[function] = "typevar namevar; ...;"
    dict_file = dict()
    try:
        ast = gen_json(file_path, is_header)
    except Exception as exception:
        Emitter.warning("\tFailed parsing AST for file:\n\t\t" + file_path)
        return function_lines, dict_file

    start = 0
    end = 0
    file = file_path.split("/")[-1]
    
    if use_deckard:
        Emitter.grey("\tGenerating vectors for " + file)
        
    if is_header:
        if use_deckard:
            Vector.ASTVector(project, file_path, None, None, None, Deckard=True)
    else:
        function_nodes = []
        root = ast[0]
        root.get_nodes("type", "FunctionDecl", function_nodes)
        #Print.white(function_nodes)
        for node in function_nodes:
            set_struct_nodes = set()
            #Print.yellow(node.file)
            if node.file != None and file == node.file.split("/")[-1]:
                f = node.value.split("(")[0]
                start = int(node.line)
                end = int(node.line_end)
                function_lines.append((f, start, end))
                gen_vec(project, project.functions, file_path, f, start, end, use_deckard)
                structural_nodes = []
                for interesting_type in interesting:
                    node.get_nodes("type", interesting_type, structural_nodes)
                for struct_node in structural_nodes:
                    var = struct_node.value.split("(")
                    var_type = var[-1][:-1]
                    var = var[0]
                    line = var_type + " " + var + ";"
                    if f not in dict_file.keys():
                        dict_file[f] = ""
                    dict_file[f] = dict_file[f] + line
                    set_struct_nodes.add(struct_node.value)

        if use_deckard:
            get_vars(project, file_path, dict_file)
   
    return function_lines, dict_file


def get_vars(proj, file, dict_file):
    for func in dict_file.keys():
        for line in dict_file[func].split(";"):
            if file in proj.functions.keys():
                if func in proj.functions[file].keys():
                    proj.functions[file][func].variables.append(line)
                        

def intersect(start, end, start2, end2):
    return not (end2 < start or start2 > end)
    
                        
def find_affected_funcs(project, source_file, pertinent_lines):
    Emitter.blue("\tProject " + project.name + "...")
    try:
        function_list, definition_list = parseAST(source_file, project, False)
    except Exception as e:
        err_exit(e, "Error in parseAST.")

    for start2, end2 in pertinent_lines:
        for f, start, end in function_list:
            if intersect(start, end, start2, end2):
                if source_file not in project.functions.keys():
                    project.functions[source_file] = dict()
                if f not in project.functions[source_file]:
                    project.functions[source_file][f] = Vector.ASTVector(project, source_file, f, start, end, True)
                    Emitter.success("\t\tFunction successfully found: " + f + \
                               " in " + source_file.replace(project.path,
                                                            project.name + "/"))
                    Emitter.grey("\t\t\t" + f + " " + str(start) + "-" + str(end), False)
                break
    get_vars(project, source_file, definition_list)
    return function_list, definition_list
