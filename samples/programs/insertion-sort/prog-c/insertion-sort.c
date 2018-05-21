#include <stdio.h>
#include <stdlib.h>


int sort(float array[], int length)
{
	int a, b, c;
	float temp;
	a = 1;
	while (a < length)
	{
		b = 0;
		while (j < a && array[j] < array[a])
		{
			j++;
		}
		temp = array[a];
		for (k = a; k > j; k--)
		{
			array[k] = array[k-1];
		}
		array[j] = temp;
		a++;
	}
}

int main(void)
{
	float numbers[10];

	for (int i=0; i< 10; i++){
		numbers[i] = 100 * ((float)rand()/(float)(RAND_MAX));
	}


	sort(numbers,10);

	for (int i=0; i< 10; i++){
		printf("%.2f ", numbers[i]);
	}

	return 0;
}