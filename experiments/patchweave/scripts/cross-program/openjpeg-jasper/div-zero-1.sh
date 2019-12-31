project_name=openjpeg-jasper
bug_id=div-zero-1
dir_name=$1/$project_name/$bug_id
pa=openjpeg-1.5.1
pb=openjpeg-1.5.2
pc=jasper-1.900.2
pa_url=https://github.com/uclouvain/openjpeg.git
pc_url=https://github.com/mdadams/jasper.git
pa_commit=c02f145
pb_commit=e55d5e2
pc_commit=version-1.900.2
opj_file=applications/codec/j2k_to_image.c
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

cd ../$pb
git checkout $pb_commit
sed -i "s/get_file_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"
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


