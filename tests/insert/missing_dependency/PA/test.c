#include <stdio.h>
#include <string.h>
#include <ctype.h>  

int k = 2;

struct Author {
  char name[50];
  int user_id;
  int rank;
} author;


void testLocalRefA(int a, char* str){
    int dev = 9;
    printf("the values are  %d %s\n", a, str);
}


int main( ) {
    printf("TEST A");
    struct Author author;
    float only_declaration;
    int i = 2;
    int dev;
    dev = 4;
    dev = 124;
    dev = 326346;
    return 0;
}
