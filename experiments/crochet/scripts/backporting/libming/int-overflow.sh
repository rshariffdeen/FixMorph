project_name=libming
bug_id=int-overflow
dir_name=$1/backport/$project_name/$bug_id
pa=libming-0.4.7
pb=libming-0.4.8
pc=libming-0.4.6
project_url=https://github.com/libming/libming.git
pa_commit=447821c
pb_commit=1a1d270
pc_commit=ming-0_4_6


if [ -d $dir_name ] 
then
    rm -rf $dir_name 
    mkdir -p $dir_name
else
    mkdir -p $dir_name
fi

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
