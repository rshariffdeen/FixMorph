#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefC(int a, char* str){
     printf("the values are  %d %s\n", a, str);
}


int main( ) {
    int k = 2;
    if (k > 0){
        k += 3;
        testLocalRefC(k, "test");
    }
    printf("CHECK");
    return 0;
}
