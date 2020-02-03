project_name=linux
bug_id=3
dir_name=$1/$project_name/$bug_id
pa=$project_name-5_0
pb=$project_name-5_1
pc=v3_16
pd=v4_9
pe=v4_14
pf=v4_19
project_url=https://github.com/torvalds/linux.git
pa_commit=9e98c67 #Use commit hash here to checkout a particular commit from the branches
pb_commit=00206a6
pc_commit=19583ca
pd_commit=69973b8
pe_commit=bebc608
pf_commit=84df952

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
cp -rf $pa $pd
cp -rf $pa $pe
cp -rf $pa $pf

cd $pa
git checkout $pa_commit

cd ../$pb
git checkout $pb_commit

cd ../$pc
git checkout $pc_commit

cd ../$pd
git checkout $pd_commit

cd ../$pe
git checkout $pe_commit

cd ../$pf
git checkout $pf_commit

cd $dir_name
touch $bug_id.conf
{
  echo 'path_a:'$dir_name/$pa/src
  echo 'path_b:'$dir_name/$pb/src
  echo 'path_c:'$dir_name/$pc/src
  echo 'path_d:'$dir_name/$pc/src
  echo 'path_e:'$dir_name/$pc/src
  echo 'path_f:'$dir_name/$pc/src
  echo 'config_command_a:skip'
  echo 'config_command_c:skip'
  echo 'config_command_d:skip'
  echo 'config_command_e:skip'
  echo 'config_command_f:skip'
  echo 'build_command_a:make -j10'
  echo 'build_command_c:make -j10'
  echo 'build_command_d:make -j10'
  echo 'build_command_e:make -j10'
  echo 'build_command_f:make -j10'
} >$bug_id.conf

cd /crochet
