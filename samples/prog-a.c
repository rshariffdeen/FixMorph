#include <assert.h>
#include <stdio.h>

long add (int x, int y)
{
    return x + y;
}

int main(void)
{
    int a, b, c = 7;

    while (scanf("%d", &a) > 0) {
        assert(a > 0);
        printf("fact: %lu\n", add(a,c));
    }

    return 0;
}
