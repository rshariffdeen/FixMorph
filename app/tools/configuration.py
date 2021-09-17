import os
import signal
import shutil
import git
from app.common import definitions, values, utilities
from app.tools import generator, differ, emitter, db
from app.entity import project


def load_standard_list():
    with open(definitions.FILE_STANDARD_FUNCTION_LIST, "r") as list_file:
        values.STANDARD_FUNCTION_LIST = [line[:-1] for line in list_file]
    with open(definitions.FILE_STANDARD_MACRO_LIST, "r") as list_file:
        values.STANDARD_MACRO_LIST = [line[:-1] for line in list_file]
    with open(definitions.FILE_STANDARD_DATATYPE_LIST, "r") as list_file:
        for line in list_file:
            values.STANDARD_DATATYPE_LIST.append(line[:-1])
            values.STANDARD_DATATYPE_LIST.append("const " + line[:-1])
            values.STANDARD_DATATYPE_LIST.append(line[:-1] + " *")


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
        elif definitions.CONF_TAG_ID in configuration:
            values.CONF_TAG_ID = configuration.replace(definitions.CONF_TAG_ID, "").strip().replace("\n", "")
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
                values.IS_BACKPORT = True
            else:
                values.IS_BACKPORT = False
    if values.IS_LINUX_KERNEL:
        repo = git.Repo(definitions.DIRECTORY_LINUX)
        # versions. (requires git version >= 2.13.7)
        ver_A = repo.git.describe("--exclude", "*rc*", "--contains", values.CONF_COMMIT_A).split("~")[0]
        values.CONF_VERSION_A = (".".join(ver_A.split(".", 2)[:2]))[1:]
        ver_C = repo.git.describe(values.CONF_COMMIT_C).split('-')[0]
        values.CONF_VERSION_C = (".".join(ver_C.split(".", 2)[:2]))[1:]



def read_from_db():
    emitter.normal("reading from db to get configuration values")
    
    commit_b, commit_e = db.get_one_untrained_pair()
    id = "training-tmp"

    values.CONF_TAG_ID = id
    values.IS_LINUX_KERNEL = True
    # directory names
    path_prefix = definitions.DIRECTORY_TRAINING + "/" + id
    values.CONF_PATH_A = path_prefix + "/pa"
    values.CONF_PATH_B = path_prefix + "/pb"
    values.CONF_PATH_C = path_prefix + "/pc"
    values.CONF_PATH_E = path_prefix + "/pe"
    # commit hashes
    repo = git.Repo(definitions.DIRECTORY_LINUX)
    values.CONF_COMMIT_A = repo.git.rev_parse(commit_b + "~1")
    values.CONF_COMMIT_B = commit_b
    values.CONF_COMMIT_C = repo.git.rev_parse(commit_e + "~1")
    values.CONF_COMMIT_E = commit_e
    # versions. (requires git version >= 2.13.7)
    ver_A = repo.git.describe("--exclude", "*rc*", "--contains", values.CONF_COMMIT_A).split("~")[0]
    values.CONF_VERSION_A = (".".join(ver_A.split(".", 2)[:2]))[1:]
    ver_C = repo.git.describe(values.CONF_COMMIT_C).split('-')[0]
    values.CONF_VERSION_C = (".".join(ver_C.split(".", 2)[:2]))[1:]
    # config command
    values.CONF_CONFIG_COMMAND_A = "make allyesconfig"
    values.CONF_CONFIG_COMMAND_C = "make allyesconfig"
    # build command - to be completed later
    values.CONF_BUILD_COMMAND_A = "make "
    values.CONF_BUILD_COMMAND_C = "make "


def training_setup_each():
    emitter.normal("setting up source file directories for training")
    top_path = values.CONF_PATH_A[:-3]
    individual_paths = [values.CONF_PATH_A, values.CONF_PATH_B, values.CONF_PATH_C, values.CONF_PATH_E]
    commit_hashes = [values.CONF_COMMIT_A, values.CONF_COMMIT_B, values.CONF_COMMIT_C,values.CONF_COMMIT_E]
    if not os.path.isdir(top_path):
        os.makedirs(top_path)
    for i in range(len(individual_paths)):
        curr_path = individual_paths[i]
        if not os.path.isdir(curr_path):
            shutil.copytree(definitions.DIRECTORY_LINUX, curr_path)
        repo = git.Repo(curr_path)
        repo.git.reset("--hard")
        repo.git.checkout(commit_hashes[i], force=True)


