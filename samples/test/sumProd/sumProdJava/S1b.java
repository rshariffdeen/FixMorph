public class S1b {

	public void sumProd(int n) {
		float sum = 0.0;//C1'
		float prod = 1.0;//C
		for (int i = 1; i <= n; i++) {
			sum = sum + i;
			prod = prod * i;
			foo(sum, prod);
		}
	}
}