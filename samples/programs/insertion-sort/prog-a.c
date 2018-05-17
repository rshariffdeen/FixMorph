#include <stdio.h>

int *insertionSort(int array[],int n)
{
	int j, temp, i, k;
	i = 1;
	while (i < n)
	{
		j = 0;
		while (j < i && array[j] < array[i]) 
		{
			j++;
		}
		temp = array[i];
		for (k = i; k > j; k--) 
		{
			array[k] = array[k-1];
		}
		array[j] = temp;
		i++;
	}
}