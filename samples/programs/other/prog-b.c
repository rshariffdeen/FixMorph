#include <assert.h>
#include <stdio.h>
#include <klee/klee.h>

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

    klee_make_symbolic(&a,sizeof(a),"a");
    if(a>0)
        b=a+10;
    else
        b=-a+10;
    klee_print_expr("b=",b);


    return 0;
}