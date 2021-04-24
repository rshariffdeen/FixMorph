#include <stdio.h>
#define NUM 10

int fibonacci(int number)
{
	if (number == 0 || number == 1)
	{
		return number;
	}
	return fibonacci(number - 1) + fibonacci(number - 2);
}



int main(int argc, char **argv)
{
	int i;
	scanf("%d", &i);
	int fibonacci_number = fibonacci(i);
	int k = atoi(argv[0]);
	if (k == 0) {
	   printf("SOMETHING");
	}

	if (k < 0)
	   printf("INVALID");

	printf("fib number is %d", fibonacci_number);

	if (fibonacci_number > 10) {
	    i = 10;
	    goto something;
	}

	something:
	    printf("ERROR");
	return 0;
}