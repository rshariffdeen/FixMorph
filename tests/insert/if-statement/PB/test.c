#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefA(int a, char* str){
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    int j = 2;
    if (j > 0){
        if (j == 2)
            j += 3;
        testLocalRefA(j, "test");
    }

    if (j > 10){
       for (int l =0; ;)
        printf("RANDOM");
    }

    if (j < 0){
       j = 9;
       printf("OK");
    } else
       printf("CHECK");

    return 0;
}
