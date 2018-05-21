import sys
import os
import subprocess as sub

project_A = dict()
project_B = dict()
project_C = dict()
diff_info = dict()
code_clones = dict()


diff_info["sort.c"] = dict()
diff_info["sort.c"]["insertionSort"] = "j,temp,i,k,n,array"


def load_projects():
    source_path_a = sys.argv[1]
    source_path_b = sys.argv[2]
    source_path_c = sys.argv[3]

    if not os.path.isdir(source_path_a):
        print "source directory A not found"
        print source_path_a
        exit(-1)
    else:
        project_A["dir_path"] = os.path.abspath(source_path_a)
        project_A["dir_name"] = os.path.abspath(source_path_a).split("/")[-1]
        project_A["output_dir"] = "output/" + project_A["dir_name"]

    if not os.path.isdir(source_path_b):
        print "source directory B not found"
        print source_path_b
        exit(-1)
    else:
        project_B["dir_path"] = os.path.abspath(source_path_b)
        project_B["dir_name"] = os.path.abspath(source_path_b).split("/")[-1]
        project_B["output_dir"] = "output/" + project_B["dir_name"]

    if not os.path.isdir(source_path_c):
        print "source directory C not found"
        print source_path_c
        exit(-1)
    else:
        project_C["dir_path"] = os.path.abspath(source_path_c)
        project_C["dir_name"] = os.path.abspath(source_path_c).split("/")[-1]
        project_C["output_dir"] = "output/" + project_C["dir_name"]


def cmd_exec(command):
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE)
    output, errors = p.communicate()
    return output


def generate_line_range_per_function(source_file_path):
    command = "clang-7 -Wno-everything -g -Xclang -load -Xclang lib/libCrochetLineNumberPass.so " + source_file_path + " 2> line-function"
    os.system(command)


def generate_ast_dump(project):
    command = "clang -Xclang -ast-dump -fsyntax-only -fno-color-diagnostics " + string(
        source_file.filePath) + " | grep -P \"(Function|Var)Decl\" > " + output_path + "/" + "declarations.txt"



def generate_variable_slices(project):
    return


def generate_patch_slices():
    for patched_file, patched_file_info in diff_info.items():
        for function_name, variable_list in patched_file_info.items():
            source_file_path = project_A["dir_path"] + "/" + patched_file
            slice_file_path = project_A["output_dir"] + "/" + patched_file
            slice_command = "frama-c -main " + function_name + " -slice-value='" + variable_list + "' " + source_file_path
            slice_command += "  -then-on 'Slicing export' -print | sed -e '1,/* Generated /d'"
            slice_command += " > " + slice_file_path
            os.system(slice_command)


def generate_deckard_vectors(project):

    return


def get_diff_info():
    diff_file_list_command = "diff -qr " + project_A["dir_path"] + " " + project_B["dir_path"] + " > diff-files"
    os.system(diff_file_list_command)
    with open('diff-files') as diff_file:
        diff_file_path = str(diff_file.readline())
        while diff_file_path:
            file_name = diff_file_path.split(" and ")[1].split(" differ")[0].replace(project_B["dir_path"], '').replace("/", '')
            diff_line_list_command = "diff " + project_A["dir_path"] + "/" + file_name + " " + project_B["dir_path"] + "/" + file_name + " | grep '^[1-9]' > diff-lines"
            os.system(diff_line_list_command)
            diff_file_path = str(diff_file.readline())
            with open('diff-lines') as diff_line:
                line_range = str(diff_line.readline())
                while line_range:
                    start_line = line_range.split('c')[0]
                    print start_line
                    line_range = str(diff_line.readline())
    exit()


def create_output_directories():
    os.system("mkdir output")
    os.system("mkdir " + project_A["output_dir"])
    os.system("mkdir " + project_B["output_dir"])
    os.system("mkdir " + project_C["output_dir"])


def run():
    if len(sys.argv) < 4:
        print "Insufficient arguments"
        exit(-1)

    load_projects()
    get_diff_info()
    create_output_directories()
    generate_patch_slices()

    generate_deckard_vectors(project_A["dir_path"])
    generate_deckard_vectors(project_C["dir_path"])




run()