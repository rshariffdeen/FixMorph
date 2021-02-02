#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefA(int a, char* str){
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    int i = 2;
    for (i=0; i< 3; i++)
        testLocalRefA(i, "test");
    return 0;
}
