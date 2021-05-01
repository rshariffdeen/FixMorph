# Experiment Replication

FixMorph successfully generates correct transformation for 75.1% of the subjects in our data-set which are curated from backported patches in the Linux Kernel project. 

In our replication package, we include scripts to reproduce the experiment using fixmorph.
This directory includes scripts and Dockerfile to re-create the experiment setup and reproduce the evaluation results.

Dockerhub Repo: https://hub.docker.com/repository/docker/rshariffdeen/fixmorph


# Getting Started

## Building the environment
Setup environment can be built using the Dockerfile provided within, which will encompass the dependencies, configurations
and setup scripts. Use the following command:

```bash
git clone https://github.com/rshariffdeen/FixMorph.git
cd /FixMorph
docker build -t rshariffdeen/fixmorph .
cd /FixMorph/experiments/ISSTA21
docker build -t rshariffdeen/fixmorph:issta21 .
```

Note that the build process can be time-consuming, hence you can using the following command to download pre-built Docker image from following repository Dockerhub Repo: https://hub.docker.com/repository/docker/rshariffdeen/fixmorph
```bash
docker pull rshariffdeen/fixmorph:issta21
```

Having the image, you can now start a Docker container. 

[comment]: <> (We recommend linking the container to folders in the filesystem,)
[comment]: <> (so that it is possible to check the logs and generated outputs also outside of the Docker container. )

```bash
docker run --name FixMorph -it rshariffdeen/fixmorph:issta21 bash
```

## Test Input Files
We will first run a test example to verify that FixMorph is working in the given environment, for this purpose we will use the test-case provided in the directory 'tests/update/assignment'. In this example we provide three C source files and their corresponding Makefiles, in addition we also provide the configuration file for FixMorph.


* /FixMorph/tests/update/assignment/repair.conf is the FixMorph configuration file.
* /FixMorph/tests/update/assignment/PA lists the source files for pre-transform version of the reference version
* /FixMorph/tests/update/assignment/PB lists the source files for post-transform version of the reference version
* /FixMorph/tests/update/assignment/PC lists the source files for target version

## Test Run
You can check if everything is working well by running the above test-case from our test-suite. 

```bash
python3.7 FixMorph.py --conf=tests/update/assignment/repair.conf
```

This example test-case illustrates a change in a sorting logic. The patch updates the field use of the sorting logic from 'rank' to entity 'id'. We use FixMorph to learn the transformation rule and apply it to another similar but different version.

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

For more examples refer [this guide](../../doc/Examples.md).


# Running Experiments
Following details how to run the scripts and the tool to replicate the results of our experiments.
Once you build the docker image, you spin up a container as mentioned above.

Inside the container the following directories/files will be used
- /FixMorph - this is the tool directory
- /experiments/ISSTA21 - all experiment setups will be deployed in this directory
- /experiments/ISSTA21/main-data.json - this contains the meta-data for the main experiment of (350 commits)
- /experiments/ISSTA21/cve-data.json - this contains the meta-data for the cve-fixes


In /experiments/ISSTA21 directory a python driver is provided to run all experiments. 
You can run all the experiments using the following command

```bash
python3.7 driver.py --data=[cve-data.json/main-data.json]
```

You can specify the driver to setup the environment and manually run the tool later by using following command, which will setup the experiment data in /data directory.

```bash
python3.7 driver.py --data=[cve-data.json/main-data.json] --only-setup
```

You can also select a single test-case you want to replicate by running the following command, where the bug ID is the id specified in our benchmark.

```bash
python3.7 driver.py --data=[cve-data.json/main-data.json] --bug-id=BUG_ID
```

Alternatively, you can run the experiment manually (after setting up)

```bash
python3.7 FixMorph.py --conf=/path/to/configuration
python3.7 FixMorph.py --conf=/data/backport/linux/1/repair.conf
python3.7 FixMorph.py --conf=/data/backport/linux-cve/1/repair.conf
```

## Running experiment #238 (Patch Type-3)
Lets run one of the experiments (Bug-ID 238) in our data-set using the following command. The general experiment timeout is set to 1hr. 
[Note: to stop a run, please use CTRL+C]

### Step 1 - Setting up the experiment
First, we need to prepare the experiment by setting up the source directories. We use the following command:
```bash

cd /FixMorph/experiments/ISSTA21
python3.7 driver.py --data=main-data.json --only-setup --bug-id=238

```

Once the setup is completed, you can verify the setup is located at /data/backport/linux/BUG_ID

## Step 2 - Running FixMorph
Next step is to invoke FixMorph with the experiment configuration, using the following command:
```bash

cd /FixMorph
python3.7 FixMorph.py --conf=/data/backport/linux/238/repair.conf

```
The transformation should be completed in ~10 minutes. 

## Step 3 - Analysing Results
You can observe the transformation from the following artefacts, which shows that FixMorph generated a semantically equivalent
transformation compared to the patch that developer manually ported. 

### Original Patch
```c
430a431
> 		if ((status != -ENOENT) || (urb->actual_length == 0))
```

### Ported Patch (Manual Dev)
```c
429a430
> 		if ((urb->status != -ENOENT) || (urb->actual_length == 0))
```

### Transplanted Patch (FixMorph Generated)
```c
413a414,415
>  int status = urb->status; 

430c432,434
< 		return;
---
> if ((status != -ENOENT) || (urb->actual_length == 0))
> 			return;
```

## General Notes
The same steps need to be performed for all other subjects. The experimental results can differ in terms of timeout for different computation power
TIMEOUT is set to 1hr by default, which can be modified passing the argument "--time=TIME" as shown in below command. In addition, you can specify
which mode of transformation to use from
* 0: FixMorph
* 1: Linux Patch No-Context 
* 2: Linux Patch using Context
* 3: SYDIT

```bash

cd /FixMorph
python3.7 FixMorph.py --conf=/data/backport/linux/238/repair.conf --time=TIME --mode=MODE_NUMBER

```

## Additional Files ##
Please find below files useful for the replication of the experiments

* [Results Sheet](experiments/ISSTA21/Results.xlsx)  
* [Main Data Set](experiments/ISSTA21/main-data.json)
* [CVE Data Set](experiments/ISSTA21/cve-data.json)


# Additional Links
* [Getting Started](../../doc/GetStart.md)
* [Example Usage](../../doc/Examples.md)
* [Manual](../../doc/Manual.md)
