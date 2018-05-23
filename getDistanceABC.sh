#!/bin/bash

P_A_PATH=$1
P_B_PATH=$2
P_C_PATH=$3
DECKARD_PATH="/home/pedrobw/Deckard"

find . -name "*.vec" -exec rm -f {} \;

python ./crochet.py $P_A_PATH $P_B_PATH $P_C_PATH

find $P_C_PATH -name "*.c" > P_C_files.txt

while read a;
do
	file=$(echo $a | cut -d':' -f1)
	f=$(echo $a | cut -d':' -f2)
	lines=$(echo $a | cut -d':' -f3)
	start=$(echo $lines | cut -d'-' -f1)
	end=$(echo $lines | cut -d'-' -f2)
	echo A $P_A_PATH $file $f $lines $start $end;
	AUX=$PWD/$P_A_PATH/$file
	$DECKARD_PATH/src/main/cvecgen $AUX --start-line-number $start --end-line-number $end -o $AUX.$f.$lines.vec
done <diff_funcs.txt
while read b;
do
	clang-7 -Wno-everything -g -Xclang -load -Xclang lib/libCrochetLineNumberPass.so $b  2> line-function
	while read function;
	do
		f=$(echo $function | cut -d':' -f1)
		lines=$(echo $function | cut -d':' -f2)
		start=$(echo $lines | cut -d'-' -f1)
		end=$(echo $lines | cut -d'-' -f2)
		echo $f $start $end;
		$DECKARD_PATH/src/main/cvecgen $b --start-line-number $start --end-line-number $end -o $b.$f.$lines.vec
	done <line-function
	#N_LINES=$(grep --regexp="$" --count $b)
	#$DECKARD_PATH/src/main/cvecgen $b --start-line-number 1 --end-line-number $N_LINES
done <P_C_files.txt
find $P_A_PATH -name "*.vec" > vec_a.txt
find $P_C_PATH -name "*.vec" > vec_c.txt

./computeDistance.py vec_a.txt vec_c.txt