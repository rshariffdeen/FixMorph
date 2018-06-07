#! /usr/bin/env python3

from __future__ import print_function, division
from six import iteritems
from ASTParser import transplant, longestSubstringFinder
import os
import computeDistance
import time
import json
import subprocess as sub


path_deckard = "tools/Deckard"
output_dir = "output/"
out_diff_files = output_dir + "diff-files"
out_diff_lines = output_dir + "diff-lines"

project_A = dict()
project_B = dict()
project_C = dict()
proj = [project_A, project_B, project_C]
diff_info = dict()
code_clones = dict()

# TODO: If not used later, remove
def wait_timeout(proc, seconds):
    """Wait for a process to finish, or raise exception after timeout"""
    start = time.time()
    end = start + seconds
    interval = min(seconds/1000.0, 0.25)

    while True:
        result = proc.poll()
        if result is not None:
            return result
        if time.time() >= end:
            proc.kill()
            raise RuntimeError("Process timed out")
        time.sleep(interval)


def exec_command(command):
    #print(command)
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    output, errors = p.communicate()

    if p.returncode != 0:
        print ("ERROR")
        print(errors)
        exit(-1)
    return output


def print_title(title):
    print("\n" + title + "\n" + "-"*50 + "\n")


def csurf_make(proj_dir, proj_name):
    print("Making project with csurf...")
    make_command = "cd " + proj_dir + "; make clean; "
    make_command += "csurf hook-build " + proj_name + " make"
    exec_command(make_command)


def configure_project(project):
    print(project["dir_name"])
    cs_conf_file_path = project["dir_path"] + project["dir_name"] + ".csconf"
    if os.path.isfile(cs_conf_file_path):
        print("Codesurfer project detected ..")
    else:
        print("Configuring project ...")
        with open(cs_conf_file_path, 'w') as conf_file:
            conf_file.write("PRESET_BUILD_OPTIONS = high")

        if os.path.isfile(project["dir_path"] + "CMakeLists.txt"):
            config_command = "cd " + project["dir_path"] + "; cmake ."
            exec_command(config_command)

        elif os.path.isfile(project["dir_path"] + "configure.ac"):
            config_command = "cd " + project["dir_path"] + "; autoreconf -i ; "
            config_command += "./configure"
            exec_command(config_command)

        elif os.path.isfile(project["dir_path"] + "configure"):
            config_command = "cd " + project["dir_path"] + "; make clean ; "
            config_command += "./configure"
            exec_command(config_command)
        csurf_make(project["dir_path"], project["dir_name"])


def generate_ast_map(source_a, source_b):
    common_path = longestSubstringFinder(source_a, source_b).split("/")[:-1]
    common_path = "/".join(common_path)
    ast_diff_command = "docker run -v " + common_path + ":/diff "
    ast_diff_command += " gumtree diff "
    ast_diff_command += source_a.replace(common_path, "/diff") + " "
    ast_diff_command += source_b.replace(common_path, "/diff")
    ast_diff_command += " | grep Match | sed -e 's/GenericString//g' "
    ast_diff_command += "| sed -e 's/Match//g' | sed -e 's/://g' > " + output_dir + "ast-map"
    exec_command(ast_diff_command)


def read_config():
    print_title("Loading configuration")
    config_file = "crochet.conf"
    with open(config_file, 'r') as conf:
        project_line = conf.readline().strip()
        for project in proj:
            source_path = project_line.split("=")[1]
            if not os.path.isdir(source_path):
                print("Source directory not found:\n" + source_path)
            else:
                proj_name = os.path.abspath(source_path).split("/")[-1]
                proj_dir = os.path.abspath(source_path) + "/"
                project["dir_path"] = proj_dir
                project["dir_name"] = proj_name
                project["output_dir"] = "output/" + proj_name
                configure_project(project)
            project_line = conf.readline().strip()


def generate_function_information():
    print_title("Generating line range for functions")
    for project in proj:
        project_dir = project["dir_path"]
        project_name = project['dir_name']
        print(project_name)
        csurf_command = "csurf -nogui -python $PWD/CSParser.py " + project_dir
        csurf_command += " -end-python " + project_dir + project_name
        #print(csurf_command)
        exec_command(csurf_command)


def json_loads_byteified(json_text):
    return _byteify(json.loads(json_text, object_hook=_byteify),
                    ignore_dicts=True)


def isstr(s):
    try:
        # bytestring is for unicode and str in Python2
        return isinstance(s, basestring)
    except NameError:
        # In Python 3, only str exists
        return isinstance(s, str)

        
def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isstr(data):
            return data.encode('utf-8')
    # if this is a list of values, return list of byte-ified values
    elif isinstance(data, list):
        return [_byteify(item, True) for item in data]
    # if this is a dictionary, return dictionary of byte-ified keys and values
    # but only if we haven't already byte-ified it
    elif isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, True): _byteify(value, True)
            for key, value in iteritems(data)
        }
    # if it's anything else, return it in its original form
    return data


