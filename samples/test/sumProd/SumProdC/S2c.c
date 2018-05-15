 void sumProd(int n) {
	int sum = 0;//C1
	int prod = 1;
	int i;
	for (i = 1; i <= n; i++) {
		sum = sum + i;
		prod = prod * i;
		foo(sum, prod);
	}
}