#include <stdio.h>

#define SWAP(a,b) ({ a ^= b; b ^= a; a ^= b;})
#define SQUARE(x) (x*x)
#define TRACE_LOG(fmt, args...) fprintf(stdout, fmt, ##args);

#define __stringify_1(x...)	#x
#define __stringify(x...)	__stringify_1(x)

#define IWL7260_UCODE_API_OK	7
#define IWL3160_UCODE_API_OK	7

/* This struct is here for syntactic coherency, it is not used */
#define __MODULE_INFO(tag, name, info)					  \
static const char __UNIQUE_ID(name)[]					  \
  __used __attribute__((section(".modinfo"), unused, aligned(1)))	  \
  = __stringify(tag) "=" info



/* Generic info of form tag = "info" */
#define MODULE_INFO(tag, info) __MODULE_INFO(tag, tag, info)

/* Optional firmware file (or files) needed by the module
 * format is simply firmware file name.  Multiple firmware
 * files require multiple MODULE_FIRMWARE() specifiers */
#define MODULE_FIRMWARE(_firmware) MODULE_INFO(firmware, _firmware)



#define IWL7260_FW_PRE "iwlwifi-7260-"
#define IWL7260_MODULE_FIRMWARE(api) IWL7260_FW_PRE __stringify(api) ".ucode"
#define IWL3160_FW_PRE "iwlwifi-3160-"
#define IWL3160_MODULE_FIRMWARE(api) IWL3160_FW_PRE __stringify(api) ".ucode"



int main(void)
{
	int a = SQUARE(2);
	scanf("%d", &a);
	int fib_number = fib(a);
	printf("square number is %d", SQUARE(2));
	printf("fib number is %d", fib_number);
	return 0;
}

MODULE_FIRMWARE(IWL7260_MODULE_FIRMWARE(IWL7260_UCODE_API_OK));
MODULE_FIRMWARE(IWL3160_MODULE_FIRMWARE(IWL3160_UCODE_API_OK));

