#include <stdio.h>

int fibonacci(int number)
{
	if (    number <=  1)
	{
		return number;
	}
	return fibonacci(number - 1) + fibonacci(number - 2);
}


int main(void)
{
	int a;
	scanf("%d", &a);
	int fibonacci_number = fibonacci(a);
	printf("fib number is %d", fibonacci_number);
	return 0;
}