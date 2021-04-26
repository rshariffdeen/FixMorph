# Experiment Replication

FixMorph successfully generates correct transformation for most of the subjects in our data-set which are curated from backported
patches in the Linux Kernel project. For each transformation, we provide an url that contains the original transformation, manually ported transformation and 
the generated transformation by FixMorph at https://fixmorph.github.io. 

In our replication package, we include scripts to reproduce the experiment setup which can be evaluated using our tool. 
This directory includes scripts and Dockerfile to re-create the experiment setup, you can also use our pre-built Docker 
which can be downloaded from following repository

Dockerhub Repo: https://hub.docker.com/repository/docker/rshariffdeen/fixmorph

# Getting Started

## Building the environment
Setup environment can be built using the Dockerfile provided within, which will encompass the dependencies, configurations
and setup scripts. Use the following command:

``
docker build -t rshariffdeen/fixmorph:issta21 .
``

Note that the build process can be time-consuming, hence you can also use the pre-built docker image using the command:

``
docker pull rshariffdeen/fixmorph:issta21
``

Having the image, you can now start a Docker container. We recommend linking the container to folders in the filesystem,
so that it is possible to check the logs and generated outputs also outside of the Docker container. 

``
docker run --name FixMorph -it rshariffdeen/fixmorph:issta21 bash
``

## Test Input Files
For our example test run, we choose /FixMorph/tests/bug-types/div-zero/div-zero-1, which is a simple divide-by-zero repair. There are 3 input files provided for this 
example. 

* /FixMorph/tests/bug-types/div-zero/div-zero-1/repair.conf shows the FixMorph configuration file.
* /FixMorph/tests/bug-types/div-zero/div-zero-1/spec.smt2 shows the user-provided specification.
* /FixMorph/tests/bug-types/div-zero/div-zero-1/t1.smt2 shows the expected output for the failing test case (x=1, as defined in the repair.conf at line 7).

## Test Run
You can check if everything is working well, by running a simple test-case from our test-suite. 

``
pypy3 FixMorph.py --conf=/FixMorph/tests/bug-types/div-zero/div-zero-1/repair.conf
``

The program /FixMorph/tests/bug-types/div-zero/div-zero-1/test.c contains a simple division-by-zero error, which we want to fix with FixMorph.

### FixMorph Output
The output message at the end of the execution should look similar to the following:

	Startup: 0.003 minutes
	Build: 0.009 minutes
	Testing: 0.054 minutes
	Synthesis: 0.010 minutes
	Explore: 0.167 minutes
	Refine: 0.463 minutes
	Reduce: 0.875 minutes
	Iteration Count: 4
	Patch Start Count: 85
	Patch End Seed Count: 42
	Patch End Count: 42
	Template Start Count: 5
	Template End Seed Count: 5
	Template End Count: 5
	Paths Detected: 2
	Paths Explored: 2
	Paths Skipped: 0
	Paths Hit Patch Loc: 3
	Paths Hit Observation Loc: 2
	Paths Hit Crash Loc: 2
	Paths Crashed: 1
	Component Count: 6
	Component Count Gen: 4
	Component Count Cus: 2
	Gen Limit: 40

### Analysing Results
FixMorph performed 4 iterations with the concolic exploration.
It generated 5 abstract patches (see "Template Start Count") and ended also with 5 (see "Template End Count").
In the beginning, the 5 abstract patches represented 85 concrete patches (see "Patch Start Count").
During exploration FixMorph ruled out 43 (= 85-42) of them.

To better explore the final outcome, please check the FixMorph output directory which is in
/FixMorph/output/<tag_id> (for this example the tag_id defined in the configuration file is 'crash') i.e. /FixMorph/output/crash
Similarly, the logs are also stored in /FixMorph/logs/<tag_id>. 

This output folder will contain "patch-set-gen" and "patch-set-ranked".
"patch-set-gen" are the patches after the initial synthesis step.
"patch-set-ranked" are the patches after FixMorph finished.

Note that the order (i.e., the ranking) of the patches changed during our concolic exploration.
The correct patch would be "x+1 == 0".
FixMorph identifies "(constant_a == x)" with constant_a in [1, 1], which is semantically equivalent to the correct patch.
FixMorph ranks this patch at position 1.

For more examples refer [this guide](../doc/Examples.md)


# Running Experiments
Following details how to run the scripts and the tool to replicate the results of our experiments.
Once you build the docker image, you spin up a container as mentioned above. 

Inside the container the following directories will be used
- /FixMorph - this will be the tool directory
- /experiments - all experiment setups will be deployed in this directory


In /experiments directory a python driver is provided to run all experiments. 
You can run all the experiments using the following command

``
python3.7 driver.py
``

You can specify the driver to setup the environment and manually run the tool later by using following command, which will 
setup the experiment data in /data directory. 

``
python3.7 driver.py --only-setup
``

You can also select a single test-case you want to replicate by running the following command, where the bug ID is the id specified in our benchmark.

