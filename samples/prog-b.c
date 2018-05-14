#include <assert.h>
#include <stdio.h>

long add (int x, int y)
{

    long r = x + y ;
    return r;
}

int function (int i, int j){
    int k = 10;
    while (i < k){
        i++;
    }

    j = i + 100;
    j = 3 *k + j;

    printf("i=%d, j=%d",i,j);
    return j;
}

int main(void)
{
    int a, b, c = 7;

    while (scanf("%d", &a) > 0) {
        assert(a > 0);
        printf("fact: %lu\n", add(a,c));
        printf("sample: %d", function(a,c));
    }

    return 0;
}