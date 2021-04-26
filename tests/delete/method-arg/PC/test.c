#include <stdio.h>

int fib_n(int num, int just, int random)
{
	if (num == 0 || num == 1)
	{
		return num;
	}
	return fib_n(num - 1 , just , random) + fib_n(num - 2 , just , random);
}


int main(void)
{
	int k, l = 10, p=1;
	scanf("%d", &k);
	int fn = fib_n(k , l , p);
	return 0;
}
