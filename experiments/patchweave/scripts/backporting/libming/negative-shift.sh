bug_id=negative-shift
project_name=libming
dir_name=$1/backport/$project_name/$bug_id


project_url=https://github.com/libming/libming.git
pa=$project_name-0.4.7
pb=$project_name-0.4.8
pc=$project_name-0.4.6

pa_commit=19e7127
pb_commit=2e5a98a0
pc_commit=ming-0_4_6


mkdir $dir_name
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

