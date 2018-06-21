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

def initialize_project(dir_path):
    global project_path
    project_path = dir_path
    build_project()
    return


def exec_command(command):
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    output, errors = p.communicate()

    if p.returncode != 0:
        print ("ERROR")
        print(errors)
        exit(-1)
    return output


def build_project():

    if os.path.isdir(project_path + "/crochet"):
        print("llvm compilation detected ..")
        return
    else:
        start_time = time.time()
        print("compiling project for symbolic execution..")
        if os.path.isfile(script_dir + build_script):
            shutil.copy(script_dir + build_script, project_path)
        build_command = "docker exec crochet bash /project/" + build_script
        exec_command(build_command)
        os.remove(project_path + build_script)
        end_time = time.time()
        print("\tcompilation finished after " + str(end_time - start_time) + " seconds")


def instrument_symbolic_execution(source_path):
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


def run_klee(project_path, source_path, binary_path, function_name):
    setup_docker_environment(project_path)
    start_time = time.time()
    initialize_project(project_path)
    instrument_symbolic_execution(source_path)
    invoke_klee(binary_path, function_name)
    summarise_symbolic_expressions()
    end_time = time.time()
    print("klee finished after " + str(end_time - start_time) + "seconds.")


if __name__ == "__main__":
    dir_path = "/home/ridwan/workspace/research-work/patch-transplant/data-set/reproducible/mysql/mysql-5.5.60/"
    source_path = "client/mysql_upgrade.c"
    binary_path = "client/mysql_upgrade"
    function_name = "free_used_memory"
    run_klee(dir_path, source_path, binary_path, function_name)
