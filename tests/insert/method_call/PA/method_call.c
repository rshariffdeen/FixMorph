#include <stdio.h>
#include <string.h>
#include <ctype.h>  

int testSum(int a, int b, int c){
   return a + c;
}

void testLocalRefA(int a, char* str){
    printf("the values are  %d %s\n", a, str);
}

void testGlobalRefRefA(){
    printf("this is sample print\n");
}

void testGlobalRefA(char* str){
    testGlobalRefRefA();
    printf("the string is  %s\n", str);
}

int main( ) {
    int p = testSum(1, 2, 3);
    testLocalRefA(3, "test2");
    return 0;
}
