import sys
import os
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
            start = line[1].split("-")[0]
            end = line[1].split("-")[1]
            function_range[function_name] = dict()
            function_range[function_name]['start'] = int(start)
            function_range[function_name]['end'] = int(end)
            line = range_file.readline().strip().split(":")
    return function_range
    
# TODO: Have a look at this
'''def generate_ast_dump(project):
    command = "clang -Xclang -ast-dump -fsyntax-only -fno-color-diagnostics "
    command += str(source_file.filePath)
    command += " | grep -P '(Function|Var)Decl' "
    command += "> " + output_path + "/" + "declarations.txt"


def generate_variable_slices(project):
    return
    
def generate_deckard_vectors(project):

    return
'''

def generate_patch_slices():
    for patched_file, patched_file_info in diff_info.items():
        for function_name, var_list in patched_file_info.items():
            file_path = project_A["dir_path"] + patched_file
            slice_file_path = project_A["output_dir"] + patched_file
            slice_command = "frama-c -main " + function_name
            slice_command += " -slice-value='" + var_list + "' " + file_path
            slice_command += " -then-on 'Slicing export' -print"
            slice_command +=  "| sed -e '1,/* Generated /d'"
            slice_command += " > " + slice_file_path
            os.system(slice_command)


def get_diff_info():
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
            diff_line_list_command = "diff " + project_A["dir_path"]
            diff_line_list_command += file + " " + project_B["dir_path"]
            diff_line_list_command += file + " | grep '^[1-9]'"
            diff_line_list_command += "> diff-lines"
            os.system(diff_line_list_command)
            path = diff_file.readline().strip()
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
                        for f_name, lrange in f_range.items():
                            if lrange['start'] <= i <= lrange['end']:
                                if f_name not in affected_function_list:
                                    affected_function_list[f_name] = lrange
                    line = str(diff_line.readline())
            diff_info[file] = affected_function_list


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
        while(len(line) == 3):
            file, f, lines = line
            start, end = lines.split("-")
            vecgen(path, file, f, start, end)
            line = p.readline().strip().split(":")

def run():
    # Check that we have Pa, Pb and Pc
    if len(sys.argv) < 4:
        print("Insufficient arguments")
        exit(-1)
        
    # Define directories
    load_projects()
    
    # Obtain diff in file diff_funcs with format file:function:start-end
    get_diff_info()
    with open('diff_funcs', 'w') as file:
        for file_name, function_list in diff_info.items():
            for f_name, lrange in function_list.items():
                file.write(file_name + ":"+ f_name + ":" + 
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



if __name__=="__main__":
    run()
    clean()
    
    
    
        