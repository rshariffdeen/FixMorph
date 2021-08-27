FROM ubuntu:16.04
MAINTAINER Ridwan Shariffdeen <ridwan@comp.nus.edu.sg>

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    autoconf \
    apt-transport-https \
    autoconf-archive \
    autogen \
    bison \
    cmake \
    curl \
    flex \
    google-perftools \
    mercurial \
    minisat \
    nano \
    ninja \
    perl \
    pkg-config \
    software-properties-common \
    subversion \
    unzip \
    wget \
    zlib1g-dev

RUN add-apt-repository -y ppa:git-core/ppa
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git

RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key| apt-key add -
RUN apt-add-repository "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-9 main"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y  --no-install-recommends --force-yes \
    clang-9 \
    python3.7 \
    python3-pip \
    python3-setuptools

RUN mkdir -p /llvm/llvm-10; git clone https://github.com/llvm/llvm-project.git /llvm/llvm-10/source; cd /llvm/llvm-10/source; git checkout llvmorg-10.0.0
RUN git clone https://github.com/rshariffdeen/clang-tools.git /llvm/llvm-10/source/clang-tools-extra/clang-tools; cd /llvm/llvm-10/source/clang-tools-extra/clang-tools; git checkout llvm-10
RUN echo "add_subdirectory(clang-tools)" >> /llvm/llvm-10/source/clang-tools-extra/CMakeLists.txt
RUN mkdir /llvm/llvm-10/build; cd /llvm/llvm-10/build; cmake /llvm/llvm-10/source/llvm -DCMAKE_BUILD_TYPE=Release -DCMAKE_ENABLE_ASSERTIONS=OFF -DLLVM_ENABLE_WERROR=OFF \
 -DLLVM_TARGETS_TO_BUILD=X86 -DCMAKE_CXX_FLAGS="-std=c++11" -DCMAKE_C_COMPILER=clang-9 -DCMAKE_CXX_COMPILER=clang++-9 \
 -DLLVM_ENABLE_PROJECTS="clang;libcxx;clang-tools-extra;libcxxabi"

RUN cd /llvm/llvm-10/build; make -j32; make install


RUN mkdir /bear; git clone https://github.com/rizsotto/Bear.git /bear/source;
RUN cd /bear/source; git checkout 2.2.1
RUN mkdir /bear/build; cd /bear/build; cmake ../source; make -j32; make install

## Install PyPy JITC
RUN add-apt-repository -y ppa:pypy/ppa
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y  --no-install-recommends --force-yes \
    gfortran \
    python3.7-dev

RUN python3.7 -m pip install --upgrade pip
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install pylint
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install six
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install gitpython
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install cython
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install pymongo

RUN git clone https://gitlab.com/akihe/radamsa.git /radamsa
RUN cd /radamsa; git checkout 30770f6e; make; make install
RUN git clone https://github.com/rshariffdeen/FixMorph.git /FixMorph
RUN rm /FixMorph/Dockerfile
WORKDIR /FixMorph
RUN python3.7 setup.py build_ext --inplace
# Tidy up the container
RUN DEBIAN_FRONTEND=noninteractive apt-get -y autoremove && apt-get clean && \
     rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN ln -s /FixMorph/bin/fixmorph /usr/bin/fixmorph
