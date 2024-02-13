FROM ubuntu:22.04
MAINTAINER Ridwan Shariffdeen <ridwan@comp.nus.edu.sg>

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    autoconf \
    apt-transport-https \
    autoconf-archive \
    autogen \
    bear \
    bison \
    cmake \
    curl \
    flex \
    g++ \
    gcc \
    git \
    google-perftools \
    mercurial \
    minisat \
    nano \
    ninja-build \
    perl \
    pkg-config \
    software-properties-common \
    subversion \
    unzip \
    wget \
    zlib1g-dev


ENV LLVM_VERSION=17
ENV LLVM_TAG=17.0.3
ENV CLANG_VERSION=17
ENV PYTHON_VERSION=3.11



RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key| apt-key add -
RUN apt-add-repository "deb http://apt.llvm.org/jammy/ llvm-toolchain-jammy-${LLVM_VERSION} main"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y  --no-install-recommends --force-yes \
    clang-${CLANG_VERSION} \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    python3-setuptools \
    llvm-${LLVM_VERSION} \
    llvm-${LLVM_VERSION}-dev \
    llvm-${LLVM_VERSION}-tools

RUN mkdir -p /opt/llvm; git clone https://github.com/llvm/llvm-project.git /opt/llvm/source; cd /opt/llvm/source; git checkout llvmorg-${LLVM_TAG}
RUN git clone https://github.com/rshariffdeen/clang-tools.git /opt/llvm/source/clang-tools-extra/clang-tools; cd /opt/llvm/source/clang-tools-extra/clang-tools; git checkout llvm-${LLVM_VERSION}
RUN echo "add_subdirectory(clang-tools)" >> /opt/llvm/source/clang-tools-extra/CMakeLists.txt
RUN mkdir /opt/llvm/build; cd /opt/llvm/build; cmake -G Ninja /opt/llvm/source/llvm -DCMAKE_BUILD_TYPE=Release -DCMAKE_ENABLE_ASSERTIONS=OFF -DLLVM_ENABLE_WERROR=OFF \
 -DLLVM_TARGETS_TO_BUILD=X86 -DCMAKE_CXX_FLAGS="-std=c++11" -DCMAKE_C_COMPILER=clang-17 -DCMAKE_CXX_COMPILER=clang++-17 \
 -DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra"

RUN cd /opt/llvm/build; ninja crochet-diff crochet-patch


## Install PyPy JITC
RUN add-apt-repository -y ppa:pypy/ppa
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y  --no-install-recommends --force-yes \
    gfortran \
    pypy3 \
    pypy3-dev

RUN python${PYTHON_VERSION} -m pip install --upgrade pip

#RUN pypy3 -m easy_install cython
#RUN pypy3 -m easy_install setuptools
#RUN pypy3 -m easy_install six
#RUN pypy3 -m easy_install gitpython


RUN git clone https://gitlab.com/akihe/radamsa.git /opt/radamsa
RUN cd /opt/radamsa; git checkout 30770f6e; make; make install
ADD . /opt/fixmorph
WORKDIR /opt/fixmorph
RUN python${PYTHON_VERSION} -m pip --disable-pip-version-check --no-cache-dir install -r /opt/fixmorph/requirements.txt
RUN python${PYTHON_VERSION} setup.py build_ext --inplace
ENV PATH="${PATH}:/opt/fixmorph/bin"
# Tidy up the container
RUN DEBIAN_FRONTEND=noninteractive apt-get -y autoremove && apt-get clean && \
     rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

