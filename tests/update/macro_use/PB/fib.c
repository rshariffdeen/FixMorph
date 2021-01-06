#include <stdio.h>

#define SWAP(a,b) ({ a ^= b; b ^= a; a ^= b;})
#define SQUARE(x) (x*x)
#define TRACE_LOG(fmt, args...) fprintf(stdout, fmt, ##args);


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
	int a = SQUARE(3);
	scanf("%d", &a);
	int fib_number = fib(a);
	printf("square number is %d", SQUARE(3));
	printf("fib number is %d", fib_number);
	return 0;
}