def training_update_build_command():
    differ.diff_files(definitions.FILE_DIFF_ALL,
                      definitions.FILE_DIFF_C,
                      definitions.FILE_DIFF_H,
                      definitions.FILE_EXCLUDED_EXTENSIONS_A,
                      definitions.FILE_EXCLUDED_EXTENSIONS_B,
                      definitions.FILE_EXCLUDED_EXTENSIONS,
                      values.CONF_PATH_A,
                      values.CONF_PATH_B)
    untracked_file_list = generator.generate_untracked_file_list(definitions.FILE_EXCLUDED_EXTENSIONS, values.CONF_PATH_A)
    diff_c_file_list = differ.diff_c_files(definitions.FILE_DIFF_C, values.CONF_PATH_B, untracked_file_list)
    if not diff_c_file_list:
        db.mark_pair_as_error(values.CONF_COMMIT_B, values.CONF_COMMIT_E)
        utilities.error_exit("no c files to build.")
    for diff_file in diff_c_file_list:
        o_file = os.path.relpath(diff_file[0], values.CONF_PATH_A)
        o_file = o_file[:-1] + "o "
        values.CONF_BUILD_COMMAND_A += o_file
    print("Final build command for A is {}".format(values.CONF_BUILD_COMMAND_A))

    differ.diff_files(definitions.FILE_DIFF_ALL,
                      definitions.FILE_DIFF_C,
                      definitions.FILE_DIFF_H,
                      definitions.FILE_EXCLUDED_EXTENSIONS_A,
                      definitions.FILE_EXCLUDED_EXTENSIONS_B,
                      definitions.FILE_EXCLUDED_EXTENSIONS,
                      values.CONF_PATH_C,
                      values.CONF_PATH_E)
    untracked_file_list = generator.generate_untracked_file_list(definitions.FILE_EXCLUDED_EXTENSIONS, values.CONF_PATH_C)
    diff_c_file_list = differ.diff_c_files(definitions.FILE_DIFF_C, values.CONF_PATH_E, untracked_file_list)
    if not diff_c_file_list:
        db.mark_pair_as_error(values.CONF_COMMIT_B, values.CONF_COMMIT_E)
        utilities.error_exit("no c files to build.")
    for diff_file in diff_c_file_list:
        o_file = os.path.relpath(diff_file[0], values.CONF_PATH_C)
        o_file = o_file[:-1] + "o "
        values.CONF_BUILD_COMMAND_C += o_file
    print("Final build command for C is {}".format(values.CONF_BUILD_COMMAND_C))



def read_conf(arg_list):
    emitter.normal("reading configuration values")
    if len(arg_list) > 0:
        for arg in arg_list:
            if definitions.ARG_DEBUG_DATA in arg:
                values.DEBUG_DATA = True
            elif definitions.ARG_DEBUG in arg:
                values.DEBUG = True
            elif definitions.ARG_TIMEOUT in arg:
                values.CONF_TIMEOUT = int(arg.replace(definitions.ARG_TIMEOUT, "").strip()) * 60
            elif definitions.ARG_SKIP_VEC_GEN in arg:
                values.SKIP_VEC_GEN = True
            elif definitions.ARG_SKIP_RESTORE in arg:
                values.SKIP_RESTORE = True
            elif definitions.ARG_USE_CACHE in arg:
                values.CONF_USE_CACHE = True
            elif definitions.ARG_BACKPORT in arg:
                values.IS_BACKPORT = True
            elif definitions.ARG_FORK in arg:
                values.IS_FORK = True
            elif definitions.ARG_CONF_FILE in arg:
                values.FILE_CONFIGURATION = str(arg).replace(definitions.ARG_CONF_FILE, '')
            elif definitions.ARG_LINUX_KERNEL in arg:
                values.IS_LINUX_KERNEL = True
            elif definitions.ARG_TRAINING in arg:
                values.IS_TRAINING = True
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
            elif definitions.ARG_OUTPUT_FORMAT in arg:
                format = arg.replace(definitions.ARG_OUTPUT_FORMAT, '')
                if format not in definitions.output_format_list:
                    emitter.normal("Invalid argument: " + arg)
                    emitter.help()
                else:
                    values.CONF_OUTPUT_FORMAT = format
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
            elif "--help" in arg:
                emitter.help()
                exit()
            else:
                emitter.normal("Invalid argument: " + arg)
                emitter.help()
                raise Exception("Unsupported Arguments")
    else:
        emitter.help()
        raise Exception("No Arguments Provided")


