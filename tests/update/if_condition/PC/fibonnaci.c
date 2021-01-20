#include <stdio.h>

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
	int a;
	scanf("%d", &a);
	int fibonacci_number = fibonacci(a);
	int c = atoi(argv[0]);
	if (c == 0){
	   printf("SOMETHING");
	}

	printf("fib number is %d", fibonacci_numberN);

	if (fibonacci_number > 10){
	    a = 10;
	      goto error:
	}

	error:
	    printf("ERROR");
	return 0;
}