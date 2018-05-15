MODULE S3c;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		sum := 0.0; (*C1*)
		prod := 1.0;
		FOR i := 1 TO n BY 1 DO
			sum := sum + i;
			prod := prod * i;
			IF n MOD 2 = 0 THEN
				foo(sum, prod);
			END
		END
	END sumProd;
END S3c.