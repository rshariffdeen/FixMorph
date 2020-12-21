#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefA(int a, char* str){
    printf("the value of a is %d %s\n", a, str);
}

void testGlobalRefA(char* str){
    printf("the value of a is %d %s\n", str);
}

int main( ) {
    int i = 0;
    testLocalRefA(i, "test");
    testLocalRefA(3, "test2");
    printf("\ntest function\n");
    return 0;
}
