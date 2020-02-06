project_name=curl
bug_id=info-leak
dir_name=$1/backport/$project_name/$bug_id
pa=curl-7.57.0
pb=curl-7.58.0
pc=curl-7.53.0
project_url=https://github.com/curl/curl.git
pa_commit=993dd56
pb_commit=af32cd3
pc_commit=curl-7_53_0


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
