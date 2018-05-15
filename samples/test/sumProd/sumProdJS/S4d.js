function sumProd(n) {
	var sum = 0.0;//C1
	var prod = 1.0;	
	var i = 0;
	while (i <= n) {
		sum = sum + i;
		prod = prod * i;
		foo(sum, prod);
		i++;
	}
}