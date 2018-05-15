MODULE S3e;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		sum := 0.0; (*C1*)
		prod := 1.0;
		FOR i := 1 TO n BY 1 DO
			IF n MOD 2 = 0 THEN
				INC(sum, i);
			END;
			prod := prod * i;
			foo(sum, prod);
		END
	END sumProd;
END S3e.