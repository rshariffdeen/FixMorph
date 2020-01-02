#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
from common.Utilities import execute_command, error_exit
from common import Definitions, Values
from tools import Logger, Emitter

CC = "clang"
CXX = "clang++"
C_FLAGS = "-g -O0  -fPIC"
CXX_FLAGS = "-g -O0  -fPIC"
LD_FLAGS = ""


def config_project(project_path, is_llvm, custom_config_command=None):
    dir_command = "cd " + project_path + ";"
    if os.path.exists(project_path + "/" + "aclocal.m4"):
        pre_config_command = "rm aclocal.m4;aclocal"
        execute_command(pre_config_command)

    if custom_config_command is not None:
        if custom_config_command == "skip":
            return
        else:
            if CC == "wllvm":
                custom_config_command = remove_fsanitize(custom_config_command)
                # print(custom_config_command)
            if "--default-cc" in custom_config_command:
                config_command = "CC=" + CC + " "
                config_command += "CXX=" + CXX + " "
                config_command += custom_config_command.replace("--default-cc", "")
            else:
                config_command = custom_config_command + " "
                config_command += "CC=" + CC + " "
                config_command += "CXX=" + CXX + " "

            if "--cc=" in config_command:
                config_command = config_command.replace("--cc=clang-7", "--cc=" + CC)
            # print(config_command)

            config_command = custom_config_command + ' '
            if "cmake" not in custom_config_command:
                if CC == "wllvm":
                    custom_config_command = remove_fsanitize(custom_config_command)
                    # print(custom_config_command)
                config_command += "CC=" + CC + " "
                config_command += "CXX=" + CXX + " "
                if "--cc=" in config_command:
                    config_command = config_command.replace("--cc=clang-7", "--cc=" + CC)
                # print(config_command)

    elif os.path.exists(project_path + "/autogen.sh"):
        config_command = "./autogen.sh;"
        config_command += "CC=" + CC + " "
        config_command += "CXX=" + CXX + " "
        config_command += "./configure "
        config_command += "CFLAGS=" + C_FLAGS + " "
        config_command += "CXXFLAGS=" + CXX_FLAGS

    elif os.path.exists(project_path + "/configure"):
        config_command = "CC=" + CC + " "
        config_command += "CXX=" + CXX + " "
        config_command += "./configure "
        config_command += "CFLAGS=" + C_FLAGS + " "
        config_command += "CXXFLAGS=" + CXX_FLAGS

    elif os.path.exists(project_path + "/configure.ac"):
        config_command = "autoreconf -i;"
        config_command += "CC=" + CC + " "
        config_command += "CXX=" + CXX + " "
        config_command += "./configure "
        config_command += "CFLAGS=" + C_FLAGS + " "
        config_command += "CXXFLAGS=" + CXX_FLAGS

    elif os.path.exists(project_path + "/configure.in"):
        config_command = "autoreconf -i;"
        config_command += "CC=" + CC + " "
        config_command += "CXX=" + CXX + " "
        config_command += "./configure "
        config_command += "CFLAGS=" + C_FLAGS + " "
        config_command += "CXXFLAGS=" + CXX_FLAGS

    elif os.path.exists(project_path + "/CMakeLists.txt"):
        config_command = "cmake -DCMAKE_CC=" + CC + " "
        config_command += "-DCMAKE_CXX=" + CXX + " "
        config_command += "-DCMAKE_C_FLAGS=" + C_FLAGS + " "
        config_command += "-DCMAKE_CXX_FLAGS=" + CXX_FLAGS + " . "

    if is_llvm:
        config_command = "LLVM_COMPILER=clang;" + config_command

    config_command = dir_command + config_command
    # print(config_command)
    ret_code = execute_command(config_command)
    if int(ret_code) != 0:
        Emitter.error(config_command)
        error_exit("CONFIGURATION FAILED!!\nExit Code: " + str(ret_code))


