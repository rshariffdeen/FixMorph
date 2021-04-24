#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void printA(int n, char* str){
    for(int i =0; i< a; i++)
        printf("A: the value is  %d %s\n", n, str);
}

void printB(int b){
    for(int i =0; i< b; i++)
        printf("B: the value is  %d\n", b);
}

int main( ) {
    int i = 2;
    printA(i, "printA");
    printB(i);
    return 0;
}
