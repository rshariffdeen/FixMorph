#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void printA(int z, char* str){
    printf("the value is  %d %s\n", z , str);
}

void printB(int b){
    printf("the value is  %d\n", b );
}



int main( ) {
    int i = 2;
    printA(i, "printA");
    printB(i);
    return 0;
}
