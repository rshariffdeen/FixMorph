project_name=openjpeg-jasper
bug_id=div-zero-2
dir_name=$1/$project_name/$bug_id
pa=openjpeg-1.3
pb=openjpeg-1.4
pc=jasper-1.900.2
pa_url=https://github.com/uclouvain/openjpeg.git
pc_url=https://github.com/mdadams/jasper.git
pa_commit=65e5ff0
pb_commit=71bbf41
pc_commit=version-1.900.2
opj_file=codec/j2k_to_image.c
opj_input=J2K_CFMT


mkdir -p $dir_name
cd $dir_name
git clone $pa_url $pa
cp -rf $pa $pb
cd $pa
git checkout $pa_commit
sed -i "s/get_file_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"
sed -i "s/CFLAGS = -O3 -lstdc++ # -g -p -pg/CFLAGS = -O3 -lstdc++ # -g -p -pg\nCC = clang/g" codec/Makefile
sed -i "s/gcc/\$(CC)/g" codec/Makefile
git add codec/Makefile
git commit -m "fix make error"

cd ../$pb
git checkout $pb_commit
sed -i "s/get_file_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"
sed -i "s/CFLAGS = -O3 -lstdc++ # -g -p -pg/CFLAGS = -O3 -lstdc++ # -g -p -pg\nCC = clang/g" codec/Makefile
sed -i "s/gcc/\$(CC)/g" codec/Makefile
git add codec/Makefile
git commit -m "fix make error"
sed -i "s/%s: invalid image size/invalid image size/g" libopenjpeg/j2k.c
git add libopenjpeg/j2k.c
git commit -m "fix bug"
cd ..

git clone $pc_url $pc
cd $pc
git checkout $pc_commit
rm aclocal.m4
git add aclocal.m4
git commit -m "removing aclocal"

cd $dir_name/$pc;autoreconf -i;./configure
cd $dir_name/$pc; bear make
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD


