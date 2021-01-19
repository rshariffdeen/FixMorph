#include <stdio.h>

int fib(int n)
{
	if (n == 0 || n == 1)
	{
		return n;
	}
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


