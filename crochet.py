import sys
import os
import subprocess as sub

project_A = dict()
project_B = dict()
project_C = dict()
diff_info = dict()


diff_info["sort.c"] = dict()
diff_info["sort.c"]["function-name"] = "insertionSort"
diff_info["sort.c"]["variable-list"] = "j, temp, i, k, n, array"


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
        project_A["dir_name"] = os.path.dirname(source_path_a)

    if not os.path.isdir(source_path_b):
        print "source directory B not found"
        print source_path_b
        exit(-1)
    else:
        project_B["dir_path"] = os.path.abspath(source_path_b)
        project_B["dir_name"] = os.path.dirname(source_path_b)

    if not os.path.isdir(source_path_c):
        print "source directory C not found"
        print source_path_c
        exit(-1)
    else:
        project_C["dir_path"] = os.path.abspath(source_path_c)
        project_C["dir_name"] = os.path.dirname(source_path_c)


def cmd_exec(command):
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE)
    output, errors = p.communicate()
    return output


def generate_line_range_per_function(source_file_path):
    command = "clang-7 -Wno-everything -g -Xclang -load -Xclang lib/libCrochetLineNumberPass.so " + source_file_path + " > line-function"
    os.system(command)


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


def run():
    if len(sys.argv) < 4:
        print "Insufficient arguments"
        exit(-1)

    load_projects()
   # get_diff_info()


run()