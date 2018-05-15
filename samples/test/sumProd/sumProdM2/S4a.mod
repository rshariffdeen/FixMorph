MODULE S4a;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		prod := 1.0;
		sum := 0.0; (*C1*)
		FOR i := 1 TO n BY 1 DO
			sum := sum + i;
			prod := prod * i;
			foo(sum, prod);
		END
	END sumProd;
END S4a.