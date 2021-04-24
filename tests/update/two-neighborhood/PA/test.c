#include <stdio.h>
#include <string.h>
#include <ctype.h>  

void printA(int a, char* str){
    printf("A: the value is  %d %s\n", a, str);
}

void printB(int a){
    printf("B: the value is  %d\n", a);
}



int main( ) {
    int i = 2;
    printA(i, "printA");
    printB(i);
    return 0;
}
