#! /usr/bin/env python3
# -*- coding: utf-8 -*-


from app.tools import oracle


def compare_test_output(output_c, output_d):
    return_code_c, program_crashed_c, program_output_c = output_c
    return_code_d, program_crashed_d, program_output_d = output_d
    # print(output_c)
    # print(output_d)
    if str(program_output_c) == str(program_output_d):
        return 0
    else:
        if program_crashed_c:
            if program_crashed_d:
                if return_code_c == return_code_d:
                    if oracle.any_runtime_error(program_output_c):
                        if oracle.any_runtime_error(program_output_d):
                            return 0
                        else:
                            return 1
                    else:
                        if oracle.any_runtime_error(program_output_d):
                            return -1
                        else:
                            return 0
                else:
                    print(program_output_c)
                    print(program_output_d)
                    return -1
            else:
                return 1

        else:
            if program_crashed_d:
                print(program_output_c)
                print(program_output_d)
                exit(1)
            else:
                if return_code_c == return_code_d:
                    if oracle.any_runtime_error(program_output_c):
                        if oracle.any_runtime_error(program_output_d):
                            program_output_c = "\n".join(program_output_c)
                            program_output_d = "\n".join(program_output_d)
                            runtime_error_count_c = program_output_c.count("runtime error")
                            runtime_error_count_d = program_output_d.count("runtime error")
                            # print(runtime_error_count_c, runtime_error_count_d)
                            if runtime_error_count_d < runtime_error_count_c:
                                return 1
                            else:
                                return 0
                        else:
                            return 1
                    else:
                        if oracle.any_runtime_error(program_output_d):
                            return -1
                        else:
                            return 0
                else:
                    if oracle.any_runtime_error(program_output_c):
                        if oracle.any_runtime_error(program_output_d):
                            program_output_c = "\n".join(program_output_c)
                            program_output_d = "\n".join(program_output_d)
                            runtime_error_count_c = program_output_c.count("runtime error")
                            runtime_error_count_d = program_output_d.count("runtime error")
                            # print(runtime_error_count_c, runtime_error_count_d)
                            if runtime_error_count_d < runtime_error_count_c:
                                return 1
                            else:
                                return 0
                        else:
                            return 1
                    else:
                        if oracle.any_runtime_error(program_output_d):
                            return -1
                        else:
                            return 0
                    # print(program_output_c)
                    # print(program_output_d)
                    # return -1

