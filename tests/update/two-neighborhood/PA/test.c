#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void printA(int n, char* str){
    printf("A: the value is  %d %s\n", n, str);
}

void printB(int b){
    printf("B: the value is  %d\n", b);
}



int main( ) {
    int i = 2;
    printA(i, "printA");
    printB(i);
    return 0;
}
