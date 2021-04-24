#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void printX(int x, char* str){
    printf("X: the values are  %d %s\n", x, str);
}

void printY(int y){
    printf("Y: the values are  %d\n", y);
}

int main( ) {
    int k = 2;
    printX(k, "printX");
    printY(k);
    return 0;
}