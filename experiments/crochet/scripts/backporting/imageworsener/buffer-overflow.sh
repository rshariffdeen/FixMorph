project_name=imageworsener
bug_id=buffer-overflow
dir_name=$1/backport/$project_name/$bug_id
pa=imageworsener-1.3.0
pb=imageworsener-1.3.1
pc=imageworsener-0.9.4
project_url=https://github.com/jsummers/imageworsener.git
pa_commit=8656405
pb_commit=ca3356eb
pc_commit=0.9.4

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

