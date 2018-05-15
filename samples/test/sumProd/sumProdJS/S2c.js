function sumProd(n) {
	var sum = 0;//C1
	var prod = 1;
	for (var i = 1; i <= n; i++) {
		sum = sum + i;
		prod = prod * i;
		foo(sum, prod);
	}
}
