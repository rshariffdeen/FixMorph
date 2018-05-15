MODULE S2c;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : INTEGER;
		i : INTEGER;
	BEGIN
		sum := 0; (*C1*)
		prod := 1;
		FOR i := 1 TO n BY 1 DO
			sum := sum + i;
			prod := prod * i;
			foo(sum, prod);
		END
	END sumProd;
END S2c.