project_name=linux
bug_id=1
dir_name=$1/$project_name/$bug_id
pa=$project_name-3_11
pb=$project_name-3_12
pc=v3_2
pd=v3_4
pe=v3_10
project_url=https://github.com/torvalds/linux.git
pa_commit=2db811c #Use commit hash here to checkout a particular commit from the branches
pb_commit=f5360a4
pc_commit=805a6af
pd_commit=76e10d1
pe_commit=8bb495e

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

cd $dir_name
touch $bug_id-$pc.conf
{
  echo 'path_a:'$dir_name/$pa/block
  echo 'path_b:'$dir_name/$pb/block
  echo 'path_c:'$dir_name/$pc/block
  echo 'config_command_a:skip'
  echo 'config_command_c:skip'
  echo 'build_command_a:make -j10'
  echo 'build_command_c:make -j10'
} >$bug_id-$pc.conf

touch $bug_id-$pd.conf
{
  echo 'path_a:'$dir_name/$pa/block
  echo 'path_b:'$dir_name/$pb/block
  echo 'path_c:'$dir_name/$pd/block
  echo 'config_command_a:skip'
  echo 'config_command_c:skip'
  echo 'build_command_a:make -j10'
  echo 'build_command_c:make -j10'
} >$bug_id-$pd.conf

touch $bug_id-$pe.conf
{
  echo 'path_a:'$dir_name/$pa/block
  echo 'path_b:'$dir_name/$pb/block
  echo 'path_c:'$dir_name/$pe/block
  echo 'config_command_a:skip'
  echo 'config_command_c:skip'
  echo 'build_command_a:make -j10'
  echo 'build_command_c:make -j10'
} >$bug_id-$pe.conf

cd /crochet
