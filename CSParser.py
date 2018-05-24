import cs
import os, signal
import sys
import json

project = ''
proj_dir = ''

function_info = dict()
output_dir = 'crochet-output/'


def initialize_project():
    global project, proj_dir
    project = cs.project.current()
    proj_dir = sys.argv[1]
    return


def create_output_directories():
    if not os.path.isdir(output_dir):
        os.system("mkdir " + output_dir)


def get_function_lines():
    for func in project.procedures():
        function_name = func.name()
        print function_name
        if '#' in function_name:
            continue

        try:
            source_file = func.file_line()
            source_file_path = source_file[0].name()
            if source_file_path not in function_info:
                function_info[source_file_path] = dict()

            start_line = func.entry_point().file_line()[1]
            end_line = func.exit_point().file_line()[1]
            line_range = dict()
            line_range['start'] = str(start_line)
            line_range['end'] = str(end_line)
            function_info[source_file_path][function_name] = line_range

        except:
            print "exception processing system function "


def print_function_lines():
    output_path = output_dir + "/" + "function-lines"
    with open(output_path, 'w') as outfile:
        json.dump(function_info, outfile)


def kill_csruf_shell():
    pstring = "csurf"
    for line in os.popen("ps ax | grep " + pstring + " | grep -v grep"):
        fields = line.split()
        pid = fields[0]
    os.kill(int(pid), signal.SIGKILL)


def run():
    initialize_project()
    create_output_directories()
    get_function_lines()
    print_function_lines()
    #kill_csruf_shell()
    return


run()

