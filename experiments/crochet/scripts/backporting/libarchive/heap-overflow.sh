project_name=libarchive
bug_id=heap-overflow
dir_name=$1/$project_name/$bug_id
pa=libarchive-3.2.1
pb=libarchive-3.2.2
pc=libarchive-3.1.2
project_url=https://github.com/libarchive/libarchive.git
pa_commit=a6dd4cc
pb_commit=7f17c79
pc_commit=v3.1.2


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
