MODULE S4b;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		sum := 0.0; (*C1*)
		prod := 1.0;
		FOR i := 1 TO n BY 1 DO
			prod := prod * i;
			sum := sum + i;
			foo(sum, prod);
		END
	END sumProd;
END S4b.