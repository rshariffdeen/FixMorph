#include <assert.h>
#include <stdio.h>

long sum (int a, int b)
{
    return a + b ;
}

int main(void)
{
    int i, j, k = 7;
    scanf("%d", &i);
    printf("fact: %lu\n", sum(i,k));

    return 0;
}