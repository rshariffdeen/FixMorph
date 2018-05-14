#include <assert.h>
#include <stdio.h>
#include <time.h>

long sum (int a, int b)
{
    return a + b ;
}

int procedure (int i, int j){
    int k = 10;

    clock_t start  = clock();
    clock_t finish;

    while (i < k){
        i++;
    }

    finish = clock();
    printf("look took :%fms\n", (double)finish-start/CLOCKS_PER_SEC);

    j = 2*k;

    printf("i=%d, j=%d",i,j);
    return j;
}

int main(void)
{
    int i, j, k = 7;
    scanf("%d", &i);
    printf("fact: %lu\n", sum(i,k));
    printf("sample: %d", procedure(i,k));
    return 0;
}