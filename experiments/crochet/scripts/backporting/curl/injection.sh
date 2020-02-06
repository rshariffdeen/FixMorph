project_name=curl
bug_id=injection
dir_name=$1/backport/$project_name/$bug_id
pa=curl-7.50.0
pb=curl-7.51.0
pc=curl-7.48.0
project_url=https://github.com/curl/curl.git
pa_commit=811a693
pb_commit=cff89bc
pc_commit=curl-7_48_0

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
