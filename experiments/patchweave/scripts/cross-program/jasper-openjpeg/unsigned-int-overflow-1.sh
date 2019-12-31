project_name=jasper-openjpeg
bug_id=unsigned-int-overflow-1
dir_name=$1/$project_name/$bug_id
dir_name_docker=/data/$bug_id
pa=jasper-1.900.13
pb=jasper-1.900.14
pc=openjpeg-2.1.0
pa_url=https://github.com/mdadams/jasper.git
pc_url=https://github.com/uclouvain/openjpeg.git
pa_commit=e546362
pb_commit=ba2b9d00
pc_commit=version.2.1
opj_file=src/bin/jp2/opj_dump.c
opj_input=JP2_CFMT


mkdir -p $dir_name
cd $dir_name
git clone $pa_url $pa
cp -rf $pa $pb
cd $pa
git checkout $pa_commit


cd ../$pb
git checkout $pb_commit
cd ..

git clone $pc_url $pc
cd $pc
git checkout $pc_commit
sed -i "s/get_file_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"

cd $dir_name/$pc;cmake .
cd $dir_name/$pc; bear make
rm -rf $dir_name/$pc/CMakeFiles
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD


