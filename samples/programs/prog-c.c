#include <assert.h>
#include <stdio.h>
#include <time.h>

long sum (int a, int b)
{
    return a + b ;
}

int procedure (int x, int y){
    int z = 10;

    clock_t start  = clock();
    clock_t finish;

    while (x < z){
        x++;
    }

    finish = clock();
    printf("look took :%fms\n", (double)finish-start/CLOCKS_PER_SEC);

    y = 2*z;

    printf("i=%d, j=%d",x,y);
    return y;
}

int main(void)
{
    int i, j, k = 7;
    scanf("%d", &i);
    printf("fact: %lu\n", sum(i,k));
    printf("sample: %d", procedure(i,k));
    return 0;
}