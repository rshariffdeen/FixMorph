function sort(array) {
	var i, j, temp;
	i = 1;
	while (i < array.length) {
		j = 0;
		while (j < i && array[j] < array[i]) {
			j++;
		}
		temp = array[i];
		for (var k = i; k > j; k-- ) {
			array[k] = array[k-1];
		}
		array[j] = temp;
		i++;
	}
}