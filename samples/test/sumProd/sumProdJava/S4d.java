public class S4d {

	public void sumProd(int n) {
		float sum = 0.0;//C1
		float prod = 1.0;
		int i = 0;
		while (i <= n) {
			sum = sum + i;
			prod = prod * i;
			foo(sum, prod);
			i++;
		}
	}
}