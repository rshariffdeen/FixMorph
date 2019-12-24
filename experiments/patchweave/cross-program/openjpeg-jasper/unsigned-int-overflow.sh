project_name=openjpeg-jasper
bug_id=unsigned-int-overflow
dir_name=$1/$project_name/$bug_id
pa=openjpeg-2.1
pb=openjpeg-2.1.1
pc=jasper-1.900.13
pa_url=https://github.com/uclouvain/openjpeg.git
pc_url=https://github.com/mdadams/jasper.git
pa_commit=c0cb119c
pb_commit=58fc8645
pc_commit=version-1.900.13
opj_file=src/bin/jp2/opj_dump.c
opj_input=JP2_CFMT


mkdir -p $dir_name
cd $dir_name
git clone $pa_url $pa
cp -rf $pa $pb
cd $pa
git checkout $pa_commit
sed -i "s/infile_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"
sed -i -e '43,48d;75,113d;135d;140,175d;195d' src/lib/openjp2/mct.c
git add src/lib/openjp2/mct.c
git commit -m "remove sse2"

cd ../$pb
git checkout $pb_commit
sed -i "s/infile_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"
sed -i -e '43,48d;75,113d;135d;140,175d;195d' src/lib/openjp2/mct.c
git add src/lib/openjp2/mct.c
git commit -m "remove sse2"
cd ..


git clone $pc_url $pc
cd $pc
git checkout $pc_commit


cd $dir_name/$pc;autoreconf -i;./configure
cd $dir_name/$pc; bear make
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD


