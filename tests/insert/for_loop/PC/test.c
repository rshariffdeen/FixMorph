#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefC(int a, char* str){
     printf("the values are  %d %s\n", a, str);
}


int main( ) {
    int k = 2;
    testLocalRefC(k, "test");
    return 0;
}
