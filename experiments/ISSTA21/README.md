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
We will first run a test example to verify that FixMorph is working in the given environment, for this purpose we will use
the test-case provided in the directory 'tests/update/assignment'. In this example we provide three C source files and their
corresponding Makefiles, in addition we also provide the configuration file for FixMorph. 


* /FixMorph/tests/update/assignment/repair.conf shows the FixMorph configuration file.
* /FixMorph/tests/update/assignment/PA lists the source files for pre-transform version of the reference program
* /FixMorph/tests/update/assignment/PB lists the source files for post-transform version of the reference program
* /FixMorph/tests/update/assignment/PC lists the source files for target program

## Test Run
You can check if everything is working well, by running the above test-case from our test-suite. 

``
python3.7 FixMorph.py --conf=tests/update/assignment/repair.conf
``

The example test-case provided illustrates a change in the sorting logic in the donor/reference program by updating the field
use for the sorting logic, from 'rank' to the entity 'id'. We use FixMorph to learn the transformation and apply it to another 
similar but different program. 

### FixMorph Output
The output message at the end of the execution should look similar to the following:

	Initialization: 0.000 minutes
	Build Analysis: 0.000 minutes
	Diff Analysis: 0.001 minutes
	Clone Analysis: 0.005 minutes
	Slicing: 0.000 minutes
	AST Analysis: 0.001 minutes
	Map Generation: 0.011 minutes
	Translation: 0.002 minutes
	Evolution: 0.004 minutes
	Transplantation: 0.004 minutes
	Verification: 0.002 minutes
	Comparison: 0.000 minutes
	Summarizing: 0.002 minutes
    
    FixMorph finished successfully after 0.032 minutes


### Analysing Results
FixMorph was able to successfully generate an updated version of the target program from the transformation learnt from the
reference program. During this process FixMorph produces several files and we will analyse each below:

* /FixMorph/logs/TAG_ID directory stores all logs, the "TAG_ID" should be specified in the configuration file
	* log-latest: this is the main application log which captures each step of the program transformation
	* log-error: this log captures any errors (if observed), which can be use for debugging purpose
	* log-make: this log captures the output of the build process of each program
* /FixMorph/output/TAG_ID directory stores all artefacts generated for the transformation, the "TAG_ID" should be specified in the configuration file
	* orig-diff: this file captures the transformation in the reference program
	* transplant-diff: this file captures the transformation applied to the target program
	* port-diff: this file captures the transformation done in manual (comparison phase will run only if an additional version of target program "Pe" is provided in configuration)
	* vector-map: this file shows the mapping for the function/source files
	* namespace-map-global: this file shows the generated global mapping for each function/slice mapped


To better explore the final outcome, please check the FixMorph output directory which is in
/FixMorph/output/<tag_id> (for this example the tag_id defined in the configuration file is 'update-test') i.e. /FixMorph/output/update-test
Similarly, the logs are also stored in /FixMorph/logs/<tag_id>.

For more examples refer [this guide](../doc/Examples.md)


# Running Experiments
Following details how to run the scripts and the tool to replicate the results of our experiments.
Once you build the docker image, you spin up a container as mentioned above. 

Inside the container the following directories will be used
- /FixMorph - this will be the tool directory
- /experiments/ISSTA21 - all experiment setups will be deployed in this directory


In /experiments/ISSTA21 directory a python driver is provided to run all experiments. 
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
python3.7 FixMorph.py --conf=/path/to/configuration
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
