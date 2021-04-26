#include <stdio.h>

int fib(int n, int o)
{
	if (n == 0 || n == 1)
	{
		return n;
	}
	return fib(n - 1, o) + fib(n - 2, o);
}


int main(void)
{
	int a, c=1;
	scanf("%d", &a);
	int fib_number = fib(a, c);
	return 0;
}