def apply_flags(build_command):
    c_flags = C_FLAGS
    if "XCFLAGS=" in build_command:
        c_flags_old = (build_command.split("XCFLAGS='")[1]).split("'")[0]
        if "-fPIC" in c_flags_old:
            c_flags = c_flags.replace("-static", "")
        c_flags_new = c_flags.replace("'", "") + " " + c_flags_old
        build_command = build_command.replace(c_flags_old, c_flags_new)
    elif "CFLAGS=" in build_command:
        c_flags_old = (build_command.split("CFLAGS='")[1]).split("'")[0]
        if "-fPIC" in c_flags_old:
            c_flags = c_flags.replace("-static", "")
        c_flags_new = c_flags.replace("'", "") + " " + c_flags_old
        build_command = build_command.replace(c_flags_old, c_flags_new)
    else:
        new_command = "make CFLAGS=" + c_flags + " "
        build_command = build_command.replace("make", new_command)

    if "XCXXFLAGS=" in build_command:
        c_flags_old = (build_command.split("XCXXFLAGS='")[1]).split("'")[0]
        if "-fPIC" in c_flags_old:
            c_flags = c_flags.replace("-static", "")
        c_flags_new = c_flags.replace("'", "") + " " + c_flags_old
        build_command = build_command.replace(c_flags_old, c_flags_new)
    elif "CXXFLAGS=" in build_command:
        c_flags_old = (build_command.split("CXXFLAGS='")[1]).split("'")[0]
        if "-fPIC" in c_flags_old:
            c_flags = c_flags.replace("-static", "")
        c_flags_new = c_flags.replace("'", "") + " " + c_flags_old
        build_command = build_command.replace(c_flags_old, c_flags_new)
    else:
        new_command = "make CXXFLAGS=" + c_flags + " "
        build_command = build_command.replace("make", new_command)

    if "XCC=" in build_command:
        cc_old = (build_command.split("XCC='")[1]).split("'")[0]
        build_command = build_command.replace(cc_old, CC)
    elif "CC=" in build_command:
        cc_old = (build_command.split("CC='")[1]).split("'")[0]
        build_command = build_command.replace(cc_old, CC)
    else:
        new_command = "make CC=" + CC + " "
        build_command = build_command.replace("make", new_command)

    if "XCXX=" in build_command:
        cc_old = (build_command.split("XCXX='")[1]).split("'")[0]
        build_command = build_command.replace(cc_old, CXX)
    elif "CXX=" in build_command:
        cc_old = (build_command.split("CXX='")[1]).split("'")[0]
        build_command = build_command.replace(cc_old, CXX)
    else:
        new_command = "make CXX=" + CXX + " "
        build_command = build_command.replace("make", new_command)

    return build_command


def build_project(project_path, build_command=None):
    dir_command = "cd " + project_path + ";"
    if build_command is None:
        build_command = "bear make CFLAGS=" + C_FLAGS + " "
        build_command += "CXXFLAGS=" + CXX_FLAGS + " > " + Definitions.FILE_MAKE_LOG
    else:
        if "--no-static" in build_command:
            c_flags_Nstatic = C_FLAGS.replace("-static", "")
            build_command = "bear make CFLAGS=" + c_flags_Nstatic + " "
            cxx_flags_Nstatic = CXX_FLAGS.replace("-static", "")
            build_command += "CXXFLAGS=" + cxx_flags_Nstatic + " > " + Definitions.FILE_MAKE_LOG
        else:
            if not os.path.isfile(project_path + "/compile_commands.json"):
                build_command = build_command.replace("make", "bear make")
            if CC == "wllvm":
                build_command = remove_fsanitize(build_command)
            if "-j" not in build_command:
                build_command = apply_flags(build_command)
    build_command = dir_command + build_command
    # print(build_command)
    ret_code = execute_command(build_command)
    if int(ret_code) != 0:
        Emitter.error(build_command)
        error_exit("BUILD FAILED!!\nExit Code: " + str(ret_code))


def build_all():
    Emitter.sub_sub_title("building projects")

    Emitter.normal("\t" + Values.Project_A.path)
    if not Values.BUILD_COMMAND_A:
        build_project(Values.Project_A.path)
    else:
        build_project(Values.Project_A.path, Values.BUILD_COMMAND_A)

    Emitter.normal("\t" + Values.Project_B.path)
    if not Values.BUILD_COMMAND_A:
        build_project(Values.Project_B.path)
    else:
        build_project(Values.Project_B.path, Values.BUILD_COMMAND_A)

    Emitter.normal("\t" + Values.Project_C.path)
    if not Values.BUILD_COMMAND_C:
        build_project(Values.Project_C.path)
    else:
        build_project(Values.Project_C.path, Values.BUILD_COMMAND_C)

    Emitter.normal("\t" + Values.Project_D.path)
    if not Values.BUILD_COMMAND_C:
        build_project(Values.Project_D.path)
    else:
        build_project(Values.Project_D.path, Values.BUILD_COMMAND_C)


