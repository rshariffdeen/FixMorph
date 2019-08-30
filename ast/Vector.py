# -*- coding: utf-8 -*-

from tools import Logger, Emitter
import sys
from common.Utilities import execute_command, error_exit
import os


class Vector:
    deckard_path = "third-party/Deckard/cvecgen_fail "
    deckard_path_2 = "third-party/Deckard/cvecgen "
    # deckard_vecs = dict()
    vid = 0

    def __init__(self, file_path, function_name, start_line, end_line, is_deckard=True):
        # self.project = project
        self.file_path = file_path
        self.function_name = function_name
        self.start_line = start_line
        self.end_line = end_line
        self.variables = []
        if self.function_name is not None:
            self.vector_path = self.file_path + "." + self.function_name + ".vec"
        else:
            self.vector_path = self.file_path + ".vec"
        self.vector = None
        if is_deckard:
            self.vector = self.generate_deckard_vec()
        # if proj.name not in ASTVector.deckard_vecs.keys():
        #    ASTVector.deckard_vecs[proj.name] = list()
        # ASTVector.deckard_vecs[proj.name].append(self.vector)
        self.id = Vector.vid
        Vector.vid += 1

    def generate_deckard_vec(self):
        Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
        if self.function_name is None:
            command = "echo " + self.vector_path + " >> output/errors; " + \
                      Vector.deckard_path + " " + self.file_path + " -o " + \
                      self.vector_path + " 2> output/errors"
        else:
            current = "\t\t" + self.function_name + " " + str(self.start_line) + "-" + \
                      str(self.end_line)
            Emitter.information("generating vector for " + str(current))
            start_line = self.start_line
            end_line = self.end_line
            with open(self.file_path, 'r') as source_file:
                ls = source_file.readlines()
                max_line = len(ls)
                if int(end_line) > max_line:
                    # TODO: This shouldn't happen!
                    Emitter.error(current)
                    error_exit("Deckard failed. The following file not generated:", self.vector_path)
                    return None
            self.start_line = start_line
            self.end_line = end_line

            command = "echo " + self.vector_path + "\n >>  output/errors; "
            command += Vector.deckard_path + " --start-line-number " + \
                       str(self.start_line) + " --end-line-number " + str(self.end_line) + \
                       " " + self.file_path + " -o " + self.vector_path + \
                       " 2> output/errors"

        try:
            execute_command(command)
        except Exception as exception:
            error_exit(exception, "Error with Deckard vector generation. Exiting...")

        if not os.path.isfile(self.vector_path):
            if self.function_name is None:
                c1 = "echo " + self.vector_path + " >> output/errors; " + \
                     Vector.deckard_path_2 + " " + self.file_path + " -o " + \
                     self.vector_path + " 2> output/errors"
            else:
                c1 = "echo " + self.vector_path + "\n >>  output/errors; "
                c1 += Vector.deckard_path_2 + " --start-line-number " + \
                      str(self.start_line) + " --end-line-number " + \
                      str(self.end_line) + " " + self.file_path + " -o " + \
                      self.vector_path + " 2> output/errors"
            try:
                execute_command(c1, False)
            except Exception as e:
                error_exit(e, "Error with Deckard vector generation. Exiting...")

        if not os.path.isfile(self.vector_path):
            Emitter.warning("Deckard fail. The vector file was not generated:")
            Emitter.warning(self.vector_path + "\n")
            with open('output/reproduce_errors', 'a') as file:
                file.write(command + "\n" + c1 + "\n")
            return None

        with open(self.vector_path, 'r') as vec_file:
            first = vec_file.readline()
            if first:
                v = [int(s) for s in vec_file.readline().strip().split(" ")]
                print(v)
                v = Vector.normed(v)
                return v

    def norm(v):
        return sum(v[i] ** 2 for i in range(len(v))) ** (1 / 2)

    def normed(v):
        n = Vector.norm(v)
        return [i / n for i in v]

    def dist(u, v):
        assert (len(u) == len(v))
        return sum(((u[i] - v[i]) ** 2) for i in range(len(u)))

    def file_dist(file1, file2, normed=True):
        with open(file1, 'r') as f1:
            v = f1.readline()
            if v:
                v = [int(i) for i in f1.readline().strip().split(" ")]
                if normed:
                    v = Vector.normed(v)

        with open(file2, 'r') as f2:
            u = f2.readline()
            if v:
                u = [int(i) for i in f2.readline().strip().split(" ")]
                if normed:
                    u = Vector.normed(u)

        return Vector.dist(u, v)
