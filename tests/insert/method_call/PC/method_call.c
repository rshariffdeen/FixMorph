#include <stdio.h>
#include <string.h>
#include <ctype.h>  




void testLocalRefC(int a, char* str){
     printf("the values are  %d %s\n", a, str);
}

void testGlobalRefRefC(){
    printf("this is sample print\n");
}

void testGlobalRefC(char* str){
     testGlobalRefRefC();
     printf("the string is  %s\n", str);
}

int main( ) {

    testLocalRefC(0, "test");
    return 0;
}
