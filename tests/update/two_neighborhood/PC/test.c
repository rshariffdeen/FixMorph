#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void printX(int a, char* str){
    print("X: the values are  %d %s\n", a, str);
}

void printY(int a, char* str){
    printf("Y: the values are  %d %s\n", a, str);
}

int main( ) {
    int k = 2;
    printX(k, "printX");
    printY(k, "printY");
    return 0;
}