def update_phase_configuration(arg_list):

    if values.IS_TRAINING:
        values.DEFAULT_OPERATION_MODE = 4
        values.PHASE_SETTING = {
            definitions.PHASE_BUILD: 1,
            definitions.PHASE_DIFF: 0,
            definitions.PHASE_TRAINING: 1,
            definitions.PHASE_DETECTION: 0,
            definitions.PHASE_SLICING: 0,
            definitions.PHASE_EXTRACTION: 0,
            definitions.PHASE_MAPPING: 0,
            definitions.PHASE_TRANSLATION: 0,
            definitions.PHASE_EVOLUTION: 0,
            definitions.PHASE_WEAVE: 0,
            definitions.PHASE_VERIFY: 0,
            definitions.PHASE_REVERSE: 0,
            definitions.PHASE_EVALUATE: 0,
            definitions.PHASE_COMPARE: 0,
            definitions.PHASE_SUMMARIZE: 0,
        }

    if values.DEFAULT_OPERATION_MODE in [0, 3]:
        for phase_name in values.PHASE_SETTING:
            if phase_name != definitions.PHASE_TRAINING:
                values.PHASE_SETTING[phase_name] = 1

    elif values.DEFAULT_OPERATION_MODE in [1, 2]:
        values.PHASE_SETTING = {
            definitions.PHASE_BUILD: 1,
            definitions.PHASE_DIFF: 1,
            definitions.PHASE_DETECTION: 1,
            definitions.PHASE_SLICING: 0,
            definitions.PHASE_EXTRACTION: 1,
            definitions.PHASE_MAPPING: 0,
            definitions.PHASE_TRANSLATION: 0,
            definitions.PHASE_EVOLUTION: 0,
            definitions.PHASE_TRAINING: 0,
            definitions.PHASE_WEAVE: 1,
            definitions.PHASE_VERIFY: 1,
            definitions.PHASE_REVERSE: 0,
            definitions.PHASE_EVALUATE: 0,
            definitions.PHASE_COMPARE: 1,
            definitions.PHASE_SUMMARIZE: 1,
        }

    if values.DEFAULT_OPERATION_MODE == 3:
        values.PHASE_SETTING[definitions.PHASE_EVOLUTION] = 0

    if values.CONF_OUTPUT_FORMAT:
        values.DEFAULT_OUTPUT_FORMAT = values.CONF_OUTPUT_FORMAT

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
    emitter.configuration("debug mode", values.DEBUG)
    emitter.configuration("debug data", values.DEBUG_DATA)
    emitter.configuration("Linux Kernel", values.IS_LINUX_KERNEL)
    emitter.configuration("Backport", values.IS_BACKPORT)


def update_configuration():
    emitter.normal("updating configuration values")
    # create log files and other directories
    if values.CONF_TAG_ID:
        values.DEFAULT_TAG_ID = values.CONF_TAG_ID
    else:
        values.DEFAULT_TAG_ID = "test"
    # conf_file_name = values.FILE_CONFIGURATION.split("/")[-1]
    dir_name = values.DEFAULT_TAG_ID

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

    if values.CONF_TIMEOUT > 0:
        values.DEFAULT_OVERALL_TIMEOUT = values.CONF_TIMEOUT
        
    signal.alarm(values.DEFAULT_OVERALL_TIMEOUT)
    patch_dir = values.CONF_PATH_C + "-patch"
    if os.path.isdir(patch_dir):
        if definitions.DIRECTORY_TESTS in patch_dir:
            shutil.rmtree(patch_dir)
    if not os.path.isdir(patch_dir):
        if not values.IS_TRAINING:
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
    if not values.IS_TRAINING:
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
