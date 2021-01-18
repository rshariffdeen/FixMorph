#include <stdio.h>
#include <string.h>
#include <ctype.h>  


int testTotal(int a, int b){
   return a + b;
}


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
    int t = testTotal(1,2);
    testLocalRefC(0, "test");
    return 0;
}
