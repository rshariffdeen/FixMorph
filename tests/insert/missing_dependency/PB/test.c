#include <stdio.h>
#include <string.h>
#include <ctype.h>  

int k = 2;
int l = 3;

void testLocalRefA(int a, char* str){
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    int i = 2;
    int j = 4;
    testLocalRefA(i, "test");
    testLocalRefA(j, "test");
    testLocalRefA(k, "test");
    testLocalRefA(l, "test");
    return 0;
}
