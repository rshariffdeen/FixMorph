project_name=jasper
bug_id=CVE-2016-9560
dir_name=$1/$project_name/$bug_id
pa=jasper-1.900.25
pb=jasper-1.900.26
pc=jasper-1.900.1
project_url=https://github.com/mdadams/jasper.git
pa_commit=71bbf41
pb_commit=1abc2e5a
pc_commit=version-1.900.1


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
