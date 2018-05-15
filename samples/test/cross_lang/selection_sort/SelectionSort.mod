IMPLEMENTATION MODULE SelectionSort_Mod;
	PROCEDURE Sort(array : ARRAY OF INTEGER);
	VAR i, j, min, temp, pos : INTEGER;
	BEGIN
		i := 0;
		WHILE (i < array.Length) DO
			min := array[i];
			pos := i;
			FOR j:= i TO array.Length - 1 DO
				IF array[j] < min THEN
					min := array[j];
					pos := j
				END;
			END;
			temp := array[i];
			array[i] := min;
			array[pos] := temp;
			INC(i)
		END
	END Sort;
END SelectionSort.