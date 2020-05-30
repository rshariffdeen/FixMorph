FROM ubuntu:16.04
MAINTAINER Ridwan Shariffdeen <ridwan@comp.nus.edu.sg>

RUN apt-get update && apt-get install -y \
    autoconf \
    apt-transport-https \
    autoconf-archive \
    autogen \
    bison \
    cmake \
    curl \
    flex \
    git \
    google-perftools \
    mercurial \
    minisat \
    nano \
    ninja \
    perl \
    pkg-config \
    python3 \
    python3-pip \
    software-properties-common \
    subversion \
    unzip \
    wget \
    zlib1g-dev


RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key| apt-key add -
RUN apt-add-repository "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-10 main"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y  --no-install-recommends --force-yes \
    clang-10
RUN mkdir -p /llvm/llvm-10; git clone https://github.com/llvm/llvm-project.git /llvm/llvm-10/source; cd /llvm/llvm-10/source; git checkout llvmorg-10.0.0
#RUN svn co https://llvm.org/svn/llvm-project/cfe/tags/RELEASE_700/final/ /llvm/llvm-7/source/tools/clang
RUN git clone https://github.com/rshariffdeen/clang-tools.git /llvm/llvm-10/source/clang-tools-extra/clang-tools; cd /llvm/llvm-10/source/clang-tools-extra/clang-tools; git checkout llvm-10
#RUN git clone https://github.com/llvm-mirror/clang-tools-extra.git /llvm/llvm-7/source/tools/clang/tools/clang-extra
#RUN cd /llvm/llvm-7/source/tools/clang/tools/clang-extra; git checkout release_70;
RUN echo "add_subdirectory(clang-tools)" >> /llvm/llvm-10/source/clang-tools-extra/CMakeLists.txt
#RUN echo "add_clang_subdirectory(clang-extra)" >> /llvm/llvm-7/source/tools/clang/tools/CMakeLists.txt
#RUN svn co http://llvm.org/svn/llvm-project/compiler-rt/tags/RELEASE_700/final /llvm/llvm-7/source/projects/compiler-rt
RUN mkdir /llvm/llvm-10/build; cd /llvm/llvm-10/build; cmake /llvm/llvm-10/source/llvm -DCMAKE_BUILD_TYPE=Release -DCMAKE_ENABLE_ASSERTIONS=OFF -DLLVM_ENABLE_WERROR=OFF \
 -DLLVM_TARGETS_TO_BUILD=X86 -DCMAKE_CXX_FLAGS="-std=c++11" -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
 -DLLVM_ENABLE_PROJECTS="clang;libcxx;clang-tools-extra;libcxxabi"

RUN cd /llvm/llvm-10/build; make -j32; make install


RUN mkdir /bear; git clone https://github.com/rizsotto/Bear.git /bear/source;
RUN cd /bear/source; git checkout 2.2.1
RUN mkdir /bear/build; cd /bear/build; cmake ../source; make -j32; make install

RUN /usr/bin/pip3 install --upgrade pip && pip3 install \
    pysmt \
    six \
    wllvm

RUN echo "Y" | pysmt-install  --z

RUN pip install gitpython

RUN git clone https://gitlab.com/akihe/radamsa.git /radamsa
RUN cd /radamsa; git checkout 30770f6e; make; make install
ADD $PWD /crochet


# Tidy up the container
RUN DEBIAN_FRONTEND=noninteractive apt-get -y autoremove && apt-get clean && \
     rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
