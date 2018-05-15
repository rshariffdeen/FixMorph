#include <stdio.h>

int *selectionSort(int array[],int n)
{
	int j, temp, i, min, pos;
	i = 0;
	while (i < n)
	{
		min = array[i];
		pos = i;
		for (j = i + 1; j < n; j++) 
		{
			if (array[j] < min)
			{
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