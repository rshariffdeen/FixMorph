class bs{
public static int[] bubblesort(int[] numbers) {
    boolean swapped = true;
    for(int i = numbers.length - 1; i > 0 && swapped; i--) {
        swapped = false;
        for (int j = 0; j < i; j++) {
            if (numbers[j] > numbers[j+1]) {
                int temp = numbers[j];
                numbers[j] = numbers[j+1];
                numbers[j+1] = temp;
                swapped = true;
            }
        }
    }
    return numbers;
}
}
