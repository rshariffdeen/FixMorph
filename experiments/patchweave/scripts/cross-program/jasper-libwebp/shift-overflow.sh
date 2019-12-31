project_name=jasper-libwebp
bug_id=shift-overflow
dir_name=$1/$project_name/$bug_id

pa=jasper-1.900.3
pb=jasper-1.900.4
pc=libwebp-0.2.0
pa_url=https://github.com/mdadams/jasper.git
pc_url=https://chromium.googlesource.com/webm/libwebp
pa_commit=8b6e9a0
pb_commit=6109f6a
pc_commit=v0.2.0


mkdir -p $dir_name
cd $dir_name
git clone $pa_url $pa
cp -rf $pa $pb

cd $pa
git checkout $pa_commit


cd ../$pb
git checkout $pb_commit
cd ..

git clone $pc_url $pc
cd $pc
git checkout $pc_commit
sed -i -e '206d' examples/jpegdec.c
git add examples/jpegdec.c
git commit -m "remove longjmp"

sed -i -e '28,30d' src/dsp/dsp.h
git add src/dsp/dsp.h
git commit -m "remove sse2"

cd $dir_name/$pc;autoreconf -i;./configure
cd $dir_name/$pc; bear make
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD


