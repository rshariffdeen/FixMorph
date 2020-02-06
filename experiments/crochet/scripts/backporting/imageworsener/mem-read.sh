project_name=imageworsener
bug_id=mem-read
dir_name=$1/backport/$project_name/$bug_id
pa=imageworsener-1.3.1
pb=imageworsener-1.3.2
pc=imageworsener-1.2.0
project_url=https://github.com/jsummers/imageworsener.git
pa_commit=e2f7490
pb_commit=a4f2477
pc_commit=1.2.0

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

