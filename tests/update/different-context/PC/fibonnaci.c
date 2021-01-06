#include <stdio.h>

/*
    add few comments to change the line numbers
*/

int fib(int n)
{
    int k = 0;
    k = k + 1;
	if (n == 0 || n == 1)
	{
		return n;
	}
	printf("value of k is %d\n", k);
	return fib(n - 1) + fib(n - 2);
}


int main(void)
{
	int a;
	scanf("%d", &a);
	int fib_number = fib(a);
	printf("fib number is %d", fib_number);
	return 0;
}
