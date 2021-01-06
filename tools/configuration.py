import os
import signal
import shutil
from common import definitions, values, utilities
from tools import emitter
from entity import project


def load_standard_list():
    with open(definitions.FILE_STANDARD_FUNCTION_LIST, "r") as list_file:
        values.STANDARD_FUNCTION_LIST = [line[:-1] for line in list_file]
    with open(definitions.FILE_STANDARD_MACRO_LIST, "r") as list_file:
        values.STANDARD_MACRO_LIST = [line[:-1] for line in list_file]


def read_conf_file():
    emitter.normal("reading configuration file")
    if not os.path.exists(values.FILE_CONFIGURATION):
        emitter.normal("[NOT FOUND] Configuration file " + values.FILE_CONFIGURATION)
        exit()

    with open(values.FILE_CONFIGURATION, 'r') as conf_file:
        configuration_list = [i.strip() for i in conf_file.readlines()]

    for configuration in configuration_list:
        if definitions.CONF_PATH_A in configuration:
            values.CONF_PATH_A = configuration.replace(definitions.CONF_PATH_A, '')
            if "$HOME$" in values.CONF_PATH_A:
                values.CONF_PATH_A = values.CONF_PATH_A.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_PATH_B in configuration:
            values.CONF_PATH_B = configuration.replace(definitions.CONF_PATH_B, '')
            if "$HOME$" in values.CONF_PATH_B:
                values.CONF_PATH_B = values.CONF_PATH_B.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_PATH_C in configuration:
            values.CONF_PATH_C = configuration.replace(definitions.CONF_PATH_C, '')
            if "$HOME$" in values.CONF_PATH_C:
                values.CONF_PATH_C = values.CONF_PATH_C.replace("$HOME$", definitions.DIRECTORY_MAIN)
            if str(values.CONF_PATH_C)[-1] == "/":
                values.CONF_PATH_C = values.CONF_PATH_C[:-1]
        elif definitions.CONF_PATH_E in configuration:
            values.CONF_PATH_E = configuration.replace(definitions.CONF_PATH_E, '')
            if "$HOME$" in values.CONF_PATH_E:
                values.CONF_PATH_E = values.CONF_PATH_E.replace("$HOME$", definitions.DIRECTORY_MAIN)
            if str(values.CONF_PATH_E)[-1] == "/":
                values.CONF_PATH_E = values.CONF_PATH_E[:-1]

        elif definitions.CONF_COMMIT_A in configuration:
            values.CONF_COMMIT_A = configuration.replace(definitions.CONF_COMMIT_A, '')
        elif definitions.CONF_COMMIT_B in configuration:
            values.CONF_COMMIT_B = configuration.replace(definitions.CONF_COMMIT_B, '')
        elif definitions.CONF_COMMIT_C in configuration:
            values.CONF_COMMIT_C = configuration.replace(definitions.CONF_COMMIT_C, '')
        elif definitions.CONF_COMMIT_E in configuration:
            values.CONF_COMMIT_E = configuration.replace(definitions.CONF_COMMIT_E, '')

        elif definitions.CONF_PATH_POC in configuration:
            values.CONF_PATH_POC = configuration.replace(definitions.CONF_PATH_POC, '')
            if "$HOME$" in values.CONF_PATH_POC:
                values.CONF_PATH_POC = values.CONF_PATH_POC.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_FLAGS_A in configuration:
            values.CONF_BUILD_FLAGS_A = configuration.replace(definitions.CONF_FLAGS_A, '')
        elif definitions.CONF_FLAGS_C in configuration:
            values.CONF_BUILD_FLAGS_C = configuration.replace(definitions.CONF_FLAGS_C, '')
        elif definitions.CONF_CONFIG_COMMAND_A in configuration:
            values.CONF_CONFIG_COMMAND_A = configuration.replace(definitions.CONF_CONFIG_COMMAND_A, '')
        elif definitions.CONF_CONFIG_COMMAND_C in configuration:
            values.CONF_CONFIG_COMMAND_C = configuration.replace(definitions.CONF_CONFIG_COMMAND_C, '')
        elif definitions.CONF_BUILD_COMMAND_A in configuration:
            values.CONF_BUILD_COMMAND_A = configuration.replace(definitions.CONF_BUILD_COMMAND_A, '')
        elif definitions.CONF_BUILD_COMMAND_C in configuration:
            values.CONF_BUILD_COMMAND_C = configuration.replace(definitions.CONF_BUILD_COMMAND_C, '')
        elif definitions.CONF_ASAN_FLAG in configuration:
            values.CONF_ASAN_FLAG = configuration.replace(definitions.CONF_ASAN_FLAG, '')
        elif definitions.CONF_DIFF_SIZE in configuration:
            values.CONF_AST_DIFF_SIZE = configuration.replace(definitions.CONF_DIFF_SIZE, '')
        elif definitions.CONF_EXPLOIT_C in configuration:
            values.CONF_EXPLOIT_C = configuration.replace(definitions.CONF_EXPLOIT_C, '')
        elif definitions.CONF_VC in configuration:
            values.CONF_VC = configuration.replace(definitions.CONF_VC, '')
        elif definitions.CONF_CONTEXT_LEVEL in configuration:
            values.CONF_CONTEXT_LEVEL = int(configuration.replace(definitions.CONF_CONTEXT_LEVEL, ""))
        elif definitions.CONF_LINUX_KERNEL in configuration:
            value = configuration.replace(definitions.CONF_LINUX_KERNEL, '')
            if "true" in value:
                values.IS_LINUX_KERNEL = True
            else:
                values.IS_LINUX_KERNEL = False
        elif definitions.CONF_BACKPORT in configuration:
            value = configuration.replace(definitions.CONF_BACKPORT, '')
            if "true" in value:
                values.BACKPORT = True
            else:
                values.BACKPORT = False


