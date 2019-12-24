project_name=libwebp-jasper
bug_id=shift-overflow
dir_name=$1/$project_name/$bug_id

pa=libwebp-0.2.0
pb=libwebp-0.3.0
pc=jasper-1.900.3
pc_url=https://github.com/mdadams/jasper.git
pa_url=https://chromium.googlesource.com/webm/libwebp
pa_commit=31bea324
pb_commit=7a650c6a
pc_commit=version-1.900.3


mkdir -p $dir_name
cd $dir_name
git clone $pa_url $pa
cp -rf $pa $pb

cd $pa
git checkout $pa_commit
sed -i -e '206d' examples/jpegdec.c
git add examples/jpegdec.c
git commit -m "remove longjmp"
sed -i -e '28,30d' src/dsp/dsp.h
git add src/dsp/dsp.h
git commit -m "remove sse2"

cd ../$pb
git checkout $pb_commit
sed -i -e '206d' examples/jpegdec.c
git add examples/jpegdec.c
git commit -m "remove longjmp"
sed -i -e '28,30d' src/dsp/dsp.h
git add src/dsp/dsp.h
git commit -m "remove sse2"
cd ..

git clone $pc_url $pc
cd $pc
git checkout $pc_commit


cd $dir_name/$pc;autoreconf -i;./configure"
cd $dir_name/$pc; bear make"
python /patchweave/script/python/format.py $dir_name/$pc

git add *.c
git commit -m "format style"
git reset --hard HEAD