def load_function_info():
    print_title("Loading line range for functions")
    for project in proj:
        project_dir = project["dir_path"]
        project_name = project['dir_name']
        print(project_name)
        json_file_path = project_dir + "crochet-output/function-info"
        with open(json_file_path) as file:
            line = file.readline().strip()
            function_info = json_loads_byteified(line)
            project['function-info'] = function_info


def generate_patch_slices():
    for patched_file, patched_file_info in diff_info.items():
        for f_name, variable_list in patched_file_info.items():
            source_file_path = project_A["dir_path"] + "/" + patched_file
            slice_file_path = project_A["output_dir"] + "/" + patched_file
            slice_command = "frama-c -main " + f_name + " -slice-value='"
            slice_command += variable_list + "' " + source_file_path
            slice_command += "  -then-on 'Slicing export' -print "
            slice_command += "| sed -e '1,/* Generated /d'"
            slice_command += " > " + slice_file_path
            exec_command(slice_command)


def get_diff_info():
    diff_file_list_command = "diff -qr --ignore-all-space "
    diff_file_list_command += project_A["dir_path"] + " "
    diff_file_list_command += project_B["dir_path"]
    diff_file_list_command += " | grep  '[A-Za-z0-9_]\.c ' > " + out_diff_files
    exec_command(diff_file_list_command)

    with open(out_diff_files, 'r') as diff_file:
        diff_file_path = str(diff_file.readline().strip())
        while diff_file_path:
            file_name = diff_file_path.split(" and ")[0].split("Files ")[1]
            if file_name  in project_A['function-info']:
                function_range_in_file = project_A["function-info"][file_name]
            else:
                diff_file_path = str(diff_file.readline())
                continue

            file_name = file_name.replace(project_A["dir_path"], '')

            affected_function_list = dict()
            diff_line_list_command = "diff --ignore-all-space " 
            diff_line_list_command += project_A["dir_path"] + file_name + " "
            diff_line_list_command += project_B["dir_path"] + file_name + " "
            diff_line_list_command += "| grep '^[1-9]' > " + out_diff_lines
            exec_command(diff_line_list_command)
            with open(out_diff_lines) as diff_line:
                start = ""
                line = diff_line.readline().strip()
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
                        start, end = start.split(',')
                    # TODO: Check loop, seems inefficient
                    for i in range(int(start), int(end) + 1):
                        for f_name, details in function_range_in_file.items():
                            line_range = details['line-range']
                            if int(line_range['start']) <= i <= int(line_range['end']):
                                if f_name not in affected_function_list:
                                    affected_function_list[f_name] = line_range
                    line = str(diff_line.readline().strip())
            diff_info[file_name] = affected_function_list
            diff_file_path = str(diff_file.readline().strip())


def create_output_directories():
    print_title("Creating output directories")
    if not os.path.isdir(output_dir):
        exec_command("mkdir " + output_dir)
    for project in proj:
        if not os.path.isdir(project["output_dir"]):
            exec_command("mkdir " + project["output_dir"])


# TODO: Modify this function accordingly
def remove_vec_files():
    exec_command("find . -name '*.vec' -exec rm -f {} \;")


def generate_file_list(dir_path, file_type, out_path):
    exec_command("find " + dir_path + " -name '*" + file_type + "' > " + out_path)


# TODO: Modify this function accordingly
def clean():
    exec_command("rm -f vec_a vec_c P_C_files line-function function-range")
    exec_command("rm -f diff_funcs diff-lines a.out")
    remove_vec_files()


def gen_function_vector(source_path, file_name, f_name, start, end):
    file_name = file_name
    file_name = file_name
    file_name = file_name
    instr = path_deckard + "/src/main/cvecgen " + source_path + "/" + file_name
    instr += " --start-line-number " + str(start) + " --end-line-number "
    instr += str(end) + " -o " + source_path
    instr += file_name + "." + f_name + ".vec"
    exec_command(instr)


def generate_vectors_for_functions():
    print_title("Generating Vectors")
    # generate vectors for functions in Pa where there is a diff
    pa_path = project_A['dir_path']
    print("generating for patched functions in " + project_A['dir_name'] + " ...")
    for file_name, function_list in diff_info.items():
        #print ("\t" + file_name)
        for f_name, l_range in function_list.items():
            s_line = str(l_range['start'])
            f_line = str(l_range['end'])
            #print("\t\t\t" + f_name)
            gen_function_vector(pa_path, file_name, f_name, s_line, f_line)

    # generate vectors for all functions in Pc
    print("generating for all functions in " + project_C['dir_name'] + " ...\n")
    pc_path = project_C['dir_path']
    for file_path in project_C['function-info'].keys():
        #print("\t" + file_name)
        file_name = file_path.replace(pc_path, '')
        for f_name, details in project_C['function-info'][file_path].items():
            #print("\t\t" + f_name)
            line_range = details['line-range']
            s_line = line_range['start']
            f_line = line_range['end']
            gen_function_vector(pc_path, file_name, f_name, s_line, f_line)


