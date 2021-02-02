# FixMorph

FixMorph is a tool to automatically morph fixes (patches) from one program version to
different yet syntactically similar program version. Component-oriented programming
enables ad-hoc and low-cost code integration from multiple sources, which has a negative connotations because 
it requires developers to port changes and bug fixes from peer projects during software evolution. Adding features and
fixing bugs often requires systematic edits that are similar but not identical changes to many code locations. Finding 
such locations and making the correct edit is a tedious and error-prone process for developers. FixMorph can 
help you automate the process. 

FixMorph is a powerful morphing tool for C source-codes. FixMorph is:

* Scalable: FixMorph can reliably backport large/complex source bases such as the Linux Kernel
* Compilable: The morphed patch is verified to be syntax-error-free
* Extensible: FixMorph is designed so that it can be easily extended to support advance transformations/components




