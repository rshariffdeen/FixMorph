#include <stdio.h>
#include <stdlib.h>

int insertionSort(int array[],int n)
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



	return 1;
}

int main(void)
{
	int array[10];

	for (int i=0; i< 10; i++){
		array[i] = rand()%100;
	}

	insertionSort(array,10);

	for (int i=0; i< 10; i++){
		printf("%d ", array[i]);
	}

	return 0;
}
