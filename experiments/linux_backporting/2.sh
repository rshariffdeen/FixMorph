project_name=linux
bug_id=2
dir_name=$1/$project_name/$bug_id
pa=$project_name-4_6
pb=$project_name-4_7
pc=v3_2
pd=v3_16
pe=v4_4
project_url=https://github.com/torvalds/linux.git
pa_commit=4879efb #Use commit hash here to checkout a particular commit from the branches
pb_commit=0015f91
pc_commit=805a6af
pd_commit=19583ca
pe_commit=afd2ff9

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
  echo 'path_a:'$dir_name/$pa/drivers/usb/gadget/function
  echo 'path_b:'$dir_name/$pb/drivers/usb/gadget/function
  echo 'path_c:'$dir_name/$pc/drivers/usb/gadget/function
  echo 'config_command_a:skip'
  echo 'config_command_c:skip'
  echo 'build_command_a:make -j10'
  echo 'build_command_c:make -j10'
} >$bug_id-$pc.conf

touch $bug_id-$pe.conf
{
  echo 'path_a:'$dir_name/$pa/drivers/usb/gadget/function
  echo 'path_b:'$dir_name/$pb/drivers/usb/gadget/function
  echo 'path_c:'$dir_name/$pe/drivers/usb/gadget/function
  echo 'config_command_a:skip'
  echo 'config_command_c:skip'
  echo 'build_command_a:make -j10'
  echo 'build_command_c:make -j10'
} >$bug_id-$pe.conf

cd /crochet
