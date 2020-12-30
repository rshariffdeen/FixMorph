#include <stdio.h>

/*
    add few comments to change the line numbers
*/

#define SWAP(a,b) ({ a ^= b; b ^= a; a ^= b;})
#define SQUARE(x) (x*x)
#define TRACE_LOG(fmt, args...) fprintf(stdout, fmt, ##args);

TRACE_LOG("%s", "testing trace");

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
	int b = SQUARE(2);
	scanf("%d", &b);
	int fib_number = fib(b);
	printf("square number is %d", SQUARE(2));
	printf("fib number is %d", fib_number);
	return 0;
}
