#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os

# ------------------- Directories --------------------

DIRECTORY_MAIN = os.getcwd()
DIRECTORY_LOG = DIRECTORY_MAIN + "/logs"
DIRECTORY_OUTPUT_BASE = DIRECTORY_MAIN + "/output"
DIRECTORY_OUTPUT = ""
DIRECTORY_TMP = DIRECTORY_MAIN + "/tmp"
DIRECTORY_BACKUP = DIRECTORY_MAIN + "/backup"
DIRECTORY_VECTORS_A = DIRECTORY_OUTPUT + "/vectors-a"
DIRECTORY_VECTORS_B = DIRECTORY_OUTPUT + "/vectors-b"
DIRECTORY_VECTORS_C = DIRECTORY_OUTPUT + "/vectors-c"
DIRECTORY_TOOLS = DIRECTORY_MAIN + "/third-party"
DIRECTORY_DATA = DIRECTORY_MAIN + "/data"

# ------------------- Files --------------------

FILE_MAIN_LOG = ""
FILE_ERROR_LOG = DIRECTORY_LOG + "/log-error"
FILE_LAST_LOG = DIRECTORY_LOG + "/log-latest"
FILE_MAKE_LOG = DIRECTORY_LOG + "/log-make"
FILE_COMMAND_LOG = DIRECTORY_LOG + "/log-command"
FILE_STANDARD_FUNCTION_LIST = DIRECTORY_DATA + "/standard-function-list"
FILE_STANDARD_MACRO_LIST = DIRECTORY_DATA + "/standard-macro-list"

FILE_AST_SCRIPT = DIRECTORY_TMP + "/ast-script"
FILE_TEMP_DIFF = DIRECTORY_TMP + "/temp_diff"
FILE_AST_MAP = DIRECTORY_TMP + "/ast-map"
FILE_AST_DIFF_ERROR = DIRECTORY_TMP + "/errors_ast_diff"
FILE_PARTIAL_PATCH = DIRECTORY_TMP + "/gen-patch"


FILE_EXCLUDED_EXTENSIONS = DIRECTORY_TMP + "/excluded-extensions"
FILE_EXCLUDED_EXTENSIONS_A = DIRECTORY_TMP + "/excluded-extensions-a"
FILE_EXCLUDED_EXTENSIONS_B = DIRECTORY_TMP + "/excluded-extensions-b"
FILE_DIFF_C = DIRECTORY_TMP + "/diff_C"
FILE_DIFF_H = DIRECTORY_TMP + "/diff_H"
FILE_DIFF_ALL = DIRECTORY_TMP + "/diff_all"
FILE_FIND_RESULT = DIRECTORY_TMP + "/find_tmp"


# ------------------- Configuration --------------------

CONF_PATH_A = "path_a:"
CONF_PATH_B = "path_b:"
CONF_PATH_C = "path_c:"
CONF_EXPLOIT_A = "exploit_command_a:"
CONF_CONFIG_COMMAND_A = "config_command_a:"
CONF_BUILD_COMMAND_A = "build_command_a:"
CONF_EXPLOIT_C = "exploit_command_c:"
CONF_CONFIG_COMMAND_C = "config_command_c:"
CONF_BUILD_COMMAND_C = "build_command_c:"
CONF_FLAGS_A = "build_flags_a:"
CONF_FLAGS_C = "build_flags_c:"
CONF_ASAN_FLAG = "asan_flag:"
CONF_KLEE_FLAGS_A = "klee_flags_a:"
CONF_KLEE_FLAGS_C = "klee_flags_c:"
CONF_DIFF_SIZE = "diff_size:"

# ----------------- KEY DEFINITIONS -------------------

KEY_DURATION_TOTAL = 'run-time'
KEY_DURATION_INITIALIZATION = 'initialization'
KEY_DURATION_BUILD_ANALYSIS = "build-analysis"
KEY_DURATION_DIFF_ANALYSIS = 'diff-analysis'
KEY_DURATION_CLONE_ANALYSIS = "clone-analysis"
KEY_DURATION_EXTRACTION = "clone-analysis"
KEY_DURATION_MAP_GENERATION = "map-generation"
KEY_DURATION_SLICE = "slice"
KEY_DURATION_FUNCTION_MATCH = "match-functions"
KEY_DURATION_VARIABLE_MATCH = "match-variables"
KEY_DURATION_TRANSLATION = 'translation'
KEY_DURATION_TRANSPLANTATION = "transplantation"
KEY_DURATION_VERIFICATION = 'verification'
KEY_DURATION_EXPLOIT_GENERATION = 'exploitation'


# ---------------- ARGUMENTS ---------------------------
ARG_CONF_FILE = "--conf="
ARG_DEBUG = "--debug"
ARG_SKIP_WEAVE = "--skip-weave"
ARG_SKIP_SLICE = "--skip-slice"
ARG_SKIP_ANALYSE = "--skip-analyse"
ARG_SKIP_VERIFY = "--skip-verify"
ARG_SKIP_RESTORE = "--skip-restore"
ARG_ONLY_VERIFY = "--only-verify"


# ----------------- TOOLS --------------------------------
TOOL_VECGEN = "third-party/deckard/cvecgen_fail "
TOOL_VECGEN_ORIG = "third-party/deckard/cvecgen "

PATCH_COMMAND = "patchweave-patch"
PATCH_SIZE = "1000"
DIFF_COMMAND = "crochet-diff "
DIFF_SIZE = "1000"
SYNTAX_CHECK_COMMAND = "clang-check "
STYLE_FORMAT_COMMAND = "clang-format -style=LLVM "

crash_word_list = ["abort", "core dumped", "crashed", "exception"]
error_word_list = ["runtime error", "buffer-overflow", "unsigned integer overflow"]

UPDATEMOVE = "UpdateMove"
UPDATE = "Update"
MOVE = "Move"
INSERT = "Insert"
DELETE = "Delete"
MATCH = "Match"
TO = " to "
AT = " at "
INTO = " into "
AND = "and"
order = [UPDATE,DELETE,UPDATEMOVE, MOVE, INSERT]