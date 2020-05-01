#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os


# ------------------- Directories --------------------

DIRECTORY_MAIN = os.getcwd()
DIRECTORY_LOG_BASE = DIRECTORY_MAIN + "/logs"
DIRECTORY_LOG = ""
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
FILE_ERROR_LOG = ""
FILE_LAST_LOG = ""
FILE_MAKE_LOG = ""
FILE_COMMAND_LOG = ""
FILE_STANDARD_FUNCTION_LIST = DIRECTORY_DATA + "/standard-function-list"
FILE_STANDARD_MACRO_LIST = DIRECTORY_DATA + "/standard-macro-list"

FILE_AST_SCRIPT = DIRECTORY_TMP + "/ast-script"
FILE_TEMP_DIFF = DIRECTORY_TMP + "/temp_diff"
FILE_AST_MAP = DIRECTORY_TMP + "/ast-map"
FILE_AST_DIFF_ERROR = DIRECTORY_TMP + "/errors_ast_diff"
FILE_PARTIAL_PATCH = DIRECTORY_TMP + "/gen-patch"


FILE_DIFF_INFO = ""
FILE_ORIG_DIFF_INFO = ""
FILE_PORT_DIFF_INFO = ""
FILE_TRANSPLANT_DIFF_INFO = ""
FILE_ORIG_DIFF = ""
FILE_PORT_DIFF = ""
FILE_TRANSPLANT_DIFF = ""
FILE_CLONE_INFO = ""
FILE_SCRIPT_INFO = ""
FILE_MAP_INFO = ""
FILE_TRANSLATED_SCRIPT_INFO = ""
FILE_COMPARISON_RESULT = ""
FILE_TEMP_TRANSFORM = DIRECTORY_TMP + "/temp-transform"

FILE_PROJECT = ""
FILE_PROJECT_A = ""
FILE_PROJECT_B = ""
FILE_PROJECT_C = ""
FILE_PROJECT_D = ""
FILE_PROJECT_E = ""


FILE_EXCLUDED_EXTENSIONS = DIRECTORY_TMP + "/excluded-extensions"
FILE_EXCLUDED_EXTENSIONS_A = DIRECTORY_TMP + "/excluded-extensions-a"
FILE_EXCLUDED_EXTENSIONS_B = DIRECTORY_TMP + "/excluded-extensions-b"
FILE_GIT_UNTRACKED_FILES = DIRECTORY_TMP + "/untracked-list"
FILE_DIFF_C = DIRECTORY_TMP + "/diff_C"
FILE_DIFF_H = DIRECTORY_TMP + "/diff_H"
FILE_DIFF_ALL = DIRECTORY_TMP + "/diff_all"
FILE_FIND_RESULT = DIRECTORY_TMP + "/find_tmp"


# ------------------- Configuration --------------------

CONF_PATH_A = "path_a:"
CONF_PATH_B = "path_b:"
CONF_PATH_C = "path_c:"
CONF_PATH_E = "path_e:"
CONF_COMMIT_A = "commit_a:"
CONF_COMMIT_B = "commit_b:"
CONF_COMMIT_C = "commit_c:"
CONF_COMMIT_E = "commit_e:"
CONF_PATH_POC = "path_poc:"
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
CONF_VC = "version-control:"


# ----------------- KEY DEFINITIONS -------------------

KEY_DURATION_TOTAL = 'run-time'
KEY_DURATION_INITIALIZATION = 'initialization'
KEY_DURATION_BUILD_ANALYSIS = "build-analysis"
KEY_DURATION_SUMMARIZATION = "summarize-analysis"
KEY_DURATION_COMPARISON = "comparison-analysis"
KEY_DURATION_DIFF_ANALYSIS = 'diff-analysis'
KEY_DURATION_SEGMENTATION = 'segmentation'
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
ARG_BACKPORT = "--backport"
ARG_FORK = "--fork"
ARG_LINUX_KERNEL = "--linux-kernel"
ARG_SKIP_WEAVE = "--skip-weave"
ARG_SKIP_SUMMARY = "--skip-summary"
ARG_SKIP_COMPARE = "--skip-compare"
ARG_SKIP_SEGMENT = "--skip-segment"
ARG_SKIP_VERIFY = "--skip-verify"
ARG_SKIP_RESTORE = "--skip-restore"
ARG_ONLY_VERIFY = "--only-verify"
ARG_ONLY_COMPARISON = "--only-compare"
ARG_ONLY_SUMMARIZE = "--only-summary"
ARG_ONLY_BUILD = "--only-build"
ARG_ONLY_WEAVE = "--only-weave"
ARG_SKIP_BUILD = "--skip-build"
ARG_SKIP_VEC_GEN = "--skip-vec-gen"
ARG_SKIP_DETECTION = "--skip-detection"
ARG_SKIP_DIFFERENCE = "--skip-diff"
ARG_SKIP_EXTRACTION = "--skip-extraction"
ARG_SKIP_MAPPING = "--skip-mapping"
ARG_SKIP_TRANSLATION = "--skip-trans"
ARG_ONLY_ANALYSE = "--only-analyse"

# ----------------- TOOLS --------------------------------
TOOL_VECGEN = "third-party/deckard/cvecgen_fail "
TOOL_VECGEN_ORIG = "third-party/deckard/cvecgen "

APP_AST_DIFF = "crochet-diff"
PATCH_COMMAND = "crochet-patch"
PATCH_SIZE = "1000"
DIFF_COMMAND = "crochet-diff "
DIFF_SIZE = "1000"
SYNTAX_CHECK_COMMAND = "clang-check "
STYLE_FORMAT_COMMAND = "clang-format -style=LLVM "

crash_word_list = ["abort", "core dumped", "crashed", "exception", "dumped core"]
error_word_list = ["runtime error", "buffer-overflow", "unsigned integer overflow"]

UPDATEMOVE = "UpdateMove"
UPDATE = "Update"
MOVE = "Move"
INSERT = "Insert"
DELETE = "Delete"
MATCH = "Match"
REPLACE = "Replace"
TO = " to "
AT = " at "
INTO = " into "
AND = "and"
WITH = " with "
order = [DELETE, INSERT, UPDATE, UPDATEMOVE, MOVE]
