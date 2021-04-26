#include <stdio.h>
#include <string.h>
#include <ctype.h>  


int main( ) {
    int j = 2, k = 2, l = 5;
    for (j=0; j  < 8; j++, k++, l++){
        if (j < 0)
            printf("NEG");
          else if (k > 5)
            printf("POS");
          else
            printf("NONE");
    }

    return 0;
}
