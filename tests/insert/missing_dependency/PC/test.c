#include <stdio.h>
#include <string.h>
#include <ctype.h>  

struct Author {
  char name[50];
  int user_id;
} author;


void testLocalRefC(int a, char* str){
     int dev = 9;
     printf("the values are  %d %s\n", a, str);
}


int main( ) {
    printf("TEST C");
    return 0;
}
