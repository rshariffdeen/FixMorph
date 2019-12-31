project_name=libtiff-jasper
bug_id=memory-write-error
dir_name=$1/$project_name/$bug_id
dir_name_docker=/data/$bug_id
pa=libtiff-3.7.5
pb=libtiff-3.8.0
pc=jasper-1.900.8
pa_url=https://github.com/vadz/libtiff.git
pc_url=https://github.com/mdadams/jasper.git
pa_commit=991404c
pb_commit=50373d7d
pc_commit=version-1.900.8


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


cd $dir_name/$pc;autoreconf -i;./configure
cd $dir_name/$pc; bear make
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD


