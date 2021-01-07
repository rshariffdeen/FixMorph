#include <stdio.h>
#include <string.h>
#include <ctype.h>  

struct regmap;
struct snd_soc_component;
struct sta32x_platform_data;


/* codec private data */
struct sta32x_priv {
        struct regmap *regmap;
        struct snd_soc_component *component;
        struct sta32x_platform_data *pdata;
        unsigned int mclk;
        unsigned int format;
        int coef_shadow[50];
        int shutdown;

};


int test(struct snd_soc_component *component) {
    struct sta32x_priv *sta32x;
    return 0;
}

int main(){
    return 0;
}