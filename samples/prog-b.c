#include <assert.h>
#include <stdio.h>

long int add (int x, int y)
{
    long int r = x + y ;
    return r;
}

int main(void)
{
    int a, b, c = 7;

    while (scanf("%d", &a) > 0) {
        assert(a > 0);
        printf("fact: %lu\n", add(a,c));
    }

    return 0;
}