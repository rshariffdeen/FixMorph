# FixMorph
[![Docker Pulls](https://img.shields.io/docker/pulls/rshariffdeen/fixmorph.svg)](https://hub.docker.com/r/rshariffdeen/fixmorph)

FixMorph is a tool to automatically morph fixes (patches) from one program version to a
different yet syntactically similar program version. Component-oriented programming
enables ad-hoc and low-cost code integration from multiple sources, which has a negative connotations because 
it requires developers to port changes and bug fixes from peer projects during software evolution. Adding features and
fixing bugs often requires systematic edits that are similar but not identical changes to many code locations. Finding 
such locations and making the correct edit is a tedious and error-prone process for developers. FixMorph can 
help automate this process. 

FixMorph is a powerful morphing tool for C source-codes. FixMorph is:

* Scalable: FixMorph can backport bug-fixing patches in large/complex source bases such as the Linux Kernel
* Compilable: The morphed patch is verified to be free of syntax errors
* Extensible: FixMorph is designed so that it can be easily extended to support advanced transformations




# Building
Building FixMorph is easy with the provided Dockerfile, which has all the build dependencies and libraries required. We provide two versions of the Dockerfile

* Dockerfile: This will build the environment necessary to run the stand-alone tool
* Dockerfile.experiments: This environment includes all necessary dependencies to reproduce the experiments

You can use the following command to build the image:

```bash
cd /FixMorph
docker build -t rshariffdeen/fixmorph:16.04 .
```

# Example Usage
FixMorph requires a configuration file that specifies the source code path to the donor program and
the target program. Following is an example configuration file in the provided test cases.

```c
path_a:/fixmorph/tests/update/assignment/PA
path_b:/fixmorph/tests/update/assignment/PB
path_c:/fixmorph/tests/update/assignment/PC
config_command_a:skip
config_command_c:skip
```

Once a configuration file has been set up as above, the following command will run FixMorph to 
adapt the patch from the reference program to target program.

```bash

python3.7 FixMorph.py --conf=/path/to/conf/file
```

Original Patch from donor program PA-PB:
```c
    18c18
    <     min = rank;
    ---
    >     min = book_id;
    21,22c21,22
    <       if (list[j].rank < min) {
    <         min = list[j].rank;
    ---
    >       if (list[j].book_id < min) {
    >         min = list[j].book_id;
```

Adapted  Patch to target program PC:

```c
    18c18
    <     minimum = rank;
    ---
    >     minimum = author_id;
    21,22c21,22
    <       if (author_list[b].rank < minimum) {
    <         minimum = author_list[b].rank;
    ---
    >       if (author_list[b].user_id < minimum) {
    >         minimum = author_list[b].user_id;
```
Many such examples are included in the 'tests' directory, simply replace the configuration file path and run the same
command as above. 


## Documentation ##

* [Getting Started](doc/GetStart.md)
* [Example Usage](doc/Examples.md)
* [ISSTA'21 Experiment Replication](experiments/new/README.md)  
* [Manual](doc/Manual.md)


## Developers
* Ridwan Shariffdeen
* Gao Xiang


# License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
