# Manual #
FixMorph is a program transformation tool for C/C++ programs. It generates a list of transformation edits
that is learnt from a given reference specification and adapts the transformation, to match the target program context. It requires as input; 
the before and after transformation versions of the reference program and the target program which the adapted transformation should be applied to. 

 ## Usage ##
FixMorph requires a configuration file as input which provides values as following:

    tag_id:    a reference ID which will be used to store logs/tmp/output of the transformation process
    path_a:    absolute path to the directory Pa (before-transformation version of reference/donor program)
    path_b:    absolute path to the directory Pb (after-transformation version of reference/donor program)
    path_c:    absolute path to the directory Pc (target/host program)
    path_e:    for experimental comparison, absolute path to the directory Pe (manual ported version of target/host program)
    config_command_a: configuration command for the reference/donor program
    config_command_c: configuration command for the  target/host program
    build_command_a: build command for the reference/donor program
    build_command_c: build command for the  target/host program


One a configuration file is specified the tool can be invoked using the following command from the directory of the tool:
```
python3.7 FixMorph.py --conf=/path/to/conf/file
```

# Runtime Configuration Options
The tool supports the following runtime configurations:

    Usage: python3.7 FixMorph.py [OPTIONS] --conf=$FILE_PATH
	Options are:
		--debug	            | enable debugging information
		--mode=             | execution mode [0: fixmorph 1: linux-patch-no-context 2: linux-patch-context 3: sydit] (default = 0)
		--context=          | context level for linux-patch-context mode


### Side effects ###

**Warning!** FixMorph executes arbitrary modifications of your source code which may lead to undesirable side effects. Therefore, it is recommended to run FixMorph in an isolated environment.
Apart from that, FixMorph produces the following side effects:

- prints log messages on the standard error output
- saves generated patch(es) in the current directory (i.e. output)
- saves intermediate data in the current directory (i.e. output/tmp)
- saves various log information in the current directory (i.e. logs)
- transforms/builds/tests the provided project

Typically, it is safe to execute FixMorph consequently on the same copy of the project (without `make clean`), however idempotence cannot be guaranteed.
After FixMorph terminates successfully, it restores the original source files, but does not restore files generated/modified by the tests and the build system.
If FixMorph does not terminate successfully (e.g. by receiving `SIGKILL`), the source tree is likely to be corrupted.