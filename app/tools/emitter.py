# -*- coding: utf-8 -*-

import sys
import os
from app.common import definitions, values
from app.tools import logger
import textwrap


GREY = '\t\x1b[1;30m'
RED = '\t\x1b[1;31m'
GREEN = '\x1b[1;32m'
YELLOW = '\t\x1b[1;33m'
BLUE = '\t\x1b[1;34m'
ROSE = '\t\x1b[1;35m'
CYAN = '\x1b[1;36m'
WHITE = '\t\x1b[1;37m'

PROG_OUTPUT_COLOR = '\t\x1b[0;30;47m'
STAT_COLOR = '\t\x1b[0;32;47m'
rows, columns = os.popen('stty size', 'r').read().split()


def write(print_message, print_color, new_line=True, prefix=None, indent_level=0):
    if not values.silence_emitter:
        message = "\033[K" + print_color + str(print_message) + '\x1b[0m'
        if prefix:
            prefix = "\033[K" + print_color + str(prefix) + '\x1b[0m'
            len_prefix = ((indent_level+1) * 4) + len(prefix)
            wrapper = textwrap.TextWrapper(initial_indent=prefix, subsequent_indent=' '*len_prefix, width=int(columns))
            message = wrapper.fill(message)
        sys.stdout.write(message)
        if new_line:
            r = "\n"
            sys.stdout.write("\n")
        else:
            r = "\033[K\r"
            sys.stdout.write(r)
        sys.stdout.flush()


def title(title):
    write("\n" + "="*100 + "\n\n\t" + title + "\n" + "="*100+"\n", CYAN)
    logger.information(title)


def sub_title(subtitle):
    write("\n\t" + subtitle + "\n\t" + "_"*90+"\n", CYAN)
    logger.information(subtitle)


def sub_sub_title(sub_title):
    write("\n\t\t" + sub_title + "\n\t\t" + "-"*90+"\n", CYAN)
    logger.information(sub_title)


def command(message):
    if values.DEBUG:
        prefix = "\t\t[command] "
        write(message, ROSE, prefix=prefix, indent_level=2)
    logger.command(message)


def normal(message, jump_line=True):
    write(message, BLUE, jump_line)
    logger.information(message)


def highlight(message, jump_line=True):
    indent_length = message.count("\t")
    prefix = "\t" * indent_length
    message = message.replace("\t", "")
    write(message, WHITE, jump_line, indent_level=indent_length, prefix=prefix)
    logger.note(message)


def information(message, jump_line=True):
    if values.DEBUG_DATA:
        prefix = "\t\t[information] "
        write(message, GREY, prefix=prefix, indent_level=2)
    logger.information(message)


def statistics(message):
    write(message, WHITE)
    logger.output(message)


def error(message):
    emit_message = "\t\t[ERROR] " + message.replace("\n", "")
    write(emit_message, RED)
    logger.error(message)


def success(message):
    write(message, GREEN)
    logger.information(message)


def special(message):
    write(message, ROSE)
    logger.output(message)


def program_output(output_message):
    write("\t\tProgram Output:", WHITE)
    if type(output_message) == list:
        for line in output_message:
            write("\t\t\t" + line.strip(), PROG_OUTPUT_COLOR)
    else:
        write("\t\t\t" + output_message, PROG_OUTPUT_COLOR)


def emit_var_map(var_map):
    write("\t\tVar Map:", WHITE)
    for var_a in var_map:
        highlight("\t\t\t" + var_a + " ==> " + var_map[var_a])


def emit_ast_script(ast_script):
    for line in ast_script:
        special("\t\t" + line.strip())


def warning(message):
    append_message = message
    if "[warning]" not in message:
        append_message = "\t[warning] " + message
    write(append_message, YELLOW)
    logger.warning(message)


def debug(message):
    if values.DEBUG:
        prefix = "\t\t[debug] "
        write(message, GREY, prefix=prefix, indent_level=2)
    logger.debug(message)


def data(message, info=None):
    if values.DEBUG_DATA:
        prefix = "\t\t[data] "
        write(message, GREY, prefix=prefix, indent_level=2)
        if info:
            write(info, GREY, prefix=prefix, indent_level=2)
    logger.data(message, info)


def configuration(setting, value):
    message = "\t[config] " + setting + ": " + str(value)
    write(message, WHITE, True)
    logger.configuration(setting + ":" + str(value))


