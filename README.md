# FixMorph
[![Docker Pulls](https://img.shields.io/docker/pulls/rshariffdeen/fixmorph.svg)](https://hub.docker.com/r/rshariffdeen/fixmorph) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4764704.svg)](https://doi.org/10.5281/zenodo.4764704)

![Artifact Available](https://www.acm.org/binaries/content/gallery/acm/publications/replication-badges/artifacts_available_dl.jpg) ![Artifact Functional](https://github.com/user-attachments/assets/f38134ea-964b-4784-b05d-a4faf99eff14) ![Artifact Reusable](https://www.acm.org/binaries/content/gallery/acm/publications/replication-badges/artifacts_evaluated_reusable_dl.jpg)




FixMorph is a tool to automatically morph fixes (patches) from one program version to a different yet syntactically similar program version. To support users with different feature/stability requirements, many software systems (e.g. Linux Kernel) actively maintain multiple versions. When adding features and fixing bugs in the mainline version by introducing patches, the patches need to be backported to old stable versions. Patch backporting is a tedious and error-prone process for developers. FixMorph can help automate this process.

FixMorph is a morphing tool for C source codes. FixMorph is:

* Scalable: FixMorph can backport bug-fixing patches in large/complex source bases such as the Linux Kernel
* Compilable: The morphed patch is verified to be free of syntax errors
* Extensible: FixMorph is designed so that it can be easily extended to support advanced transformations

Note: See the [Experiment Guide](experiments/ISSTA21/README.md) to replicate the experiments for ISSTA'21. 


# Building
[comment]: <> (We provide two options to build FixMorph: &#40;1&#41; build from source, &#40;2&#41; build using Dockerfile.)

[comment]: <> (## Build from source code)

[comment]: <> (TO appear)

## Dependencies
* LLVM - 17.0.3+
* Clang - 17.0.3+
* [Clang Extra Tools](https://github.com/rshariffdeen/clang-tools)
* Python - 3.11+
* Docker - 20.10.1+


## Build using Dockerfile

Building FixMorph is easy with the provided Dockerfile, which has all the build dependencies and libraries required. We provide two Dockerfiles

* Dockerfile: This will build the environment necessary to run the stand-alone tool
* experiments/ISSTA21/Dockerfile: This environment includes all necessary dependencies to reproduce the experiments

You can use the following command to build fixmorph image:

```bash
cd FixMorph
docker build -t rshariffdeen/fixmorph .
# start docker
docker run -it rshariffdeen/fixmorph /bin/bash              
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
fixmorph --conf=/path/to/conf/file
```

The backported will be generated at ./tests/update/assignment/PC-patch directory. In this example, the original patch from mainline version PA-PB:
```diff
18c18
< min = rank;
---
> min = book_id;
21,22c21,22
<   if (list[j].rank < min) {
< min = list[j].rank;
---
>   if (list[j].book_id < min) {
> min = list[j].book_id;
```

The backported patch to target version PC is as follows:

```diff
18c18
< minimum = rank;
---
> minimum = author_id;
21,22c21,22
<   if (author_list[b].rank < minimum) {
< minimum = author_list[b].rank;
---
>   if (author_list[b].user_id < minimum) {
> minimum = author_list[b].user_id;
```


If you prefer changes to display in unified diff format, use the additional flag "--format=unified".

```diff
--- /opt/fixmorph/tests/update/assignment/PC/selection-sort.c	
+++ /opt/fixmorph/tests/update/assignment/PC-patch/selection-sort.c	
@@ -15,11 +15,11 @@
 while (a < length) {
    author_id = author_list[a].user_id;
    rank = author_list[a].rank;
-   minimum = rank;
+   minimum = author_id;
    position = a;
    for (b = a + 1; b < length; b++) {
-      if (author_list[b].rank < minimum) {
-         minimum = author_list[b].rank;
+      if (author_list[b].user_id < minimum) {
+         minimum = author_list[b].user_id;
    position = b;
    }
 }
```

Many such examples are included in the 'tests' directory, simply replace the configuration file path and run the same command as above.

# Limitations #
* Current implementation is based on LLVM/Clang, and thus inherits the limitations of that framework. 
* Specific build configurations such as compiler directives / runtime configurations need to be provided as input to obtain the correct AST, an incomplete AST could result in an incomplete/incorrect transformation. 
* FixMorph cannot simultaneously edit changes to source locations with contradicting compiler directives (#ifdefs)


## Bugs ##
FixMorph should be considered alpha-quality software. Bugs can be reported here:

    https://github.com/rshariffdeen/FixMorph/issues

## Documentation ##

* [Getting Started](doc/GetStart.md)
* [Example Usage](doc/Examples.md)
* [ISSTA'21 Experiment Replication](experiments/ISSTA21/README.md)  
* [Manual](doc/Manual.md)

# Contributions 
We welcome contributions to improve this work, see [details](doc/Contributing.md)

## Developers ##
* Ridwan Shariffdeen
* Gao Xiang

## Publication ##
**Automated Patch Backporting in Linux (Experience Paper)** <br>
Ridwan Shariffdeen, Xiang Gao, Gregory J. Duck, Shin Hwei Tan, Julia Lawall, Abhik Roychoudhury <br>
International Symposium on Software Testing and Analysis (ISSTA), 2021

## Acknowledgements ##
This work was partially supported by the National Satellite of Excellence in Trustworthy Software Systems, funded by National Research Foundation (NRF) Singapore. 


# License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Citation

If you use Cerberus in your research work, we would highly appreciate it if you
cited the [following paper](https://rshariffdeen.com/paper/ISSTA21.pdf):

```
@inproceedings{fixmorph,
author = {Shariffdeen, Ridwan and Gao, Xiang and Duck, Gregory J. and Tan, Shin Hwei and Lawall, Julia and Roychoudhury, Abhik},
title = {Automated patch backporting in Linux (experience paper)},
year = {2021},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3460319.3464821},
doi = {10.1145/3460319.3464821},
booktitle = {Proceedings of the 30th ACM SIGSOFT International Symposium on Software Testing and Analysis},
pages = {633–645},
numpages = {13},
keywords = {Linux Kernel, Patch Backporting, Program Transformation},
location = {Virtual, Denmark},
series = {ISSTA 2021}
}
```
