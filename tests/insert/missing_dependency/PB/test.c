#include <stdio.h>
#include <string.h>
#include <ctype.h>  

int k = 2;

void testLocalRefA(int a, char* str){
    int dev = 9;
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    int i = 2;
    int j = 4;
    int dev;
    dev = 4;
    testLocalRefA(i, "test");
    testLocalRefA(j, "test");
    testLocalRefA(k + dev, "test");
    return 0;
}
