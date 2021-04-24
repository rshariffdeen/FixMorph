#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void printN(int x, char* str){
    printf("N: the value is  %d %s\n", x , str);
}

void printY(int y){
    printf("Y: the value is  %d\n", y);
}

int main( ) {
    int k = 2;
    printX(k, "printX");
    printY(k);
    return 0;
}