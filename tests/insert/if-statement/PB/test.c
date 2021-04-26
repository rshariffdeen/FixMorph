#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefA(int a, char* str){
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    int j = 2;
    if (j > 1)
        j += 3;
    if ( j > 0)
        testLocalRefA(j, "test");
    return 0;
}
