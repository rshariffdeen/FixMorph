 void sumProd(int n) {
	float sum = 0.0;//C1
	float prod = 1.0;
	int i;
	for (i = 1; i <= n; i++) {
		sum = sum + i; 
		//line deleted
		foo(sum, prod);
	}
}