import os
import sys
import subprocess

FILE_SEARCH_OUTPUT = "file-list"
source_dir = sys.argv[1]

search_command = "find " + source_dir + " -name \"*.c\" > " + FILE_SEARCH_OUTPUT
# print(search_command)
process = subprocess.Popen([search_command], stdout=subprocess.PIPE, shell=True)
(output, error) = process.communicate()

file_list = list()
with open(FILE_SEARCH_OUTPUT, 'r') as read_file:
    file_list = read_file.readlines()

# print(file_list)
for source_file in file_list:
    format_command = "clang-tidy -fix -checks=\"readability-braces-around-statements\" " + source_file
    print(format_command)
    process = subprocess.Popen([format_command], stdout=subprocess.PIPE, shell=True)
    (output, error) = process.communicate()
