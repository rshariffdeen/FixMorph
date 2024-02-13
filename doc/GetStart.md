# Getting Started
Let's walk through a simple example (a Hello World!) to understand how to use FixMorph. We consider the example code given at tests/insert/goto-label directory.
This is an example of a code-evolution, where the original patch inserts an if-condition with 2 goto labels. Applying
the same fix to another similar version, requires to adapt the two goto statements in two ways, 1) the first goto label should be
renamed and 2) the second goto label is missing in the context hence need to be transplanted. FixMorph can automate both 
these changes, and we will show in the following steps how to achieve this. 



## Code for Pa
```c
int main(void)
{
	int a;
	scanf("%d", &a);
	int fib_number = fib(a);
	test:
	    printf("fib number is %d", fib_number);
	error:
	    return -1;
	return 0;
}

```

## Code for Pb
```c
int main(void)
{
	int a;
	scanf("%d", &a);
	int fib_number = fib(a);
	if (fib_number > 0)
	    goto test;
	else if (fib_number == 5)
	    goto error;
	test:
	    printf("fib number is %d", fib_number);
	error:
	    return -1;
	return 0;
}

```
Let's check the diff to observe the original patch

### Code diff Pa-Pb
```c
> 	if (fib_number > 0)
> 	    goto test;
> 	else if (fib_number == 5)
> 	    goto error;
```

Our goal is to apply the same patch to a syntactically similar but different code Pc and obtain the evolved code for Pc.
Following is the code for Pc:

## Code for Pc
```c
int main(void)
{
	int a;
	scanf("%d", &a);
	int fib_number = fib(a);
	test_c:
	    printf("fib number is %d", fib_number);
	return 0;
}
```
Observe in the above example of Pc,  the label for "test" in Pc is "test_c" and there is no label "error" as expected
in the original patch. 

Note that no annotation/instrumentation is required for the transformation, we simply need to create a configuration file
for FixMorph that tells where to locate Pa, Pb, and Pc. Following is an example configuration file:

### Configuration File
```
path_a:/opt/fixmorph/tests/insert/goto-label/PA
path_b:/opt/fixmorph/tests/insert/goto-label/PB
path_c:/opt/fixmorph/tests/insert/goto-label/PC
config_command_a:skip
config_command_c:skip
```

In the above configuration file we specify the path for each directory and in addition we should provide the custom_config
and custom_build commands that should be used to compile the program for verification. If nothing is provided FixMorph will 
use default built-in build commands. In our example we use 'skip' for configuration command since there is no configuration 
script available for this example. Note that we didn't specify a custom_build command, we have placed
a Makefile in each directory such that FixMorph can directly invoke "make"

### Running FixMorph
Now that we have setup everything, we run FixMorph to backport/transplant the patch from Pa-Pb to Pc

    fixmorph --conf=path/to/conf/file

### Analysing Results
FixMorph was able to successfully generate an updated version of the target program from the transformation learnt from the
reference program. During this process FixMorph produces several files and we will analyse each below:

* /opt/fixmorph/logs/TAG_ID directory stores all logs, the "TAG_ID" should be specified in the configuration file
	* log-latest: this is the main application log which captures each step of the program transformation
	* log-error: this log captures any errors (if observed), which can be use for debugging purpose
	* log-make: this log captures the output of the build process of each program
* /opt/fixmorph/output/TAG_ID directory stores all artefacts generated for the transformation, the "TAG_ID" should be specified in the configuration file
	* orig-diff: this file captures the transformation in the reference program
	* transplant-diff: this file captures the transformation applied to the target program
	* port-diff: this file captures the transformation done in manual (comparison phase will run only if an additional version of target program "Pe" is provided in configuration)
	* vector-map: this file shows the mapping for the function/source files
	* namespace-map-global: this file shows the generated global mapping for each function/slice mapped


To better explore the final outcome, please check the FixMorph output directory which is in
/opt/fixmorph/output/<tag_id>  i.e. /opt/fixmorph/output/update-test
Similarly, the logs are also stored in /opt/fixmorph/logs/<tag_id>.

### Morphed Fix / Adapted Patch
```c
17a18,22
>  if (fib_number > 0)
> 	goto test_c;
>  else if (fib_number == 5)
> 	goto error;
>
19a25,27
>  error:
> 	return -1;
> 
```

More examples can be found in our "tests" directory which illustrates
the capabilities of FixMorph in different scenarios. 
