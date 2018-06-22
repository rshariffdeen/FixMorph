from __future__ import print_function, division
import time
import subprocess as sub
import docker
import os
import sys
import shutil

project_path = ''
output_dir = "crochet-output/"
script_dir = "scripts/"
build_script = "build_script.sh"
klee_function_script = "klee_function.sh"
docker_client = docker.from_env()
klee_docker_image = "rshariffdeen/klee:crochet"
crochet_container = ""
original_source_code = ""
variable_list = dict()


def setup_docker_environment(dir_path):
    global crochet_container
    if not docker_client.images.get(klee_docker_image):
        docker_client.images.pull(klee_docker_image)

    try:
        if docker_client.containers.get("crochet"):
            crochet_container = docker_client.containers.get("crochet")
            print("crochet container already running...")

    except:
        docker_volume_map = dict()
        docker_volume_map[dir_path] = dict()
        docker_volume_map[dir_path]['bind'] = "/project"
        docker_volume_map[dir_path]['mode'] = "rw"
        docker_client.containers.run(klee_docker_image, command="", detach=True, tty=True, name="crochet", volumes=docker_volume_map)
        crochet_container = docker_client.containers.get("crochet")


    #klee_command = "docker run -d --name crochet -v" + dir_path + ":/project " + klee_docker_image
    #exec_command(klee_command)


def clean_docker_environment():
    return


def initialize_project(dir_path, var_list, binary_path):
    global project_path, variable_list
    project_path = dir_path
    variable_list = var_list
    build_project(binary_path.split('/')[-1])
    return


def exec_command(command):
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    output, errors = p.communicate()

    if p.returncode != 0:
        print ("ERROR")
        print(errors)
        exit(-1)
    return output


def build_project(target):

    if os.path.isdir(project_path + "/crochet"):
        print("llvm compilation detected ..")
        return
    else:
        start_time = time.time()
        print("compiling project for symbolic execution..")
        if os.path.isfile(script_dir + build_script):
            shutil.copy(script_dir + build_script, project_path)
        build_command = "docker exec crochet bash /project/" + build_script + " " + target
        exec_command(build_command)
        os.remove(project_path + build_script)
        end_time = time.time()
        print("\tcompilation finished after " + str(end_time - start_time) + " seconds")


def generate_klee_code(variable_info, is_symbolic):

    if is_symbolic:
        klee_code = "klee_make_symbolic(&" + \
                    variable_info['name'] + \
                    ", sizeof(" + variable_info['name'] + \
                    "), \"" + variable_info['name'] + \
                    + "\");"
    else:
        klee_code = variable_info['type'] + "crochet_" + variable_info['name'].replace(".", "_") + ";"
        klee_code += "klee_make_symbolic(&crochet_" + variable_info['name'].replace(".", "_") + \
                     ", sizeof(crochet_" + variable_info['name'].replace(".", "_") + \
                     "), \"" + variable_info['name'] + "\");"
        klee_code += "klee_assume(crochet_" + variable_info['name'].replace(".", "_") + \
                     " == " + variable_info['name'] + ");"

    return klee_code


def instrument_concolic_execution(source_path, variable_list, function_start_line):
    global original_source_code
    with open(source_path, "rw") as source_file:
        original_source_code = source_file.readlines()
        source_lines = list(original_source_code)
        for variable, var_info in variable_list.iteritems():
            klee_code = generate_klee_code(var_info, False)
            if var_info['line-number']:
                source_lines.insert(int(var_info['line-number']), klee_code)
            else:
                source_lines.insert(function_start_line, klee_code)
        source_file.seek(0)
        source_file.truncate()
        source_file.writelines(source_lines)
    return


def instrument_symbolic_execution(source_path, function_start_line):
    global original_source_code
    with open(project_path + source_path, "rw+") as source_file:
        original_source_code = source_file.readlines()
        source_lines = list(original_source_code)
        for variable in variable_list:
            klee_code = generate_klee_code(variable, False)
            if variable['line-number']:
                source_lines.insert(int(variable['line-number']), klee_code)
            else:
                source_lines.insert(function_start_line, klee_code)
        source_file.seek(0, 0)
        source_file.truncate()
        source_file.writelines(source_lines)
    return


def invoke_klee(binary_path, function_name):
    print("starting klee symbolic execution")
    start_time = time.time()
    relative_directory_of_binary = binary_path.rsplit('/', 1)[0]
    binary_name = binary_path.split('/')[-1]
    directory_of_binary = project_path + "crochet/" + relative_directory_of_binary
    docker_binary_directory = "/project/crochet/" + relative_directory_of_binary
    if os.path.isfile(script_dir + klee_function_script):
        shutil.copy(script_dir + klee_function_script, directory_of_binary)

    docker_command = "bash /project/crochet/" + relative_directory_of_binary + "/" + klee_function_script \
                     + " " + docker_binary_directory + " " + binary_name + " " + function_name
    #print(docker_command)
    crochet_container.exec_run(docker_command)
    #os.remove(directory_of_binary + "/" + klee_function_script)
    end_time = time.time()
    print("\tsymbolic execution finished after " + str(end_time - start_time) + " seconds")


def summarise_symbolic_expressions():

    return


def run_klee(project_path, source_path, binary_path, function_info, variable_list):
    setup_docker_environment(project_path)
    start_time = time.time()
    initialize_project(project_path, variable_list, binary_path)
    instrument_symbolic_execution(source_path, function_info['start-line'])
    invoke_klee(binary_path, function_info['name'])
    summarise_symbolic_expressions()
    end_time = time.time()
    print("klee finished after " + str(end_time - start_time) + "seconds.")


if __name__ == "__main__":
    dir_path = "/home/ridwan/workspace/research-work/patch-transplant/data-set/reproducible/mysql/mysql-5.5.60/"
    source_path = "client/mysql_upgrade.c"
    binary_path = "client/mysql_upgrade"
    function_info = {"name": "free_used_memory", "start-line": 162}

    variable_list = list()

    var_a = {"name": "defaults_argv", "type": "char **", "line-number": ""}

    var_b = {"name": "ds_args.str", "type": "char *", "line-number": ""}
    var_c = {"name": "ds_args.length", "type": "size_t ", "line-number": ""}
    var_d = {"name": "ds_args.max_length", "type": "size_t ", "line-number": ""}
    var_e = {"name": "ds_args.alloc_increment", "type": "size_t ", "line-number": ""}

    var_f = {"name": "conn_args.str", "type": "char *", "line-number": ""}
    var_g = {"name": "conn_args.length", "type": "size_t ", "line-number": ""}
    var_h = {"name": "conn_args.max_length", "type": "size_t ", "line-number": ""}
    var_i = {"name": "conn_args.alloc_increment", "type": "size_t ", "line-number": ""}

    variable_list.append(var_a)
    variable_list.append(var_b)
    variable_list.append(var_c)
    variable_list.append(var_d)
    variable_list.append(var_e)
    variable_list.append(var_f)
    variable_list.append(var_g)
    variable_list.append(var_h)
    variable_list.append(var_i)

    run_klee(dir_path, source_path, binary_path, function_info, variable_list)