def read_conf(arg_list):
    emitter.normal("reading configuration values")
    if len(arg_list) > 0:
        for arg in arg_list:
            if definitions.ARG_DEBUG in arg:
                values.DEBUG = True
            elif definitions.ARG_DEBUG_DATA in arg:
                values.DEBUG_DATA = True
            elif definitions.ARG_SKIP_VEC_GEN in arg:
                values.SKIP_VEC_GEN = True
            elif definitions.ARG_SKIP_RESTORE in arg:
                values.SKIP_RESTORE = True
            elif definitions.ARG_USE_CACHE in arg:
                values.CONF_USE_CACHE = True
            elif definitions.ARG_BACKPORT in arg:
                values.BACKPORT = True
            elif definitions.ARG_FORK in arg:
                values.FORK = True
            elif definitions.ARG_CONF_FILE in arg:
                values.FILE_CONFIGURATION = str(arg).replace(definitions.ARG_CONF_FILE, '')
            elif definitions.ARG_LINUX_KERNEL in arg:
                values.IS_LINUX_KERNEL = True
            elif definitions.ARG_BREAK_WEAVE in arg:
                values.BREAK_WEAVE = True
            elif definitions.ARG_ANALYSE_NEIGHBORS in arg:
                values.ANALYSE_N = True
                values.ONLY_RESET = True
                for phase in values.PHASE_SETTING:
                    if phase in [definitions.PHASE_BUILD, definitions.PHASE_DIFF, definitions.PHASE_COMPARE]:
                        values.PHASE_SETTING[phase] = 1
                    else:
                        values.PHASE_SETTING[phase] = 0
            elif definitions.ARG_OPERATION_MODE in arg:
                mode = int(arg.replace(definitions.ARG_OPERATION_MODE, ''))
                if mode not in definitions.operation_mode:
                    emitter.normal("Invalid argument: " + arg)
                    emitter.help()
                else:
                    values.CONF_OPERATION_MODE = mode
            elif definitions.ARG_BUILD_AND_ANALYSE in arg:
                values.ANALYSE_N = True
                for phase in values.PHASE_SETTING:
                    if phase in [definitions.PHASE_BUILD, definitions.PHASE_DIFF, definitions.PHASE_COMPARE]:
                        values.PHASE_SETTING[phase] = 1
                    else:
                        values.PHASE_SETTING[phase] = 0
            elif definitions.ARG_CONTEXT_LEVEL in arg:
                values.CONF_CONTEXT_LEVEL = int(arg.replace(definitions.ARG_CONTEXT_LEVEL, ""))
            elif "--skip" in arg:
                arg_phase = arg.replace("--skip-", "")
                values.PHASE_SETTING[arg_phase] = 0
            elif "--only" in arg:
                arg_phase = arg.replace("--only-", "")
                for phase in values.PHASE_SETTING:
                    if phase == arg_phase:
                        values.PHASE_SETTING[phase] = 1
                    else:
                        values.PHASE_SETTING[phase] = 0
            else:
                emitter.normal("Invalid argument: " + arg)
                emitter.help()
                exit()
    else:
        emitter.help()
        exit()


