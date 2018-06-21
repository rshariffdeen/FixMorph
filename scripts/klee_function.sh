#!/usr/bin/env bash

cd $1
extract-bc $2
klee -write-smt2s -write-paths --only-output-states-covering-new -entry-point=$3  -max-time=300 $2.bc