def detect_matching_function():
    print_title("Matched Functions")
    print("calculating similarity matrix for functions...\n")
    generate_file_list(project_A["dir_path"], ".vec", output_dir + "vec_a")
    generate_file_list(project_C["dir_path"], ".vec", output_dir + "vec_c")
    similarity_matrix = computeDistance.DistanceMatrix(output_dir + "vec_a",
                                                       output_dir + "vec_c")

    for pa_file in similarity_matrix.bests.keys():
        source_a = pa_file[:-4] # Remove .vec
        function_a = source_a.replace(project_A["dir_path"], '').split(".")[-1]
        source_a = source_a.rsplit(".", 2)[0] + ".c"
        print (function_a + " : " + project_A['dir_name'] + "/" + source_a.replace(project_A['dir_path'], ""))
        pc_match_list = similarity_matrix.bests[pa_file]
        for pc_file in pc_match_list:
            source_c = pc_file['path'] + "/" + pc_file['file']
            function_c = pc_file['function']
            print ("\t{0:.8f}".format(pc_file['dist']), function_c + " : " + project_C['dir_name'] + "/" + source_c.replace(project_C['dir_path'], ""))
            var_map = detect_matching_variables(function_a, source_a, function_c, source_c)
            transplant_patch_to_function(function_a, source_a, function_c, source_c, var_map)
        print ("\n")


def generate_variable_slices(function_name, source_file_path, project_source_path):
    print ("slicing function", function_name)
    project_name = os.path.abspath(project_source_path).split("/")[-1]
    csurf_command = "csurf -nogui -python $PWD/CSSlicer.py " + function_name + " " + source_file_path + " " + \
                    " -end-python " + project_source_path + project_name
    exec_command(csurf_command)


def detect_matching_variables(function_a_name, function_a_source_path, function_c_name, function_c_source_path):
    variable_mapping = dict()
    function_b_source_path = function_a_source_path.replace(project_A['dir_path'], project_B['dir_path'])
    generate_ast_map(function_a_source_path, function_c_source_path)

    function_b = project_B["function-info"][function_b_source_path][function_a_name]
    function_c = project_C["function-info"][function_c_source_path][function_c_name]

    variable_list_b = list(function_b['variable-list'])
    variable_list_c = list(function_c['variable-list'])

    for var in variable_list_b:
        if "$return" in var or "$result" in var:
            variable_list_b.remove(var)

    print ("\n\t\tvariable mapping..")
    ast_map = dict()
    with open(output_dir + "/ast-map", "r") as ast_map_file:
        map_line = ast_map_file.readline()
        while map_line:
            var_b = map_line.split(" to ")[0].split("(")[0].replace(" ", "")
            var_c = map_line.split(" to ")[1].split("(")[0].replace(" ", "")
            if var_b in variable_list_b:
                if var_b not in ast_map:
                    ast_map[var_b] = dict()

                if var_c in ast_map[var_b]:
                    ast_map[var_b][var_c] += 1
                else:
                    ast_map[var_b][var_c] = 1
            map_line = ast_map_file.readline()

    # sort match with occurrence count
    for var in ast_map:
        ast_map[var] = sorted(ast_map[var].iteritems(), key=lambda (k,v):(v,k))

    for var in variable_list_b:
        if var in ast_map:
            variable_mapping[str(var)] = str(ast_map[var][0][0])
            variable_list_b.remove(var)

    while len(variable_list_b):
        var_b = variable_list_b.pop()
        for var_c in variable_list_c:
            if str(var_b) == str(var_c):
                if str(function_b['variable-list'][var_b]['type']) == str(function_c['variable-list'][var_c]['type']):
                    #print("\t\t\t" + var_b + " - " + var_c)
                    variable_mapping[str(var_b)] = str(var_c)

    #generate_variable_slices(function_a_name, function_b_source_path, project_B['dir_path'])
    with open(output_dir + "var-map", "w") as var_map_file:
        for var_b, var_c in variable_mapping.iteritems():
            var_map_file.write(var_b + ":" + var_c + "\n")

    return variable_mapping


def transplant_patch_to_function(function_a, source_a, function_c, source_c, var_map):
    print("\t\ttransplanting function diff..")
    source_b = source_a.replace(project_A['dir_path'], project_B['dir_path'])
    transplant(source_a, function_a, source_b, function_a, source_c, function_c, var_map)


def verify_patch():
    print("\t\tverifying patch..")


def run():
    start_time = time.time()
    read_config()
    create_output_directories()
    #generate_function_information()
    load_function_info()
    get_diff_info()
    #generate_vectors_for_functions()
    detect_matching_function()
    verify_patch()

    # generate_file_list(project_A["dir_path"], ".vec", output_dir + "vec_a")
    # generate_file_list(project_C["dir_path"], ".vec", output_dir + "vec_c")
    # similarity_matrix = computeDistance.DistanceMatrix(output_dir + "vec_a",
    #                                                    output_dir + "vec_c")
    # transplant_patch_to_function(similarity_matrix)
    
    end_time = time.time()
    print("Crochet finished after " + str(end_time - start_time) + "seconds.")


    # generate_patch_slices()
    #
    # generate_deckard_vectors(project_A["dir_path"])
    # generate_deckard_vectors(project_C["dir_path"])


if __name__ == "__main__":
    run()
    #clean()


