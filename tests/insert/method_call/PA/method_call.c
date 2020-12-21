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
    testLocalRefA(3, "test2");
    return 0;
}
