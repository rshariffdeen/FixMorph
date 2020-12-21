#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefC(char* str){
    printf("the value of a is %d %s\n", a, str);
}

void testGlobalRefC(char* str){
    printf("the value of a is %d %s\n", str);
}

int main( ) {

    testLocalRefC(0, "test");
    return 0;
}
