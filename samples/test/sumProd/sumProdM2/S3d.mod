MODULE S3d;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		sum := 0.0; (*C1*)
		prod := 1.0;
		FOR i := 1 TO n BY 1 DO
			sum := sum + i;
			(* line deleted *)
			foo(sum, prod);
		END
	END sumProd;
END S3d.