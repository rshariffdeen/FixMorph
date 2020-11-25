#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testFunc(int a, char* str){
    printf("the value of a is %d %s\n", a, str);
}

int main( ) {
    int i = 0;
    testFunc(i, "test");
    testFunc(i, "test2");
    return 0;
}
