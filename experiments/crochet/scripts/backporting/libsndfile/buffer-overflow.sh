bug_id=buffer-overflow
project_name=libsndfile
dir_name=$1/backport/$project_name/$bug_id

project_url=https://github.com/erikd/libsndfile.git
pa=$project_name-1.0.28
pb=$project_name-1.0.29
pc=$project_name-1.0.26

pa_commit=5206a9b
pb_commit=fd0484ab
pc_commit=1.0.26


mkdir -p $dir_name
cd $dir_name
git clone $project_url $pa
cp -rf $pa $pb
cp -rf $pa $pc
cd $pa
git checkout $pa_commit

cd ../$pb
git checkout $pb_commit

cd ../$pc
git checkout $pc_commit

cd $dir_name/$pc;autoreconf -i;./configure
cd $dir_name/$pc; bear make
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD

