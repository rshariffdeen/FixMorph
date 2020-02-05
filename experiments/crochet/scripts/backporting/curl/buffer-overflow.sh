project_name=curl
bug_id=buffer-overflow
dir_name=$1/$project_name/$bug_id
pa=curl-7.60.0
pb=curl-7.61.0
pc=curl-7.55.1
project_url=https://github.com/curl/curl.git
pa_commit=0b4ccc9
pb_commit=ba1dbd7
pc_commit=curl-7_55_1

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

