project_name=libtiff
bug_id=buffer-overflow
dir_name=$1/backport/$project_name/$bug_id
pa=libtiff-4.0.6
pb=libtiff-4.0.7
pc=libtiff-3.9.7
project_url=https://github.com/vadz/libtiff.git
pa_commit=c421b99
pb_commit=391e77f
pc_commit=Release-v3-9-7

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

