import cs
import os
import sys

project = ''
proj_dir = ''

def initialize_project():
    project = cs.project.current()
    proj_dir = sys.argv[1]
    return


def run():
    name = project.name()
    os.system("echo '" + proj_dir + "/ " + name + "' > test")
    os.system("touch /home/ridwan/workspace/research-work/patch-transplant/crochet/test.test")

    return


run()

