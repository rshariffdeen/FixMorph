MODULE S4e;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		sum := 0.0; (*C1*)
		prod := 1.0;
		i := 1;
		IF i <= n THEN
			sum := sum + i;
			prod := prod * i;
			foo(sum, prod);
		END
	END sumProd;
END S4e.