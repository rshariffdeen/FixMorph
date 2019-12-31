project_name=openjpeg-libwebp
bug_id=signed-int-overflow
dir_name=$1/$project_name/$bug_id

pa=openjpeg-1.5
pb=openjpeg-1.5.1
pc=libwebp-0.3.0
pa_url=https://github.com/uclouvain/openjpeg.git
pc_url=https://chromium.googlesource.com/webm/libwebp
pa_commit=7720188f
pb_commit=6280b5ad
pc_commit=v0.3.0
opj_file=applications/codec/j2k_to_image.c
opj_input=JP2_CFMT

mkdir -p $dir_name
cd $dir_name
git clone $pa_url $pa
cp -rf $pa $pb

cd $pa
git checkout $pa_commit
sed -i "s/get_file_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"


cd ../$pb
git checkout $pb_commit
sed -i "s/get_file_format(infile)/$opj_input/g" $opj_file
git add $opj_file
git commit -m "fix input format"
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


