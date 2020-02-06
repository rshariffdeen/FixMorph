project_name=wavpack
bug_id=buffer-overflow
dir_name=$1/backport/$project_name/$bug_id
pa=wavpack-5.1.0
pb=wavpack-master
pc=wavpack-5.0.0
project_url=https://github.com/dbry/WavPack.git
pa_commit=36a24c7
pb_commit=8e3fe45
pc_commit=5.0.0

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
