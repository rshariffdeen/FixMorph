function sumProd(n) {
		var s = 0.0;//C1
		var p = 1.0;
		for (var j = 1; j <= n; j++){
			s = s + j;
			p = p * j;
			foo(p, s);
		}
	}
}