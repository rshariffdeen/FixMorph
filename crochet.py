import sys
import os
import subprocess as sub
import computeDistance

path_deckard = "/home/pedrobw/Deckard"
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
            if not line[0]:
                break
            function_name = line[0]
            start = line[1].split("-")[0]
            end = line[1].split("-")[1]
            function_range[function_name] = dict()
            function_range[function_name]['start'] = int(start)
            function_range[function_name]['end'] = int(end)
            line = range_file.readline().strip().split(":")
    return function_range
    

def generate_ast_dump(project):
    command = "clang -Xclang -ast-dump -fsyntax-only -fno-color-diagnostics "
    command += str(source_file.filePath) + " | grep -P \"(Function|Var)Decl\" > " + output_path + "/" + "declarations.txt"


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
        diff_file_path = str(diff_file.readline().strip())
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
                    if 'd' in line:
                        start = line.split('d')[0]
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
    
def clean():
    os.system("rm -r vec_a vec_c P_C_files line-function function-range diff_funcs diff-files diff-lines a.out")

def run():
    if len(sys.argv) < 4:
        print("Insufficient arguments")
        exit(-1)

    load_projects()
    get_diff_info()
    remove_vec_files()
    with open('diff_funcs', 'w') as file:
        for file_name, function_list in diff_info.items():
            for function_name, line_range in function_list.items():
                file.write(file_name + ":"+ function_name + ":" + str(line_range['start']) + "-" + str(line_range['end']) + "\n")
    with open('diff_funcs', 'r') as a:
        line = a.readline().strip().split(":")
        while (len(line)==3):
            file = line[0]
            f = line[1]
            lines = line[2].split("-")
            start = lines[0]
            end = lines[1]
            #print(project_A["dir_path"], file, lines, start, end)
            vecgen(os.path.abspath(project_A["dir_path"]), file, f, start, end)
            line = a.readline().strip().split(":")
    get_files(project_C["dir_path"], ".c", "P_C_files")
    with open('P_C_files', 'r') as b:
        line = b.readline().strip()
        while line and line[0]:
            instr = "clang-7 -Wno-everything -g -Xclang -load -Xclang "
            instr += "lib/libCrochetLineNumberPass.so " +  line
            instr += " 2> line-function"
            os.system(instr)
            with open('line-function', 'r') as lf:
                l = lf.readline().strip().split(":")
                while (len(l) == 2):
                    f, lines = l
                    start, end = lines.split("-")
                    vecgen(project_C["dir_path"], line.split("/")[-1], f, start, end)
                    l = lf.readline().strip().split(":")
            line = b.readline().strip().split()
    get_files(project_A["dir_path"], ".vec", "vec_a")
    get_files(project_C["dir_path"], ".vec", "vec_c")
    
    distMatrix = computeDistance.DistanceMatrix("vec_a", "vec_c")
    print(distMatrix)
    #print(distMatrix.get_distance_files('/home/pedrobw/Documents/crochet/samples/programs/selection-sort/P_a/prog-a.c.just.10-15.vec', '/home/pedrobw/Documents/crochet/samples/programs/selection-sort/P_c/prog-c.c.sort.11-35.vec'))
    
    # create_output_directories()
    # generate_patch_slices()
    #
    # generate_deckard_vectors(project_A["dir_path"])
    # generate_deckard_vectors(project_C["dir_path"])



if __name__=="__main__":
    run()
    clean()
    
    
    
        