import os
import computeDistance
import time
import json
import subprocess as sub


path_deckard = "tools/Deckard"
project_A = dict()
project_B = dict()
project_C = dict()
proj = [project_A, project_B, project_C]
diff_info = dict()
code_clones = dict()


def wait_timeout(proc, seconds):
    """Wait for a process to finish, or raise exception after timeout"""
    start = time.time()
    end = start + seconds
    interval = min(seconds / 1000.0, .25)

    while True:
        result = proc.poll()
        if result is not None:
            return result
        if time.time() >= end:
            proc.kill()
            raise RuntimeError("Process timed out")
        time.sleep(interval)


def exec_command(command):
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    output, errors = p.communicate()
    if errors:
        print errors
        exit(-1)
    return output


def read_config():
    print "Loading configuration\n-------------\n"
    config_file = "crochet.conf"
    with open(config_file, 'r') as conf:
        project_line = conf.readline()
        for i in range(3):
            source_path = project_line.split("=")[1].replace("\n", '')
            if not os.path.isdir(source_path):
                print("source directory not found:\n" + source_path)
            else:
                proj_name = os.path.abspath(source_path).split("/")[-1]
                proj_dir = os.path.abspath(source_path) + "/"
                proj[i]["dir_path"] = proj_dir
                proj[i]["dir_name"] = proj_name
                proj[i]["output_dir"] = "output/" + proj_name

                print proj_name
                if os.path.isfile(proj_dir + proj_name + ".csconf"):
                    print "codesurfer project detected .."
                else:
                    print "configuring project ..."
                    if os.path.isfile(proj_dir + "CMakeLists.txt"):
                        config_command = "cd " + proj_dir + "; cmake ."
                        exec_command(config_command)

                    if os.path.isfile(proj_dir + "configure"):
                        config_command = "cd " + proj_dir + "; make clean ;./configure"
                        exec_command(config_command)

                    print "making project with csurf ..."
                    make_command = "cd " + proj_dir + "; make clean; csurf hook-build " + proj_name + " make"
                    exec_command(make_command)

            project_line = conf.readline()


def generate_function_information():
    print "\nGenerating line range for functions\n-------------\n"
    for project in proj:
        project_dir = project["dir_path"]
        project_name = project['dir_name']
        print (project_name)
        csurf_command = "csurf -nogui -python $PWD/CSParser.py " + project_dir + " -end-python " + project_dir + project_name
        exec_command(csurf_command)


def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )


def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )


def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


def load_function_info():
    print "\nLoading line range for functions\n-------------\n"
    for project in proj:
        project_dir = project["dir_path"]
        project_name = project['dir_name']
        print (project_name)
        json_file_path = project_dir + "crochet-output/function-info"
        with open(json_file_path) as file:
            line = file.readline()
            function_info = json_loads_byteified(line)
            project['function-info'] = function_info


# TODO: Have a look at this
'''def generate_ast_dump(project):
    command = "clang -Xclang -ast-dump -fsyntax-only -fno-color-diagnostics "
    command += str(source_file.filePath)
    command += " | grep -P '(Function|Var)Decl' "
    command += "> " + output_path + "/" + "declarations.txt"


def generate_variable_slices(project):
    return

'''


def generate_patch_slices():
    for patched_file, patched_file_info in diff_info.items():
        for function_name, variable_list in patched_file_info.items():
            source_file_path = project_A["dir_path"] + "/" + patched_file
            slice_file_path = project_A["output_dir"] + "/" + patched_file
            slice_command = "frama-c -main " + function_name + " -slice-value='" + variable_list + "' " + source_file_path
            slice_command += "  -then-on 'Slicing export' -print | sed -e '1,/* Generated /d'"
            slice_command += " > " + slice_file_path
            os.system(slice_command)


