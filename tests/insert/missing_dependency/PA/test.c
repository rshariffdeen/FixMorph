#include <stdio.h>
#include <string.h>
#include <ctype.h>  

int k = 2;

void testLocalRefA(int a, char* str){
    int dev = 9;
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    printf("TEST A");
    int i = 2;
    int dev;
    dev = 4;
    dev = 124;
    dev = 326346;
    return 0;
}
