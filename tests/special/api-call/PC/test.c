#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testGlobalRefX(){
    printf("X: this is sample print\n");
}

void testGlobalRefY(){
    printf("Y: this is sample print\n");
}


void testLocalX(int a, char* str){
    testGlobalRefX();
    printf("the values are  %d %s\n", a, str);
}

void testLocalY(int a, char* str){
    testGlobalRefX();
    printf("the values are  %d %s\n", a, str);
}

void testLocalZ(int a, char* str){
    testGlobalRefY();
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    testLocalX(3, "testA");
    testLocalY(3, "testB");
    testLocalZ(3, "testC");
    return 0;
}
