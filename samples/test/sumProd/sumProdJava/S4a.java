public class S4a {

	public void sumProd(int n) {
		float prod = 1.0;
		float sum = 0.0;//C1
		for (int i = 1; i <= n; i++) {
			sum = sum + i;
			prod = prod * i;
			foo(sum, prod);
		}
	}
}