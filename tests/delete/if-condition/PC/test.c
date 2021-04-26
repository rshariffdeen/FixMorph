#include <stdio.h>

int fib_n(int num)
{
	if (num == 0 || num == 1)
	{
		return num;
	}
	return fib_n(num - 1) + fib_n(num - 2);
}


int main(void)
{
	int k;
	scanf("%d", &k);
	int fn = fib_n(k);
	k = printf("fib number is %d", fn);
	if (k > 0)
	    printf("TEST");

	return 0;
}