def update_phase_configuration(arg_list):

    if values.DEFAULT_OPERATION_MODE in [0, 3]:
        for phase_name in values.PHASE_SETTING:
            values.PHASE_SETTING[phase_name] = 1

    elif values.DEFAULT_OPERATION_MODE in [1, 2]:
        values.PHASE_SETTING = {
            definitions.PHASE_BUILD: 1,
            definitions.PHASE_DIFF: 1,
            definitions.PHASE_DETECTION: 1,
            definitions.PHASE_SLICING: 1,
            definitions.PHASE_EXTRACTION: 1,
            definitions.PHASE_MAPPING: 0,
            definitions.PHASE_TRANSLATION: 0,
            definitions.PHASE_EVOLUTION: 0,
            definitions.PHASE_WEAVE: 1,
            definitions.PHASE_VERIFY: 1,
            definitions.PHASE_REVERSE: 0,
            definitions.PHASE_EVALUATE: 0,
            definitions.PHASE_COMPARE: 1,
            definitions.PHASE_SUMMARIZE: 1,
        }

    if values.DEFAULT_OPERATION_MODE == 3:
        values.PHASE_SETTING[definitions.PHASE_EVOLUTION] = 0

    if len(arg_list) > 0:
        for arg in arg_list:
            if "--skip-" in arg:
                arg_phase = arg.replace("--skip-", "")
                if arg_phase not in values.PHASE_SETTING:
                    emitter.error("Invalid argument: " + arg)
                    emitter.help()
                    exit()
                values.PHASE_SETTING[arg_phase] = 0
            elif "--only-" in arg:
                arg_phase = arg.replace("--only-", "")
                if arg_phase not in values.PHASE_SETTING:
                    emitter.error("Invalid argument: " + arg)
                    emitter.help()
                    exit()
                for phase_name in values.PHASE_SETTING:
                    values.PHASE_SETTING[phase_name] = 0
                    if phase_name == arg_phase:
                        values.PHASE_SETTING[phase_name] = 1


def print_configuration():
    emitter.configuration("operation mode", definitions.operation_mode[values.DEFAULT_OPERATION_MODE])
    emitter.configuration("output dir", definitions.DIRECTORY_OUTPUT)
    emitter.configuration("context level", values.DEFAULT_CONTEXT_LEVEL)
    emitter.configuration("timeout limit", values.DEFAULT_OVERALL_TIMEOUT)


