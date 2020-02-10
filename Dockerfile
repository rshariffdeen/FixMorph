FROM ubuntu:16.04
MAINTAINER Ridwan Shariffdeen <ridwan@comp.nus.edu.sg>

RUN apt-get update && apt-get install -y \
    autoconf \
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
RUN apt-add-repository "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-7 main"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y  --no-install-recommends --force-yes \
    clang-7
RUN mkdir -p /llvm/llvm-7; git clone http://llvm.org/git/llvm.git /llvm/llvm-7/source; cd /llvm/llvm-7/source; git checkout release_70
RUN svn co https://llvm.org/svn/llvm-project/cfe/tags/RELEASE_700/final/ /llvm/llvm-7/source/tools/clang
RUN git clone https://github.com/rshariffdeen/clang-tools.git /llvm/llvm-7/source/tools/clang/tools/clang-tools
RUN git clone https://github.com/llvm-mirror/clang-tools-extra.git /llvm/llvm-7/source/tools/clang/tools/clang-extra
RUN cd /llvm/llvm-7/source/tools/clang/tools/clang-extra; git checkout release_70;
RUN echo "add_clang_subdirectory(clang-tools)" >> /llvm/llvm-7/source/tools/clang/tools/CMakeLists.txt
RUN echo "add_clang_subdirectory(clang-extra)" >> /llvm/llvm-7/source/tools/clang/tools/CMakeLists.txt
RUN svn co http://llvm.org/svn/llvm-project/compiler-rt/tags/RELEASE_700/final /llvm/llvm-7/source/projects/compiler-rt
RUN mkdir /llvm/llvm-7/build; cd /llvm/llvm-7/build; cmake /llvm/llvm-7/source -DCMAKE_BUILD_TYPE=Release -DCMAKE_ENABLE_ASSERTIONS=OFF -DLLVM_ENABLE_WERROR=OFF -DLLVM_TARGETS_TO_BUILD=X86 -DCMAKE_CXX_FLAGS="-std=c++11" -DCMAKE_C_COMPILER=clang-7 -DCMAKE_CXX_COMPILER=clang++-7
RUN cd /llvm/llvm-7/build; make -j32; make install


RUN mkdir /bear; git clone https://github.com/rizsotto/Bear.git /bear/source;
RUN cd /bear/source; git checkout 2.2.1
RUN mkdir /bear/build; cd /bear/build; cmake ../source; make -j32; make install

RUN /usr/bin/pip3 install --upgrade pip && pip3 install \
    pysmt \
    six \
    wllvm

RUN echo "Y" | pysmt-install  --z

# Libraries for Experiments
RUN apt-get install -y \
    gtk+-3.0 \
    libavahi-client-dev \
    libasound2-dev \
    libgconf2-dev \
    libconfig-dev \
    libcrypto++-dev \
    libdaemon-dev \
    libfreetype6-dev \
    libidn2-0-dev \
    libnl-3-dev \
    libnl-genl-3-dev \
    libpopt-dev \
    libpulse-dev \
    libsoxr-dev \
    libssl-dev \
    libtiff5-dev \
    mesa-common-dev \
    libboost-all-dev \
    libgoogle-perftools-dev \
    libncurses5-dev \
    tzdata



RUN git clone https://gitlab.com/akihe/radamsa.git /radamsa
RUN cd /radamsa; git checkout 30770f6e; make; make install

RUN git config --global user.email "rshariffdeen@gmail.com"
RUN git config --global user.name "Ridwan"
ADD $PWD /crochet


# Tidy up the container
RUN DEBIAN_FRONTEND=noninteractive apt-get -y autoremove && apt-get clean && \
     rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
