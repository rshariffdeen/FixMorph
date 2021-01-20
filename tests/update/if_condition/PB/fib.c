#include <stdio.h>
#define NUM 10

int fib(int n)
{
	if (n <= 1)
	{
		return n;
	}
	return fib(n - 1) + fib(n - 2);
}


int main(int argc, char **argv)
{
	int a;
	int c = atoi(argv[0]);
	scanf("%d", &a);
	int fib_number = fib(a);
	if (c == NUM){
	   printf("SOMETHING");
	}

	printf("fib number is %d", fib_number);

	if (fib_number > 10)
	     goto warning:

	error:
	    printf("ERROR");
	warning:
	    printf("WARNING");
	return 0;
}

