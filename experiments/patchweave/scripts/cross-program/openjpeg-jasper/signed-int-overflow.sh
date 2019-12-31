project_name=openjpeg-jasper
bug_id=signed-int-overflow
dir_name=$1/$project_name/$bug_id

pa=openjpeg-1.5.1
pb=openjpeg-1.5.2
pc=jasper-1.900.12
pa_url=https://github.com/uclouvain/openjpeg.git
pc_url=https://github.com/mdadams/jasper.git
pa_commit=910af7ed
pb_commit=6e0162a
pc_commit=version-1.900.12
opj_file=applications/codec/j2k_to_image.c
opj_input=JP2_CFMT


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


cd $dir_name/$pc;autoreconf -i;./configure
cd $dir_name/$pc; bear make
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD


