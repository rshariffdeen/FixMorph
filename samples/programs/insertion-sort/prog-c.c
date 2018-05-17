#include <stdio.h>
#include <stdlib.h>


void sort(float array[], int length)
{
	int a, b, c;
	float temp;
	a = 1;
	while (a < length)
	{
		b = 0;
		while (b < a && array[b] < array[a])
		{
			b++;
		}
		temp = array[a];
		for (c = a; c > b; c--)
		{
			array[c] = array[c-1];
		}
		array[b] = temp;
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