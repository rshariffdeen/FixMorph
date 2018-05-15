MODULE S1b;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		sum := 0.0; (*C1*)
		prod := 1.0; (*C*)
		FOR i := 1 TO n BY 1 DO
			sum := sum + i;
			prod := prod * i;
			foo(sum, prod);
		END
	END sumProd;
END S1b.