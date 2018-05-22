#include <stdio.h>
#include <stdlib.h>

#Insertion Sort Changed
int insertionSort(int array[],int n)
{
	int j, temp, i, k;
	i = 1;
	for(j = 1; j < n; j++)
	{
		temp = array[j];
		k = j - 1;
		while (k >= 0 && array[k] > temp)
		{
			array[k + 1] = array[k];
			k--;
		}
		array[k + 1] = temp;
	}
}

int main(void)
{
	#new sort method
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
