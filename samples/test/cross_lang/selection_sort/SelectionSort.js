function sort(array) {
	var i,j,min,pos,temp;
	i = 0;
	while (i < array.length) {
		min = array[i];
		pos = i;
		for (var j = i + 1; j < array.length; j++) {
			if (array[j] < min) {
				min = array[j];
				pos = j;
			}
		}
		temp = array[i];
		array[i] = array[pos];
		array[pos] = temp;
		i++;
	}
}