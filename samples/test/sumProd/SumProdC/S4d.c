 void sumProd(int n) {
	float sum = 0.0;//C1
	float prod = 1.0;
	int i =1;
	while (i <= n) {
		sum = sum + i;		
		prod = prod * i;
		foo(sum, prod);
		i++;
	}
}