def config_all(is_llvm=False):
    Emitter.sub_sub_title("configuring projects")

    Emitter.normal("\t" + Values.Project_A.path)
    if not Values.CONFIG_COMMAND_A:
        config_project(Values.Project_A.path, is_llvm)
    else:
        config_project(Values.Project_A.path, is_llvm, Values.CONFIG_COMMAND_A)

    Emitter.normal("\t" + Values.Project_B.path)
    if not Values.CONFIG_COMMAND_A:
        config_project(Values.Project_B.path, is_llvm)
    else:
        config_project(Values.Project_B.path, is_llvm, Values.CONFIG_COMMAND_A)

    Emitter.normal("\t" + Values.Project_C.path)
    if not Values.CONFIG_COMMAND_C:
        config_project(Values.Project_C.path, is_llvm)
    else:
        config_project(Values.Project_C.path, is_llvm, Values.CONFIG_COMMAND_C)

    Emitter.normal("\t" + Values.Project_D.path)
    if not Values.CONFIG_COMMAND_C:
        config_project(Values.Project_D.path, is_llvm)
    else:
        config_project(Values.Project_D.path, is_llvm, Values.CONFIG_COMMAND_C)


def build_normal():
    global CC, CXX, CXX_FLAGS, C_FLAGS, LD_FLAGS
    clean_all()
    CC = "clang"
    CXX = "clang++"
    CXX_FLAGS = "'-g -O0'"
    C_FLAGS = "'-g -O0'"
    config_all()
    CXX_FLAGS = "'-g -O0 -DNDEBUG '"
    C_FLAGS = "'-g -O0 -DNDEBUG '"
    build_all()


def remove_fsanitize(build_command):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    sanitize_group = ['integer', 'address', 'undefined']
    for group in sanitize_group:
        build_command = str(build_command).replace("-fsanitize=" + str(group), "")
    return build_command


def build_instrumented_code(source_directory):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\t\t\tbuilding instrumented code")
    global CXX_FLAGS, C_FLAGS, CC, CXX
    CC = "wllvm"
    CXX = "wllvm++"
    CXX_FLAGS = "'-g -O0 -static -DNDEBUG '"
    C_FLAGS = "'-g -O0 -static  -L/klee/build/lib -lkleeRuntest'"

    if os.path.exists(source_directory + "/" + "aclocal.m4"):
        pre_config_command = "cd " + source_directory + ";"
        pre_config_command += "rm aclocal.m4;aclocal"
        execute_command(pre_config_command)

    elif os.path.exists(source_directory + "/autogen.sh"):
        pre_config_command = "./autogen.sh;"
        execute_command(pre_config_command)

    build_command = "cd " + source_directory + ";"
    custom_build_command = ""
    if (Values.PATH_A in source_directory) or (Values.PATH_B in source_directory):
        if Values.BUILD_COMMAND_A is not None:
            custom_build_command = Values.BUILD_COMMAND_A

    if Values.PATH_C in source_directory:
        if Values.BUILD_COMMAND_C is not None:
            custom_build_command = Values.BUILD_COMMAND_C

    # print("custom command is " + custom_build_command)

    if not custom_build_command:
        build_command += "make CFLAGS=" + C_FLAGS + " "
        build_command += "CXXFLAGS=" + CXX_FLAGS + " > " + Definitions.FILE_MAKE_LOG
    else:
        if not os.path.isfile(source_directory + "/compile_commands.json"):
            custom_build_command = custom_build_command.replace("make", "bear make")
        build_command = remove_fsanitize(build_command)
        build_command_with_flags = apply_flags(custom_build_command)
        build_command += build_command_with_flags

    # print(build_command)
    ret_code = execute_command(build_command)
    if int(ret_code) == 2:
        # TODO: check only upto common directory
        while source_directory != "" and ret_code != "0":
            build_command = build_command.replace(source_directory, "???")
            source_directory = "/".join(source_directory.split("/")[:-1])
            build_command = build_command.replace("???", source_directory)
            ret_code = execute_command(build_command)

    if int(ret_code) != 0:
        Emitter.error(build_command)
        error_exit("BUILD FAILED!!\nExit Code: " + str(ret_code))


def build_verify():
    global CC, CXX, CXX_FLAGS, C_FLAGS, LD_FLAGS
    Emitter.sub_sub_title("building projects")
    CC = "clang"
    CXX = "clang++"
    CXX_FLAGS = "'-g -O0 -DNDEBUG'"
    C_FLAGS = "'-g -O0 -DNDEBUG'"
    Emitter.normal("\t\t" + Values.Project_D.path)
    clean_project(Values.Project_D.path)
    clean_project(Values.Project_C.path)

    if Values.CONFIG_COMMAND_C:
        config_project(Values.Project_D.path, False, Values.CONFIG_COMMAND_C)
        config_project(Values.Project_C.path, False, Values.CONFIG_COMMAND_C)
    else:
        config_project(Values.Project_D.path, False)
        config_project(Values.Project_C.path, False)

    if Values.BUILD_COMMAND_C:
        CXX_FLAGS = "'-g -O0 -static -DNDEBUG -fsanitize=" + Values.ASAN_FLAG + "'"
        C_FLAGS = "'-g -O0 -static -DNDEBUG -fsanitize=" + Values.ASAN_FLAG + "'"
        build_project(Values.Project_D.path, Values.BUILD_COMMAND_C)
        build_project(Values.Project_C.path, Values.BUILD_COMMAND_C)
    else:
        CXX_FLAGS = "'-g -O0 -static -DNDEBUG -fsanitize=" + Values.ASAN_FLAG + "'"
        C_FLAGS = "'-g -O0 -static -DNDEBUG -fsanitize=" + Values.ASAN_FLAG + "'"
        build_project(Values.Project_C.path)
        build_project(Values.Project_D.path)


