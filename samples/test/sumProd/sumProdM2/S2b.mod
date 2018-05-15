MODULE S2b;
	PROCEDURE sumProd(n : INTEGER);
	VAR 
		sum, prod : REAL;
		i : INTEGER;
	BEGIN
		s := 0.0; (*C1*)
		p := 1.0; 
		FOR i := 1 TO n BY 1 DO
			s := s + i;
			p := p * i;
			foo(p, s);
		END
	END sumProd;
END S2b.