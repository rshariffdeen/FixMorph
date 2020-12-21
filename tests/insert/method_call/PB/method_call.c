#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testFunc(int a, char* str){
    printf("the value of a is %d %s\n", a, str);
}

int main( ) {
    int i = 0;
    testFunc(i, "test");
    testFunc(3, "test2");
    printf("\ntest function\n");
    return 0;
}