def build_asan():
    global CC, CXX, CXX_FLAGS, C_FLAGS, LD_FLAGS
    clean_all()
    CC = "clang-7"
    CXX = "clang++-7"
    CXX_FLAGS = "'-g -O0 -static'"
    C_FLAGS = "'-g -O0 -static'"
    config_all()
    CXX_FLAGS = "'-g -O0 -static -DNDEBUG -fsanitize=" + Values.ASAN_FLAG + "'"
    C_FLAGS = "'-g -O0 -static -DNDEBUG -fsanitize=" + Values.ASAN_FLAG + "'"
    build_all()


def build_llvm():
    global CC, CXX, CXX_FLAGS, C_FLAGS, LD_FLAGS
    clean_all()
    os.environ["LLVM_COMPILER"] = "clang"
    CC = "wllvm"
    CXX = "wllvm++"
    CXX_FLAGS = "'-g -O0 -static'"
    C_FLAGS = "'-g -O0 -static'"
    config_all()
    CXX_FLAGS = "'-g -O0 -static -DNDEBUG '"
    C_FLAGS = "'-g -O0 -static  -L/klee/build/lib -lkleeRuntest'"
    build_all()


def restore_project(project_path):
    restore_command = "cd " + project_path + ";"
    if os.path.exists(project_path + "/.git"):
        restore_command += "git clean -fd; git reset --hard HEAD"
    elif os.path.exists(project_path + "/.svn"):
        restore_command += "svn revert -R .; svn status --no-ignore | grep '^\?' | sed 's/^\?     //'  | xargs rm -rf"
    elif os.path.exists(project_path + "/.hg"):
        restore_command += "hg update --clean; hg st -un0 | xargs -0 rm"
    else:
        return
    # print(restore_command)
    execute_command(restore_command)


def soft_restore_project(project_path):
    restore_command = "cd " + project_path + ";"
    if os.path.exists(project_path + "/.git"):
        restore_command += "git reset --hard HEAD"
    elif os.path.exists(project_path + "/.svn"):
        restore_command += "svn revert -R .; "
    elif os.path.exists(project_path + "/.hg"):
        restore_command += "hg update --clean"
    else:
        return
    # print(restore_command)
    execute_command(restore_command)


def restore_all():
    Emitter.sub_sub_title("restoring projects")
    Emitter.normal("\t" + Values.Project_A.path)
    restore_project(Values.Project_A.path)
    Emitter.normal("\t" + Values.Project_B.path)
    restore_project(Values.Project_B.path)
    Emitter.normal("\t" + Values.Project_C.path)
    restore_project(Values.Project_C.path)
    Emitter.normal("\t" + Values.Project_D.path)
    restore_project(Values.Project_D.path)


def soft_restore_all():
    Emitter.sub_sub_title("restoring(soft) projects")
    Emitter.normal("\t" + Values.Project_A.path)
    soft_restore_project(Values.Project_A.path)
    Emitter.normal("\t" + Values.Project_B.path)
    soft_restore_project(Values.Project_B.path)
    Emitter.normal("\t" + Values.Project_C.path)
    soft_restore_project(Values.Project_C.path)
    Emitter.normal("\t" + Values.Project_D.path)
    soft_restore_project(Values.Project_D.path)


def clean_project(project_path):
    clean_command = "cd " + project_path + "; make clean; make distclean"
    clean_command += "; rm compile_commands.json"
    clean_command += "; rm CMakeCache.txt"
    clean_command += "; rm -rf CMakeFiles"
    execute_command(clean_command)


def clean_all():
    restore_all()
    Emitter.sub_sub_title("cleaning projects")
    Emitter.normal("\t" + Values.Project_A.path)
    clean_project(Values.Project_A.path)

    Emitter.normal("\t" + Values.Project_B.path)
    clean_project(Values.Project_B.path)

    Emitter.normal("\t" + Values.Project_C.path)
    clean_project(Values.Project_C.path)

    Emitter.normal("\t" + Values.Project_D.path)
    clean_project(Values.Project_D.path)
