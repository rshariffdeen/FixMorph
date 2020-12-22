#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from tools import logger, builder, emitter, exploiter, comparer


def run_compilation():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    builder.build_verify()


def emit_comparison(target_output, target_exit_code, repaired_target_output, repaired_target_exit_code):
    emitter.sub_sub_title("before transplantation")
    emitter.program_output(target_output)
    emitter.normal("\t\t exit code: " + str(target_exit_code))
    emitter.sub_sub_title("after transplantation")
    emitter.program_output(repaired_target_output)
    emitter.normal("\t\t exit code: " + str(repaired_target_exit_code))


def run_exploit(pc_path, exploit_command, pd_path, poc_path, prog_output_file, crash_word_list):

    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())

    emitter.sub_sub_title("running exploit on original program")

    target_exit_code, target_crashed, target_output = exploiter.run_exploit(exploit_command,
                                                                            pc_path,
                                                                            poc_path,
                                                                            prog_output_file)

    emitter.sub_sub_title("running exploit on repaired program")

    # Builder.build_asan()
    repaired_target_exit_code, \
    repaired_target_crashed, \
    repaired_target_output = exploiter.run_exploit(exploit_command,
                                                   pd_path,
                                                   poc_path,
                                                   prog_output_file)


    # print(repaired_target_crashed, target_crashed)
    if target_crashed:
        if repaired_target_crashed:
            emit_comparison(target_output,
                            target_exit_code,
                            repaired_target_output,
                            repaired_target_exit_code
                            )
            emitter.error("\n\tprogram crashed with exit code " + str(target_exit_code))
        else:
            emit_comparison(target_output,
                            target_exit_code,
                            repaired_target_output,
                            repaired_target_exit_code
                            )
            emitter.success("\n\tprogram was repaired!!")
    else:
        runtime_error_count_c = target_output.count("runtime error")
        runtime_error_count_d = repaired_target_output.count("runtime error")

        if repaired_target_crashed:
            emit_comparison(target_output,
                            target_exit_code,
                            repaired_target_output,
                            repaired_target_exit_code
                            )
            emitter.error("\n\tprogram crashed with exit code " + str(target_exit_code))

        if runtime_error_count_d == 0:
            emit_comparison(target_output,
                            target_exit_code,
                            repaired_target_output,
                            repaired_target_exit_code
                            )
            emitter.success("\n\tprogram was repaired!!")
        elif runtime_error_count_c <= runtime_error_count_d:
            emit_comparison(target_output,
                            target_exit_code,
                            repaired_target_output,
                            repaired_target_exit_code
                            )
            emitter.error("\n\tprogram was not repaired!!")
        else:
            emit_comparison(target_output,
                            target_exit_code,
                            repaired_target_output,
                            repaired_target_exit_code
                            )
            emitter.success("\n\tprogram partially repaired!!")


def differential_test(file_extension, input_directory, exploit_command,
                      project_c_path, project_d_path, output_directory):

    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\tanalyzing fuzz inputs")
    count = 100
    fixes = 0
    errors = 0
    for i in range(0, 100):
        file_path = input_directory + "/" + str(i) + "." + file_extension
        log_file_name_c = output_directory + "/" + str(i) + "-c"
        pc_output = exploiter.run_exploit(exploit_command,
                                          project_c_path,
                                          file_path,
                                          log_file_name_c,
                                          True)

        log_file_name_d = output_directory + "/" + str(i) + "-d"
        pd_output = exploiter.run_exploit(exploit_command,
                                          project_d_path,
                                          file_path,
                                          log_file_name_d,
                                          True)

        result = comparer.compare_test_output(pc_output, pd_output)

        if result == 1:
            fixes += 1
        elif result == -1:
            errors += 1

    emitter.normal("\t\tTotal test: " + str(count))
    emitter.normal("\t\tTotal test that passed only in Pd: " + str(fixes))
    emitter.normal("\t\tTotal test that failed only in Pd: " + str(errors))

    logger.information("\t\tTotal test: " + str(count))
    logger.information("\t\tTotal test that passed only in Pd: " + str(fixes))
    logger.information("\t\tTotal test that failed only in Pd: " + str(errors))

    return fixes, errors