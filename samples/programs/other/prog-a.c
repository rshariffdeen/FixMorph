#include <assert.h>
#include <stdio.h>
#include <klee/klee.h>

long add (int x, int y)
{
    return x + y;
}

void nothing (int x){
    printf ("just having a void function");
    if (x){
        printf("x is not null");
    }else{
        printf("x is null");
    }
}

int function (int i, int j){
    int k = 10;
    while (i < k){
        i++;
    }

    j = 2*k;

    printf("i=%d, j=%d",i,j);
    if (j > 100)
        return j-100;

    klee_print_expr("i=",i);
    klee_print_expr("j=",j);
    klee_print_expr("k=",k);

    return j;
}

int main(void)
{
    int a, b, c = 7;

    klee_make_symbolic(&a, sizeof(a), "a");
    klee_make_symbolic(&b, sizeof(b), "b");

    function(a,b);

    return 0;
}
