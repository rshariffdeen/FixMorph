function sumProd(n) {
	var prod = 1.0;	
	var sum = 0.0;//C1
	for (var i = 1; i <= n; i++) {
		sum = sum + i;
		prod = prod * i;
		foo(sum, prod);
	}
}