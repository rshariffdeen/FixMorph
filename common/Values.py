#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from common import Definitions

Project_A = None
Project_B = None
Project_C = None
Project_D = None
Project_E = None

DEBUG = False
DEBUG_DATA = False
BACKPORT = False
BREAK_WEAVE = False
FORK = False
IS_LINUX_KERNEL = False
SKIP_VEC_GEN = False
ANALYSE_N = False
ONLY_RESET = False

count_orig_total_N = 0
count_orig_localized_N = 0
count_trans_total_N = 0
count_trans_localized_N = 0


PHASE_SETTING = {
    Definitions.PHASE_BUILD: 1,
    Definitions.PHASE_DIFF: 1,
    Definitions.PHASE_DETECTION: 1,
    Definitions.PHASE_SLICING: 1,
    Definitions.PHASE_EXTRACTION: 1,
    Definitions.PHASE_MAPPING: 1,
    Definitions.PHASE_TRANSLATION: 1,
    Definitions.PHASE_EVOLUTION: 1,
    Definitions.PHASE_WEAVE: 1,
    Definitions.PHASE_VERIFY: 1,
    Definitions.PHASE_REVERSE: 1,
    Definitions.PHASE_EVALUATE: 1,
    Definitions.PHASE_COMPARE: 1,
    Definitions.PHASE_SUMMARIZE: 1,
}

STANDARD_FUNCTION_LIST = list()
STANDARD_MACRO_LIST = list()

PROJECT_A_FUNCTION_LIST = ""
PROJECT_B_FUNCTION_LIST = ""
PROJECT_C_FUNCTION_LIST = ""
PROJECT_E_FUNCTION_LIST = ""
DIFF_FUNCTION_LIST = ""
DIFF_LINE_LIST = dict()
DIVERGENT_POINT_LIST = list()
FUNCTION_MAP = ""
MODIFIED_SOURCE_LIST = list()


# ------------------ Configuration Values ---------------
BUG_ID = ""
PATH_A = ""
PATH_B = ""
PATH_C = ""
PATH_E = ""
COMMIT_A = None
COMMIT_B = None
COMMIT_C = None
COMMIT_E = None
EXPLOIT_A = ""
EXPLOIT_C = ""
BUILD_FLAGS_A = ""
BUILD_FLAGS_C = ""
CONFIG_COMMAND_A = ""
CONFIG_COMMAND_C = ""
BUILD_COMMAND_A = ""
BUILD_COMMAND_C = ""
PATH_POC = ""
EXPLOIT_PREPARE = ""
ASAN_FLAG = ""
KLEE_FLAG_A = ""
KLEE_FLAG_C = ""
FILE_CONFIGURATION = ""
AST_DIFF_SIZE = "1000"
VC = ""
USE_CACHE = False

silence_emitter = False
file_list_to_patch = []
generated_script_files = dict()
translated_script_for_files = dict()
ast_map = dict()

original_diff_info = dict()
ported_diff_info = dict()

Pa = None
Pb = None
Pc = None
crash_script = None

CONF_FILE_NAME = "crochet.conf"
PATCH_SIZE = "1000"
DIFF_COMMAND = "crochet-diff "
DIFF_SIZE = "1000"
SYNTAX_CHECK_COMMAND = "clang-check "
STYLE_FORMAT_COMMAND = "clang-format -style=LLVM "

interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

phase_conf = {"Build": 1, "Differencing": 1, "Detection": 1, "Slicing": 1, "Extraction": 1,
              "Mapping": 1, "Translation": 1, "Weaving": 1, "Verify": 1, "Compare": 1, "Summarize": 1}

segment_map = {"func": "FunctionDecl", "var": "VarDecl",  "enum": "EnumDecl", "macro": "Macro", "struct": "RecordDecl"}

IS_FUNCTION = False
IS_STRUCT = False
IS_ENUM = False
IS_MACRO = False
IS_TYPEDEF = False
IS_TYPEDEC = False
VECTOR_MAP = dict()
VAR_MAP = dict()
VAR_MAP_LOCAL = dict()
VAR_MAP_GLOBAL = dict()
FUNCTION_MAP = dict()
FUNCTION_MAP_LOCAL = dict()
FUNCTION_MAP_GLOBAL = dict()
Method_ARG_MAP = dict()
Method_ARG_MAP_LOCAL = dict()
Method_ARG_MAP_GLOBAL = dict()
NODE_MAP = dict()

DONOR_REQUIRE_MACRO = False
TARGET_REQUIRE_MACRO = False
PRE_PROCESS_MACRO = ""
DONOR_PRE_PROCESS_MACRO = ""
TARGET_PRE_PROCESS_MACRO = ""

USE_PREPROCESS = False

missing_function_list = dict()
missing_macro_list = dict()
missing_header_list = dict()
missing_data_type_list = dict()
modified_source_list = list()