def end(time_info, is_error=False):
    if values.CONF_ARG_PASS:
        statistics("\nRun time statistics:\n-----------------------\n")
        statistics("Initialization: " + time_info[definitions.KEY_DURATION_INITIALIZATION] + " minutes")
        statistics("Build Analysis: " + time_info[definitions.KEY_DURATION_BUILD_ANALYSIS] + " minutes")
        statistics("Diff Analysis: " + time_info[definitions.KEY_DURATION_DIFF_ANALYSIS] + " minutes")
        statistics("Clone Analysis: " + time_info[definitions.KEY_DURATION_CLONE_ANALYSIS] + " minutes")
        statistics("Slicing: " + time_info[definitions.KEY_DURATION_SLICE] + " minutes")
        statistics("AST Analysis: " + time_info[definitions.KEY_DURATION_EXTRACTION] + " minutes")
        statistics("Map Generation: " + time_info[definitions.KEY_DURATION_MAP_GENERATION] + " minutes")
        statistics("Translation: " + time_info[definitions.KEY_DURATION_TRANSLATION] + " minutes")
        statistics("Evolution: " + time_info[definitions.KEY_DURATION_EVOLUTION] + " minutes")
        statistics("Transplantation: " + time_info[definitions.KEY_DURATION_TRANSPLANTATION] + " minutes")
        statistics("Verification: " + time_info[definitions.KEY_DURATION_VERIFICATION] + " minutes")
        # statistics("Reverse Transplantation: " + time_info[Definitions.KEY_DURATION_REVERSE] + " minutes")
        # statistics("Evaluation: " + time_info[Definitions.KEY_DURATION_EVALUATION] + " minutes")
        statistics("Comparison: " + time_info[definitions.KEY_DURATION_COMPARISON] + " minutes")
        statistics("Summarizing: " + time_info[definitions.KEY_DURATION_SUMMARIZATION] + " minutes")
        if is_error:
            error(values.TOOL_NAME + " exited with an error after " + time_info[definitions.KEY_DURATION_TOTAL]
                  + " minutes\n")
        else:
            success(values.TOOL_NAME + " finished successfully after " + time_info[definitions.KEY_DURATION_TOTAL]
                    + " minutes\n")


def help():
    print("Usage: python " + values.TOOL_NAME + " [OPTIONS] " + definitions.ARG_CONF_FILE + "$CONFIGURATION_FILE_PATH")

    print("Options are:")
    print("\t" + definitions.ARG_HELP + "\t| " + "displays this menu for help")
    print("\t" + definitions.ARG_DEBUG + "\t| " + "enable debugging information")
    print("\t" + definitions.ARG_TIMEOUT + "\t| " + "timeout in minutes (default=60)")
    print("\t" + definitions.ARG_OPERATION_MODE + "\t| " + "select which tool/mode to run for backport {0: fixmorph, 1: patch, 2: patch-context, 3: sydit}")
    print("\t" + definitions.ARG_CONTEXT_LEVEL + "\t| " + "set context level for patch-context mode")
    print("\t" + definitions.ARG_OUTPUT_FORMAT + "\t| " + "select the output format for the diff change {'normal', 'unified'} (default = normal)")

    print("Skip Phases\n-----------------------\n")
    print("\t" + definitions.ARG_SKIP_BUILD + "\t| " + "skip build")
    print("\t" + definitions.ARG_SKIP_SUMMARY + "\t| " + "skip diff analysis")
    print("\t" + definitions.ARG_SKIP_VEC_GEN + "\t| " + "disable vector generation")
    print("\t" + definitions.ARG_SKIP_DETECT + "\t| " + "skip clone analysis")
    print("\t" + definitions.ARG_SKIP_EXTRACT + "\t| " + "skip AST analysis")
    print("\t" + definitions.ARG_SKIP_MAP + "\t| " + "skip variable analysis")
    print("\t" + definitions.ARG_SKIP_TRANSLATE + "\t| " + "skip translation")
    print("\t" + definitions.ARG_SKIP_WEAVE + "\t| " + "skip transplant")
    print("\t" + definitions.ARG_SKIP_VERIFY + "\t| " + "skip verification")

    print("Run Only Phases\n-----------------------\n")
    print("\t" + definitions.ARG_ONLY_BUILD + "\t| " + "run only build step")
    print("\t" + definitions.ARG_ONLY_DIFF + "\t| " + "run only differentiation")
    print("\t" + definitions.ARG_ONLY_DETECT + "\t| " + "run only detection")
    print("\t" + definitions.ARG_ONLY_SLICE + "\t| " + "run only slicing")
    print("\t" + definitions.ARG_ONLY_EXTRACT + "\t| " + "run only extraction")
    print("\t" + definitions.ARG_ONLY_MAP + "\t| " + "run only mapping")
    print("\t" + definitions.ARG_ONLY_TRANSLATE + "\t| " + "run only translation")
    print("\t" + definitions.ARG_ONLY_EVOLVE + "\t| " + "run only evolution")
    print("\t" + definitions.ARG_ONLY_WEAVE + "\t| " + "run only transplantation")
    print("\t" + definitions.ARG_ONLY_VERIFY + "\t| " + "run only verification")
    print("\t" + definitions.ARG_ONLY_COMPARE + "\t| " + "run only comparison")
    print("\t" + definitions.ARG_ONLY_SUMMARY + "\t| " + "run only summarize")


