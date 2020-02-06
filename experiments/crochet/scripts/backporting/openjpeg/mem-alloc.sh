project_name=openjpeg
bug_id=mem-alloc
dir_name=$1/backport/$project_name/$bug_id
pa=openjpeg-2.2.0
pb=openjpeg-2.3.0
pc=openjpeg-2.1.2
project_url=https://github.com/uclouvain/openjpeg.git
pa_commit=afb308b
pb_commit=baf0c1ad
pc_commit=v2.1.2


mkdir -p $dir_name
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

