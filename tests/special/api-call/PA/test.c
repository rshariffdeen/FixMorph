#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testGlobalRefA(){
    printf("A: this is sample print\n");
}

void testGlobalRefB(){
    printf("B: this is sample print\n");
}


void testLocalA(int a, char* str){
    testGlobalRefA();
    printf("the values are  %d %s\n", a, str);
}

void testLocalB(int a, char* str){
    testGlobalRefA();
    printf("the values are  %d %s\n", a, str);
}

void testLocalC(int a, char* str){
    testGlobalRefB();
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    testLocalA(3, "testA");
    testLocalB(3, "testB");
    testLocalC(3, "testC");
    return 0;
}
