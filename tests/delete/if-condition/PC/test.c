#include <stdio.h>
#define SQUARE(x) (x*x)
#define TRACE_LOG(fmt, args...) fprintf(stdout, fmt, ##args);
#define NUM 10

int main(void)
{
	int k;
	scanf("%d", &k);
	int fn = SQUARE(k);
	k = printf("fib number is %d", NUM);
	if (k > 0)
	    k = SQUARE(fn);
    printf("COMPLETE");
	return 0;


}
