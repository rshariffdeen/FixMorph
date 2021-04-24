#include <stdio.h>

/*
    add few comments to change the line numbers
*/

int fib_n(int num)
{
    int k = 0;
    k = k + 1;
	if (num == 0 || num == 1)
	{
		return num;
	}
	printf("value of k is %d\n", k);
	return fib_n(num - 1) + fib_n(num - 2);
}


int main(void)
{
	int a;
	scanf("%d", &a);
	int fib_number = fib_n(a);
	printf("fib number is %d", fib_number);
	return 0;
}
