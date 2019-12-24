project_name=jasper-openjpeg
bug_id=div-zero-1
dir_name=$1/$project_name/$bug_id
pa=jasper-1.900.2
pb=jasper-1.900.3
pc=openjpeg-1.5.1
pa_url=https://github.com/mdadams/jasper.git
pc_url=https://github.com/uclouvain/openjpeg.git
pa_commit=3c55b39
pb_commit=d8c2604
pc_commit=version.1.5.1
opj_file=applications/codec/j2k_to_image.c
opj_input=J2K_CFMT


mkdir -p $dir_name
cd $dir_name
git clone $pa_url $pa
cp -rf $pa $pb
cd $pa
git checkout $pa_commit
sed -i "s/inline bool jas_safe_size_mul/inline static bool jas_safe_size_mul/g" src/libjasper/base/jas_malloc.c
git add src/libjasper/base/jas_malloc.c
git commit -m "fix compile error"

cd ../$pb
git checkout $pb_commit
sed -i "s/inline bool jas_safe_size_mul/inline static bool jas_safe_size_mul/g" src/libjasper/base/jas_malloc.c
git add src/libjasper/base/jas_malloc.c
git commit -m "fix compile error"
cd ..

git clone $pc_url $pc
cd $pc
git checkout $pc_commit
sed -i "s/get_file_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"

cd $dir_name/$pc;autoreconf -i;./configure
cd $dir_name/$pc; bear make
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD


