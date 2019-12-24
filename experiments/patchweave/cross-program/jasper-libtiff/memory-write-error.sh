project_name=jasper-libtiff
bug_id=memory-write-error
dir_name=$1/$project_name/$bug_id
pa=jasper-1.900.8
pb=jasper-1.900.9
pc=libtiff-3.7.5
pc_url=https://github.com/vadz/libtiff.git
pa_url=https://github.com/mdadams/jasper.git
pa_commit=cfa945c
pb_commit=5d66894d
pc_commit=Release-v3-7-5


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


