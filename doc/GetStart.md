# Getting Started
Let's walk through a simple example ( a Hello World!) to understand how to use FixMorph. We consider the example code given at tests/insert/goto-label directory.
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
```diff
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

Note that no annotation/instrumentation is required for the transformation, we simply need to create a configuration file
for FixMorph that tells where to locate Pa, Pb, and Pc. Following is an example configuration file:

### Configuration File
```
path_a:/fixmorph/tests/insert/goto-label/PA
path_b:/fixmorph/tests/insert/goto-label/PB
path_c:/fixmorph/tests/insert/goto-label/PC
config_command_a:skip
config_command_c:skip
```

In the above configuration file we specify the path for each directory and in addition we should provide the custom_config
and custom_build commands that should be used to compile the program for verification. If nothing is provided FixMorph will 
use default built-in build commands. In our example we use 'skip' for configuration command since there is no configuration script available. 

### Running FixMorph
Now that we have setup everything, we run FixMorph to backport/transplant the patch from Pa-Pb to Pc

    python3.7 FixMorph.py --conf=path/to/conf/file