def get_diff_info():
    diff_file_list_command = "diff -qr " + project_A["dir_path"] + " " + project_B["dir_path"]
    diff_file_list_command += " | grep  '[A-Za-z0-9_]\.c ' > diff-files"
    os.system(diff_file_list_command)

    with open('diff-files') as diff_file:
        diff_file_path = str(diff_file.readline().strip())
        while diff_file_path:
            file_name = diff_file_path.split(" and ")[1].split(" differ")[0].replace(project_B["dir_path"], project_A["dir_path"])

            if file_name in project_A['function-info']:
                function_range_in_file = project_A["function-info"][file_name]
            else:
                diff_file_path = str(diff_file.readline())
                continue

            file_name = file_name.replace(project_A["dir_path"], '')

            affected_function_list = dict()
            diff_line_list_command = "diff " + project_A["dir_path"] + file_name + " " + project_B[
                "dir_path"] + file_name + " | grep '^[1-9]' > diff-lines"

            os.system(diff_line_list_command)
            with open('diff-lines') as diff_line:
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
                        end = start.split(',')[1]
                        start = start.split(',')[0]

                    for i in range(int(start), int(end) + 1):
                        for function_name, details in function_range_in_file.items():
                            line_range = details['line-range']
                            if line_range['start'] <= i <= line_range['end']:
                                if function_name not in affected_function_list:
                                    affected_function_list[function_name] = line_range
                    line = str(diff_line.readline())
            diff_info[file_name] = affected_function_list
            diff_file_path = str(diff_file.readline().strip())


def create_output_directories():
    os.system("mkdir output")
    for i in range(3):
        os.system("mkdir " + proj[i]["output_dir"])    
    

def remove_vec_files():
    os.system("find . -name '*.vec' -exec rm -f {} \;")


def get_files(dir_path, filetype, output):
    os.system("find " + dir_path + " -name '*" + filetype + "' > " + output)


def vecgen(path, file, function, start, end):
    instr = path_deckard + "/src/main/cvecgen " + path + "/" + file
    instr += " --start-line-number " + str(start) + " --end-line-number " + str(end)
    instr += " -o " + path + "/"
    instr += file + "." + function + "." + str(start) + "-" + str(end) + ".vec"
    print instr
    os.system(instr)


def vecgen_entire(file):
    with open(file, 'r') as f:
        l = str(len(f.readlines()))
    instr = path_deckard + "/src/main/cvecgen " + file
    instr += " --start-line-number 1 --end-line-number " + l
    instr += "-o " + file + ".vec"
    os.system(instr)


def clean():
    os.system("rm -f vec_a vec_c P_C_files line-function function-range")
    os.system("rm -f diff_funcs diff-files diff-lines a.out")
    remove_vec_files()


def gen_vectors(file, path):
    with open(file, 'r') as p:
        line = p.readline().strip().split(":")
        while (len(line) == 3):
            file, f, lines = line
            start, end = lines.split("-")
            vecgen(path, file, f, start, end)
            line = p.readline().strip().split(":")


def run():
    # Define directories
    read_config()
    generate_function_information()
    load_function_info()

    # Obtain diff in file diff_funcs with format file:function:start-end
    get_diff_info()

    with open('diff_funcs', 'w') as file:
        for file_name, function_list in diff_info.items():

            for f_name, lrange in function_list.items():
                file.write(file_name + ":" + f_name + ":" +
                           str(lrange['start']) + "-" + str(lrange['end']) + "\n")

    # For each file:function:start-end in diff_funcs, we generate a vector
    gen_vectors('diff_funcs', project_A["dir_path"])

    for file in project_C['function-info'].keys():
        for function, details in project_C['function-info'][file].items():
            line_range = details['line-range']
            print file, function, line_range
            vecgen("/".join(file.split("/")[:-1]), file.split("/")[-1], function, line_range['start'], line_range['end'])

    get_files(project_A["dir_path"], ".vec", "vec_a")
    get_files(project_C["dir_path"], ".vec", "vec_c")

    distMatrix = computeDistance.DistanceMatrix("vec_a", "vec_c")
    print(distMatrix)

    # Somehow here, we should call some function to generate slices
    '''
    for Pa_file in distMatrix.bests[index].keys():
        # TODO: slices for each variable in that function > slices_Pa_file
        
        for Pc_file in distMatrix.bests[Pa_file]:
            # TODO: slices for each variable in that function > slices_Pc_file
            remove_vec_files()
            vectorgen_entire('slices_Pa_file')
            vectorgen_entire('slices_Pc_file')
            get_files(project_A["dir_path"], ".vec", vec_a)
            get_files(project_C["dir_path"], ".vec", vec_c)
            Pa_Pc_dist = computeDistance.DistanceMatrix("vec_a", "vec_c")
            # We should have a structure we can use to get best matching slices
            print(Pa_Pc_dist)
            # More stuff... e.g. put the object in a structure for future use
    '''


    # create_output_directories()
    # generate_patch_slices()
    #
    # generate_deckard_vectors(project_A["dir_path"])
    # generate_deckard_vectors(project_C["dir_path"])


if __name__ == "__main__":
    run()
    #clean()


