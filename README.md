# FixMorph
[![Docker Pulls](https://img.shields.io/docker/pulls/rshariffdeen/fixmorph.svg)](https://hub.docker.com/r/rshariffdeen/fixmorph) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4730045.svg)](https://doi.org/10.5281/zenodo.4730045)


FixMorph is a tool to automatically morph fixes (patches) from one program version to a different yet syntactically similar program version. <!--Adding features and fixing bugs often requires systematic edits that are similar but not identical changes to many code locations. Finding such locations and making the correct edit is a tedious and error-prone process for developers.--> 
To support users with different feature/stability requirements, many software systems (e.g. Linux Kernel) actively maintain multiple versions. When adding features and fixing bugs in the mainline version by introducing patches, the patches need to be backported to old stable versions. Patch backporting is a tedious and error-prone process for developers. FixMorph can help automate this process.

FixMorph is a powerful morphing tool for C source codes. FixMorph is:

* Scalable: FixMorph can backport bug-fixing patches in large/complex source bases such as the Linux Kernel
* Compilable: The morphed patch is verified to be free of syntax errors
* Extensible: FixMorph is designed so that it can be easily extended to support advanced transformations

[comment]: <> (# Building)

[comment]: <> (We provide two options to build FixMorph: &#40;1&#41; build from source, &#40;2&#41; build using Dockerfile.)

[comment]: <> (## Build from source code)

[comment]: <> (TO appear)

## Build using Dockerfile

Building FixMorph is easy with the provided Dockerfile, which has all the build dependencies and libraries required. We provide two Dockerfiles

* Dockerfile: This will build the environment necessary to run the stand-alone tool
* experiments/ISSTA21/Dockerfile: This environment includes all necessary dependencies to reproduce the experiments

You can use the following command to build fixmorph image:

```bash
cd /FixMorph
docker build -t rshariffdeen/fixmorph:16.04 .
docker run -it rshariffdeen/fixmorph:16.04 /bin/bash              # start docker
```

The experiments/ISSTA21/Dockerfile depends on the fixmorph image. The instructions to build and execute experiments/ISSTA21/Dockerfile can be found [here](./experiments/ISSTA21).


# Example Usage
FixMorph requires a configuration file that specifies the source code path, where *path_a* and *path_b* represent the paths of the mainline version before and after introducing the patch, while *path_c* represents the path of the version to which the patch is backported. Following is an example configuration file in the provided test cases.

```c
path_a:/fixmorph/tests/update/assignment/PA
path_b:/fixmorph/tests/update/assignment/PB
path_c:/fixmorph/tests/update/assignment/PC
config_command_a:skip
config_command_c:skip
```

Once a configuration file has been set up as above, the following command will run FixMorph to adapt the patch from the mainline version to the target version.

```bash
python3.7 FixMorph.py --conf=/path/to/conf/file
```

The backported will be generated at ./tests/update/assignment/PC-patch directory. In this example, the original patch from mainline version PA-PB:
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

The backported patch to target version PC is as follows:

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
Many such examples are included in the 'tests' directory, simply replace the configuration file path and run the same command as above.


## Documentation ##

* [Getting Started](doc/GetStart.md)
* [Example Usage](doc/Examples.md)
* [ISSTA'21 Experiment Replication](experiments/ISSTA21/README.md)  
* [Manual](doc/Manual.md)

## Developers ##
* Ridwan Shariffdeen
* Gao Xiang

## Publication ##
**Automated Patch Backporting in Linux (Experience Paper)** <br>
Ridwan Shariffdeen, Xiang Gao, Gregory J. Duck, Shin Hwei Tan, Julia Lawall, Abhik Roychoudhury <br>
International Symposium on Software Testing and Analysis (ISSTA), 2021

# License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
