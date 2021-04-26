#include <stdio.h>
#define NULL 2

int fib(int n, int m, int o)
{
	if (n == 0 || n == 1)
	{
		return n;
	}
	return fib(n - 1 , m , o) + fib(n - 2 , m , o);
}


int main(void)
{
	int a, v=10, c = 1;
	scanf("%d", &a);
	int fib_number = fib(a , v , c);
	v = fib_number + a - fib(v,c,a) - c;
	return 0;
}


