public class S2c {

	public void sumProd(int n) {
		int sum = 0;//C1
		int prod = 1;
		for (int i = 1; i <= n; i++) {
			sum = sum + i;
			prod = prod * i;
			foo(sum, prod);
		}
	}
}