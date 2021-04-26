#include <stdio.h>


int fib(int number)
{
	if (number == 0 || number == 1)
	{
		return number;
	}
	return fib(number - 1) + fib(number - 2);
}

int main(void)
{
	int a;
	scanf("%d", &a);
	int fib_number = fib(a);

	return 0;
}


