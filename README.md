# FixMorph

FixMorph is a tool to automatically morph fixes (patches) from one program version to
different yet syntactically similar program version. Component-oriented programming
enables ad-hoc and low-cost code integration from multiple sources, which has a negative connotations because 
it requires developers to port changes and bug fixes from peer projects during software evolution. Adding features and
fixing bugs often requires systematic edits that are similar but not identical changes to many code locations. Finding 
such locations and making the correct edit is a tedious and error-prone process for developers. FixMorph can 
help automate this process. 

FixMorph is a powerful morphing tool for C source-codes. FixMorph is:

* Scalable: FixMorph can reliably backport large/complex source bases such as the Linux Kernel
* Compilable: The morphed patch is verified to be syntax-error-free
* Extensible: FixMorph is designed so that it can be easily extended to support advance transformations/components




# Building
Building FixMorph is very easy with the provided Dockerfile which has all the build dependencies and libraries required
for the source-to-source transformation. There are two versions of the Dockerfile we provide

* Dockerfile: This will build the environment necessary to run the stand-alone tool
* Dockerfile.experiments: This environment includes all necessary dependencies to re-produce the experiments

You can use the following command to build the image:
```
docker build -f Dockerfile -t fixmorph .
```

# Example Usage
FixMorph requires a configuration file which specifies the source code path to the donor program and
the target program. Following is an example configuration file in the provided test cases.

```c
path_a:/fixmorph/tests/update/assignment/PA
path_b:/fixmorph/tests/update/assignment/PB
path_c:/fixmorph/tests/update/assignment/PC
config_command_a:skip
config_command_c:skip
```

Once you setup a configuration file as above you can use the following command to run FixMorph which will 
transplant the patch from donor to target program.

``
python3.6 FixMorph.py --conf=/path/to/conf/file
``

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

Transplanted  Patch to target program PC:

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