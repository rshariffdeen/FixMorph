#include <stdio.h>
#include <string.h>
#include <ctype.h>  


int main( ) {
    int j = 2, k = 2, l = 5;
    for (j=0; j  < 8; j++)
        l = k + j;
    printf("number is %d", j);
    return 0;
}