``
python3.7 driver.py --bug-id=BUG_ID
``

Alternatively, you can run the experiment manually (after setting up)

``
pypy3 FixMorph.py --conf=/path/to/configuration
``

## Running CVE-2016-5314
Lets run one of the experiments (CVE-2016-5314) in our data-set using the following command. The experiment timeout is set to 1hr. 
[Note: to stop a run, please use CTRL+z and kill the background process with “ps -aux | grep python | awk ‘{print $2}’ | xargs kill -9”.]

``
pypy3 FixMorph.py --conf=/FixMorph/tests/bug-types/div-zero/div-zero-1/repair.conf
``

## Intermediate Results
You can check the /output folder for intermediate results.
For example after the initial generation of the patches: cat /output/CVE-2016-5314/patch-set-gen
The expected output looks as follows:

	Patch #1
	L65: (x <= x)
			Partition: 1
			Patch Count: 1
			Path Coverage: 0
			Is Under-approximating: False
			Is Over-approximating: False
	Patch #2
	L65: (x <= y)
			Partition: 1
			Patch Count: 1
			Path Coverage: 0
			Is Under-approximating: False
			Is Over-approximating: False
	Patch #3
	L65: (x <= constant_a)
			Partition: 1
				Constant: const_a
				Range: -10 <= const_a <= 10
				Dimension: 21
			Patch Count: 21
			Path Coverage: 0
			Is Under-approximating: False
			Is Over-approximating: False
...

In total there are 28 (abstract) patches generated for this subject, representing 388 concrete patches.
Note that the initial ranking has no meaning and might vary. FixMorph will finish automatically after the timeout of 1 hour.

## Final Results
The correct patch, in this case, should be a guarded exit, check the developer patch at the corresponding commit.
The link is https://github.com/vadz/libtiff/commit/391e77f

```
+ if (sp->stream.avail_out > sp->tbuf_size)
+ {
+ 	TIFFErrorExt(tif->tif_clientdata, module, “sp->stream.avail_out > sp->tbuf_size”);
+ 	return (0);
+ }
```
The correct expression would be: sp->stream.avail_out > sp->tbuf_size

In our paper Table 1, we show that FixMorph identifies a semantic-equivalent patch ranked at position *1*. Therefore, you can check the output file to compare with the patch at rank 1.

```
less /FixMorph/output/CVE-2016-5314/patch-set-ranked
``` 


The resulting FixMorph/output/CVE-2016-5314/patch-set-ranked will show the patch:
	Patch #1
	L65: (x < y)

In the setup script: /experiments/extractfix/libtiff/CVE-2016-5314/setup.sh, we apply some annotation to inject our patch.
In setup.sh:line 33:

```
sed -i ‘786i if(__trident_choice(“L65”, “bool”, (int[]){sp->tbuf_size,sp->stream.avail_out, nsamples}, (char*[]){“x”, “y”, “z”}, 3, (int*[]){}, (char*[]){}, 0)) return 0;\n’ libtiff/tif_pixarlog.c
```


"trident_choice" represents the function call to retrieve a patch
* x is mapped to sp->tbuf_size
* y is mapped to sp->stream.avail_out
* z is mapped to nsamples


If we put all this information together, it is clear, that FixMorph successfully identified the developer patch at rank 1.
Additionally, to the ranking our Table 1 and Table 3 also show information about the patch pool size and the path exploration. The information can be checked with the “Run time statistics” printed at the end of each experiment, or by checking the logs in /FixMorph/logs/<tag_id>.

| Metric in Paper   | Description   | Metric in Logs/Output   |
|----------|----------|------|
| P_init |  the number of plausible patches, mostly similar to the concrete patches after patch synthesis step (before concolic exploration) | “Patch Start Count” |
| P_final |    the number of concrete patches after concolic exploration  |   “Patch End Count” |
| phi_explored | number of explored paths |   “Paths Explored” |
| phi_skipped | number of infeasible paths that have been skipped during concolic exploration|  “Paths Skipped” |


(In some cases FixMorph has more concrete patches after the patch synthesis: FixMorph works with abstract patches, which are not refined during synthesis, but pruned based on the failing test case. Therefore, abstract patches that in general allow to pass the failing test case would be kept completely, which means that some concrete values for the parameters might actually violate the failing test case. This is a technical detail and performance decision: an additional refinement of the abstract patches would slow down the initial patch synthesis significantly. In the paper we report the number of plausible patches that might deviate form “Patch Start Count” for some subjects, otherwise the comparison with CEGIS (which shows the actual number of plausible patches) would not be fair, as FixMorph could lead to a higher patch reduction ratio.)


## General Notes
The same steps need to be performed for all other subjects. The experimental results can differ in terms of TIMEOUT for different computation power

# Additional Links
* [Getting Started](../../doc/GetStart.md)
* [Example Usage](../../doc/Examples.md)
* [Manual](../../doc/Manual.md)
