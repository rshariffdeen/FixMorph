#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void testLocalRefC(int a, char* str){
     printf("the values are  %d %s\n", a, str);
}


int main( ) {
    int k = 2;
    if (k > 0){
    if (k == 2)
            k += 3;;
    testLocalRefC(k, "test");
    }
if (k > 10)

 {
       for (int l =0; ;)
        printf("RANDOM");
    } ;
if (k < 0)
       printf("OK");
    else
       printf("CHECK");

    
    return 0;
}
