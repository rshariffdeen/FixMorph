 void sumProd(int n) {
	float s = 0.0;//C1
	float p = 1.0; 
	int j;
	for (j = 1; j <= n; j++){
		s = s + j;
		p = p * j;
		foo(p, s);
	}
}