def update_configuration():
    emitter.normal("updating configuration values")
    # create log files and other directories
    conf_file_name = values.FILE_CONFIGURATION.split("/")[-1]
    project_name = values.FILE_CONFIGURATION.split("/")[-3]
    dir_name = project_name + "-" + conf_file_name.replace(".conf", "")

    # if definitions.DIRECTORY_MAIN + "/tests" in os.path.abspath(values.FILE_CONFIGURATION):
    #     values.CONF_VC = "git"

    definitions.DIRECTORY_OUTPUT = definitions.DIRECTORY_OUTPUT_BASE + "/" + dir_name
    definitions.DIRECTORY_TMP = definitions.DIRECTORY_OUTPUT + "/tmp"
    definitions.DIRECTORY_LOG = definitions.DIRECTORY_LOG_BASE + "/" + dir_name

    if not os.path.isdir(definitions.DIRECTORY_OUTPUT):
        # shutil.rmtree(definitions.DIRECTORY_OUTPUT)
        os.mkdir(definitions.DIRECTORY_OUTPUT)

    if not os.path.isdir(definitions.DIRECTORY_LOG):
        os.makedirs(definitions.DIRECTORY_LOG)

    if not os.path.isdir(definitions.DIRECTORY_TMP):
        os.makedirs(definitions.DIRECTORY_TMP)

    if values.CONF_OPERATION_MODE > -1:
        values.DEFAULT_OPERATION_MODE = values.CONF_OPERATION_MODE

    if values.CONF_CONTEXT_LEVEL > -1:
        values.DEFAULT_CONTEXT_LEVEL = values.CONF_CONTEXT_LEVEL

    if values.DEFAULT_OPERATION_MODE in [1, 2]:
        values.DEFAULT_OVERALL_TIMEOUT = 1200

    signal.alarm(values.DEFAULT_OVERALL_TIMEOUT)
    patch_dir = values.CONF_PATH_C + "-patch"
    if os.path.isdir(patch_dir):
        if definitions.DIRECTORY_TESTS in patch_dir:
            shutil.rmtree(patch_dir)
    if not os.path.isdir(patch_dir):
        shutil.copytree(values.CONF_PATH_C, values.CONF_PATH_C + "-patch")

    input_dir = definitions.DIRECTORY_OUTPUT + "/fuzz-input"
    output_dir = definitions.DIRECTORY_OUTPUT + "/fuzz-output"
    if not os.path.isdir(input_dir):
        os.makedirs(input_dir)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    values.Project_A = project.Project(values.CONF_PATH_A, "Pa")
    values.Project_B = project.Project(values.CONF_PATH_B, "Pb")
    values.Project_C = project.Project(values.CONF_PATH_C, "Pc")
    values.Project_D = project.Project(values.CONF_PATH_C + "-patch", "Pd")
    if values.CONF_PATH_E:
        values.Project_E = project.Project(values.CONF_PATH_E, "Pe")

    load_standard_list()

    definitions.FILE_AST_SCRIPT = definitions.DIRECTORY_TMP + "/ast-script"
    definitions.FILE_TEMP_DIFF = definitions.DIRECTORY_TMP + "/temp_diff"
    definitions.FILE_AST_MAP = definitions.DIRECTORY_TMP + "/ast-map"
    definitions.FILE_AST_DIFF_ERROR = definitions.DIRECTORY_TMP + "/errors_ast_diff"
    definitions.FILE_PARTIAL_PATCH = definitions.DIRECTORY_TMP + "/gen-patch"
    definitions.FILE_EXCLUDED_EXTENSIONS = definitions.DIRECTORY_TMP + "/excluded-extensions"
    definitions.FILE_EXCLUDED_EXTENSIONS_A = definitions.DIRECTORY_TMP + "/excluded-extensions-a"
    definitions.FILE_EXCLUDED_EXTENSIONS_B = definitions.DIRECTORY_TMP + "/excluded-extensions-b"
    definitions.FILE_GIT_UNTRACKED_FILES = definitions.DIRECTORY_TMP + "/untracked-list"
    definitions.FILE_DIFF_C = definitions.DIRECTORY_TMP + "/diff_C"
    definitions.FILE_DIFF_H = definitions.DIRECTORY_TMP + "/diff_H"
    definitions.FILE_DIFF_ALL = definitions.DIRECTORY_TMP + "/diff_all"
    definitions.FILE_FIND_RESULT = definitions.DIRECTORY_TMP + "/find_tmp"
    definitions.FILE_TEMP_TRANSFORM = definitions.DIRECTORY_TMP + "/temp-transform"



