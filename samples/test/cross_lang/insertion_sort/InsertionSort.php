<?php 
	function insertionSort($arr) {
		$i = 1;
		while ($i < count($arr)) {
			$j = 0;
			while ($j < $i && $arr[$j] < $arr[$i]) {
				$j++;
			}
			$temp = $arr[$i];
			for ($k = $i; $k > $j; $k-- ) {
				$arr[$k] = $arr[$k-1];
			}
			$arr[$j] = $temp;
			$i++;
		}
	}
?>