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


def generate_line_range_per_function_clang(source_file_path):
    command = "clang-7 -Wno-everything -g -Xclang -load -Xclang lib/libCrochetLineNumberPass.so " + source_file_path + " 2> function-range"

def load_projects():
    for i in range(3):
        source_path = sys.argv[i+1]
        if not os.path.isdir(source_path):
            print("source directory not found:\n"+ source_path)
            exit(-1)
        else:
            proj[i]["dir_path"] = os.path.abspath(source_path) + "/"
            proj[i]["dir_name"] = os.path.abspath(source_path).split("/")[-1]
            proj[i]["output_dir"] = "output/" + proj[i]["dir_name"] + "/"
            
            
def get_frange(source_file_path, output_file_path):
    command = "clang-7 -Wno-everything -g -Xclang -load -Xclang "
    command += "lib/libCrochetLineNumberPass.so " + source_file_path
    command += " 2> " + output_file_path
    os.system(command)

def gen_lrange_per_function(source_file_path):
    get_frange(source_file_path, 'function-range')
    function_range = dict()
    with open('function-range', 'r') as range_file:
        line = range_file.readline().strip().split(":")
        while line:
            if not line[0]:
                break
            function_name = line[0]
            start, end = line[1].split("-")
            start = line[1].split("-")[0]
            end = line[1].split("-")[1]
            function_range[function_name] = dict()
            function_range[function_name]['start'] = int(start)
            function_range[function_name]['end'] = int(end)
            line = range_file.readline().strip().split(":")
    return function_range


def generate_line_range_per_function_csurf():
    print "\nGenerating line range for functions\n-------------\n"
    for project in proj:
        project_dir = project["dir_path"]
        project_name = project['dir_name']
        print (project_name)
        csurf_command = "csurf -no-scripting -nogui -python $PWD/CSParser.py " + project_dir + " -end-python " + project_dir + project_name
        exec_command(csurf_command)


def load_line_range_info():
    print "\nLoading line range for functions\n-------------\n"
    for project in proj:
        project_dir = project["dir_path"]
        project_name = project['dir_name']
        print (project_name)
        json_file_path = project_dir + "crochet-output/function-lines"
        with open(json_file_path) as file:
            line = file.readline()
            function_info = json.loads(line)
            project['function-lines'] = function_info


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



def generate_deckard_vectors(project):
    return


def frama_slice(path, file, f, f_vars, output_path):
    command = "frama-c -main " + f + " -slice-value='" + f_vars + "' "
    command += path + file + " -then-on 'Slicing export' -print "
    command += "| sed -e '1,/* Generated /d' "
    output = "_".join([output_path + "/slice", file[:-2],
                            f, f_vars.replace(" ", "-")]) + ".c"
    command += "> " +  output
    print(command)
    os.system(command)

def generate_patch_slices():
    for patched_file, patched_file_info in diff_info.items():
        for function_name, var_list in patched_file_info.items():
            file_path = project_A["dir_path"] + patched_file
            frama_slice(file_path, function_name, var_list)

def get_diff_info():
    diff_file_list_command = "diff -qr " + project_A["dir_path"] + " " + project_B["dir_path"]
    diff_file_list_command += " | grep  '[A-Za-z0-9_]\.c ' > diff-files"
    os.system(diff_file_list_command)
    with open('diff-files') as diff_file:
        diff_file_path = str(diff_file.readline().strip())
        while diff_file_path:
            file_name = diff_file_path.split(" and ")[1].split(" differ")[0].replace(project_B["dir_path"], project_A["dir_path"])

            if hasattr(project_A['function-lines'], file_name):
                function_range_in_file = project_A["function-lines"][file_name]
            else:
                diff_file_path = str(diff_file.readline())
                continue

            file_name = file_name.replace(project_A["dir_path"], '')
            affected_function_list = dict()
            diff_line_list_command = "diff " + project_A["dir_path"] + file_name + " " + project_B[
                "dir_path"] + file_name + " | grep '^[1-9]' > diff-lines"

    diff_file_list_command = "diff -qr " + project_A["dir_path"]
    diff_file_list_command += " " + project_B["dir_path"]
    diff_file_list_command += " | grep -P '[A-Za-z0-9_].c ' > diff-files"
    os.system(diff_file_list_command)
    with open('diff-files', 'r') as diff_file:
        path = diff_file.readline().strip()
        while path:
            file = path.split(" and ")[1].split(" differ")[0]
            file = file.replace(project_B["dir_path"], '')
            f_range = gen_lrange_per_function(project_A["dir_path"] + file)
            affected_function_list = dict()
            diff_line_list_command = "diff " + project_A["dir_path"] + file
            diff_line_list_command += " " + project_B["dir_path"] + file
            diff_line_list_command += " | grep '^[1-9]' > diff-lines"
            os.system(diff_line_list_command)
            path = diff_file.readline().strip()
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
                        for function_name, line_range in function_range_in_file.items():
                            if line_range['start'] <= i <= line_range['end']:
                                if function_name not in affected_function_list:
                                    affected_function_list[function_name] = line_range
                    line = str(diff_line.readline())
            diff_info[file_name] = affected_function_list


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
    instr += " --start-line-number " + start + " --end-line-number " + end
    instr += " -o " + path + "/"
    instr += file + "." + function + "." + start + "-" + end + ".vec"
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
    generate_line_range_per_function_csurf()
    load_line_range_info()
    # Obtain diff in file diff_funcs with format file:function:start-end
    get_diff_info()
    with open('diff_funcs', 'w') as file:
        for file_name, function_list in diff_info.items():
            for f_name, lrange in function_list.items():
                file.write(file_name + ":" + f_name + ":" +
                           str(lrange['start']) + "-" + str(lrange['end']) + "\n")

    # For each file:function:start-end in diff_funcs, we generate a vector
    gen_vectors('diff_funcs', project_A["dir_path"])
    
    

    # Put all .c files of project C in P_C_files
    get_files(project_C["dir_path"], ".c", "P_C_files")

    # For each .c file, we generate a vector for each function in it
    with open('P_C_files', 'r') as b:
        line = b.readline().strip()
        while line:
            if not line[0]:
                break
            path = "/".join(line.split("/")[:-1])
            # Creates line-function with lines with format function:start-end
            get_frange(line, 'line-function')
            # We now explore each function and generate a vector for it
            with open('line-function', 'r') as lf:
                l = lf.readline().strip().split(":")
                while (len(l) == 2):
                    f, lines = l
                    start, end = lines.split("-")
                    vecgen(path, line.split("/")[-1], f, start, end)
                    l = lf.readline().strip().split(":")
            line = b.readline().strip()
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


def test_1():
    path = "samples/programs/insertion-sort/prog-c/"
    file = "insertion-sort.c"
    f = "sort"
    f_vars = "a"
    frama_slice(path, file, f, f_vars, "tests/test_1_output")


if __name__ == "__main__":
    run()
    clean()
    test_1()

