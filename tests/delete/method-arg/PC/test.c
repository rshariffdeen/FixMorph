#include <stdio.h>

int fib_n(int num, int just)
{
	if (num == 0 || num == 1)
	{
		return num;
	}
	return fib_n(num - 1) + fib_n(num - 2);
}


int main(void)
{
	int k, l = 10;
	scanf("%d", &k);
	int fn = fib_n(k, l);
	return 0;
}
