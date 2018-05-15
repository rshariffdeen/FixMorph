MODULE Fibonacci;
	PROCEDURE Fib(num : INTEGER):INTEGER;
	BEGIN
		IF (num = 0) OR (num = 1) THEN
			RETURN num;
		END;
		RETURN Fib(n-1) + Fib(n-2);
	END Fib;
END Fibonacci.