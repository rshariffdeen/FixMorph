#!/usr/bin/env bash

export LLVM_COMPILER=clang
export LD_LIBRARY_PATH=/home/klee/klee_build/klee/lib
cd /project; mkdir crochet; cd crochet
cmake -DCMAKE_C_COMPILER=wllvm -DCMAKE_CXX_COMPILER=wllvm++ -DCMAKE_C_FLAGS="-O0 -g -I/home/klee/klee_src/include -L/home/klee/klee_build/klee/lib -lkleeRuntest" -DCMAKE_CXX_FLAGS="-O0 -g -I/home/klee/klee_src/include -L/home/klee/klee_build/klee/lib -lkleeRuntest" -DCMAKE_LINKER=llvm-ld ..
make -j`nproc`
