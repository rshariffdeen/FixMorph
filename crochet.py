import sys
import os
import subprocess as sub

project_A = dict()
project_B = dict()
project_C = dict()
proj = [project_A, project_B, project_C]
diff_info = dict()
code_clones = dict()


def load_projects():
    for i in range(3):
        source_path = sys.argv[i+1]
        if not os.path.isdir(source_path):
            print("source directory A not found:\n"+ source_path)
            exit(-1)
        else:
            proj[i]["dir_path"] = os.path.abspath(source_path) + "/"
            proj[i]["dir_name"] = os.path.abspath(source_path).split("/")[-1]
            proj[i]["output_dir"] = "output/" + proj[i]["dir_name"]
            

def cmd_exec(command):
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE)
    output, errors = p.communicate()
    return output


def generate_line_range_per_function(source_file_path):
    command = "clang-7 -Wno-everything -g -Xclang -load -Xclang lib/libCrochetLineNumberPass.so " + source_file_path + " 2> function-range"
    os.system(command)
    function_range = dict()
    with open('function-range', 'r') as range_file:
        line = range_file.readline().strip().split(":")
        while line:
            function_name = line[0]
            start = line[1].split("-")[0]
            end = line[1].split("-")[1]
            print(function_name, start, end)

            function_range[function_name] = dict()
            function_range[function_name]['start'] = int(start)
            function_range[function_name]['end'] = int(end)
            line = range_file.readline().strip().split(":")
    return function_range
    

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
    diff_file_list_command = "diff -qr " + project_A["dir_path"] + " " + project_B["dir_path"]
    diff_file_list_command += " | grep -P '[A-Za-z0-9_].c ' > diff-files"
    os.system(diff_file_list_command)
    with open('diff-files') as diff_file:
        diff_file_path = str(diff_file.readline())
        while diff_file_path:
            file_name = diff_file_path.split(" and ")[1].split(" differ")[0].replace(project_B["dir_path"], '')
            function_range_in_file = generate_line_range_per_function(project_A["dir_path"] + file_name)
            affected_function_list = dict()
            diff_line_list_command = "diff " + project_A["dir_path"] + file_name + " " + project_B["dir_path"]  + file_name + " | grep '^[1-9]' > diff-lines"
            os.system(diff_line_list_command)
            diff_file_path = str(diff_file.readline())
            with open('diff-lines') as diff_line:
                line = str(diff_line.readline())
                while line:
                    if 'c' in line:
                        start = line.split('c')[0]
                        end = start
                    elif 'd' in line:
                        start = line.split('d')[0]
                        end = start
                    elif 'a' in line:
                        start = line.split('a')[0]
                        end = start

                    if ',' in start:
                        end = start.split(',')[1]
                        start = start.split(',')[0]
                    for i in range(int(start), int(end)+1):
                        for function_name, line_range in function_range_in_file.items():
                            if line_range['start'] <= i <= line_range['end']:
                                if function_name not in affected_function_list:
                                    affected_function_list[function_name] = line_range
                    line = str(diff_line.readline())
            diff_info[file_name] = affected_function_list


def create_output_directories():
    os.system("mkdir output")
    os.system("mkdir " + project_A["output_dir"])
    os.system("mkdir " + project_B["output_dir"])
    os.system("mkdir " + project_C["output_dir"])


def run():
    if len(sys.argv) < 4:
        print("Insufficient arguments")
        exit(-1)

    load_projects()
    get_diff_info()

    for file_name, function_list in diff_info.items():
        print(file_name + ":")
        for function_name, line_range in function_list.items():
            print("\t" + function_name + " " + str(line_range['start']) + "-" + str(line_range['end']))

    # create_output_directories()
    # generate_patch_slices()
    #
    # generate_deckard_vectors(project_A["dir_path"])
    # generate_deckard_vectors(project_C["dir_path"])




run()