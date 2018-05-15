function sumProd(n) {
	var sum = 0.0;//C1
	var prod = 1.0;	
	for (var i = 1; i <= n; i++) {
		if (i % 2 == 0) sum += i;
		prod = prod * i;
		foo(sum, prod);
	}
}