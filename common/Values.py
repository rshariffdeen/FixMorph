#! /usr/bin/env python3
# -*- coding: utf-8 -*-


Project_A = None
Project_B = None
Project_C = None
Project_D = None
Project_E = None

DEBUG = False
SKIP_TRACE_GEN = False
SKIP_SYM_TRACE_GEN = False
SKIP_EXPLOIT = False
SKIP_WEAVE = False
SKIP_DIFF = False
SKIP_SUMMARY = False
SKIP_COMPARE = False
SKIP_SEGMENT = False
SKIP_VERIFY = False
SKIP_SLICE = False
SKIP_RESTORE = False
ONLY_VERIFY = False
ONLY_ANALYSE = False
ONLY_MAPPING = False
ONLY_TRANSLATE = False
ONLY_DETECT = False
BACKPORT = False
BREAK_WEAVE = False
FORK = False
IS_LINUX_KERNEL = False
SKIP_BUILD = False
SKIP_DETECTION = False
SKIP_VEC_GEN = False
SKIP_EXTRACTION = False
SKIP_MAPPING = False
SKIP_TRANSLATION = False


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

DONOR_REQUIRE_MACRO = False
TARGET_REQUIRE_MACRO = False
PRE_PROCESS_MACRO = ""
DONOR_PRE_PROCESS_MACRO = ""
TARGET_PRE_PROCESS_MACRO = ""

USE_PREPROCESS = False
