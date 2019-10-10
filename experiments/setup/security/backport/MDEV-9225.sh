project_name=mariadb
bug_id=MDEV-9225
dir_name=$1/$project_name/$bug_id
pa=$project_name-5.5.48
pb=$project_name-5.5.49
pc=oracle_mysql-5.5
project_url=https://github.com/MariaDB/server.git
alternate_url=https://github.com/mysql/mysql-server.git
pa_commit=b7dc830 #Use commit hash here to checkout a particular commit from the branches
pb_commit=2a47817
pc_commit=5.5 #Use branch names here

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
git clone $alternate_url $pc


cd $pa
git checkout $pa_commit

cd ../$pb
git checkout $pb_commit

cd ../$pc
git checkout $pc_commit

cd $dir_name
touch $bug_id.conf
{
  echo 'path_a:'$dir_name/$pa
  echo 'path_b:'$dir_name/$pb
  echo 'path_c:'$dir_name/$pc
} >$bug_id.conf

cd /crochet
python3 Crochet.py --conf=$dir_name/$bug_id.conf | sed 's/\x1b\[[0-9;]*m//g' | tee /crochet/results/$bug_id.txt
