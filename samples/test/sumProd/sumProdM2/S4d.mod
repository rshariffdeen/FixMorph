MODULE S4d;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		sum := 0.0; (*C1*)
		prod := 1.0;
		i := 1;
		WHILE i <= n DO
			sum := sum + i;
			prod := prod * i;
			foo(sum, prod);
			INC(i)
		END
	END sumProd;
END S4d.