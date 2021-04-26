#include <stdio.h>
#define SQUARE(x) (x*x)
#define TRACE_LOG(fmt, args...) fprintf(stdout, fmt, ##args);
#define NUM 10

int main(void)
{
	int a;
	scanf("%d", &a);
	int fib_number = SQUARE(a);
	a = printf("fib number is %d", NUM);
	if (a > 0)
	    a = SQUARE(fib_number);
    printf("COMPLETE");
	return 0;
}


