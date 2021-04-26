#include <stdio.h>

int main(void)
{
	int a, empty;
	float number, num=10.0;
	scanf("%d", &a);
	int fib_number = fib(a);
	a = printf("fib number is %d", fib_number);
	if (a > 0){
	    printf("TEST");
	}
	return 0;
}


