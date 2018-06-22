#!/usr/bin/env bash
export LLVM_COMPILER=clang
export LD_LIBRARY_PATH=/home/klee/klee_build/klee/lib
cd /project;

#grep -rlHRw . -e "-fuse-linker-plugin" | while read a;
#do
#    sed -i "s/-fuse-linker-plugin//g" $a
#done

mkdir crochet; cd crochet
cmake -DCMAKE_C_COMPILER=wllvm -DCMAKE_CXX_COMPILER=wllvm++ -DCMAKE_C_FLAGS="-O0 -g -I/home/klee/klee_src/include -L/home/klee/klee_build/klee/lib -lkleeRuntest" -DCMAKE_CXX_FLAGS="-O0 -g -I/home/klee/klee_src/include -L/home/klee/klee_build/klee/lib -lkleeRuntest" -DCMAKE_LINKER=llvm-ld ..

make -j`nproc` $1
returnValue=$?

if [ $returnValue -ne 0 ]; then
    make -j`nproc`
fi
