#include <stdio.h>


int main(void)
{
	int k, empty;
	float random, num=10.0;
	scanf("%d", &k);
	int fn = fib_n(k);
	k = printf("fib number is %d", fn);
	if (k > 0){
	    printf("TEST");
	}
	return 0;
}
