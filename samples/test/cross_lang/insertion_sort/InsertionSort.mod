MODULE InsertionSort;
	PROCEDURE Sort(array : ARRAY OF INTEGER);
	VAR i, j, k, temp : INTEGER;
	BEGIN
		i := 1;
		WHILE (i < array.Length) DO
			j := 0;
			WHILE (j < i) AND (array[j] < array[i]) DO 
				INC(j);
			END;
			temp := array[i];
			FOR k:=i TO j - 1 BY -1 DO
				array[k] := array[k-1];
			END;
			array[j] := temp;
			INC(i)
		END
	END Sort;
END InsertionSort.