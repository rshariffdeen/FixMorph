#include <stdio.h>

int add2(int a, int b)
{
	if (a < 0 || b < 0)
	{
		return 0;
	}
	return a + b;
}

int add3(int a, int b, int c)
{
	if (a < 0 || b < 0 || c < 0)
	{
		return 0;
	}
	return a + b + c;
}

int duplicate(int a)
{
	if (a < 0 )
	{
		return 0;
	}
	return a + a;
}


int main(void)
{
	int k;
	scanf("%d", &k);
	return 0;
}
