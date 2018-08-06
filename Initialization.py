#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
from Utils import err_exit, clean
import Project
import Common
import Print


def initialize():

    Print.title("Initializing project for Transplantation")
    if len(sys.argv) > 1:
        Common.CONF_FILE_NAME = sys.argv[1]

    with open(Common.CONF_FILE_NAME, 'r', errors='replace') as conf_file:
        args = [i.strip() for i in conf_file.readlines()]

    if len(args) < 3:
        err_exit("Insufficient arguments: Pa, Pb, and Pc source paths required.")

    Common.Pa = Project.Project(args[0], "Pa")
    Common.Pb = Project.Project(args[1], "Pb")
    Common.Pc = Project.Project(args[2], "Pc")

    if len(args) >= 4:
        if os.path.isfile(args[3]):
            if len(args[3]) >= 4 and args[3][:-3] == ".sh":
                crash = args[3]
            else:
                Print.yellow("Script must be path to a shell (.sh) file. Running anyway.")
        else:
            Print.yellow("No script for crash provided. Running anyway.")
    else:
        Print.yellow("No script for crash provided. Running anyway.")
    clean()
