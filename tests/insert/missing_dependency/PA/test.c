#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefA(int a, char* str){
    printf("the values are  %d %s\n", a, str);
}

void testGlobalRefRef(){
    printf("this is sample print\n");
}

void testGlobalRefA(char* str){
    testGlobalRefRefA();
    printf("the string is  %s\n", str);
}

int main( ) {
    int i = 2;
    if (i == 2){
       testGlobalRefRef();
    }
    return 0;
}
