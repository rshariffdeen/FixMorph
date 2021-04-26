#include <stdio.h>

int fib(int n, int m)
{
	if (n == 0 || n == 1)
	{
		return n;
	}
	return fib(n - 1) + fib(n - 2);
}


int main(void)
{
	int a, b=10;
	scanf("%d", &a);
	int fib_number = fib(a, b);
	return 0;
}


