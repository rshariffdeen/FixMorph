MODULE S4c;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		sum := 0.0; (*C1*)
		prod := 1.0;		
		FOR i := 1 TO n BY 1 DO
			sum := sum + i;
			foo(sum, prod);
			prod := prod * i;
		END
	END sumProd;
END S4c.