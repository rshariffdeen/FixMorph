public class S2a {

	public void sumProd(int n) {
		float s = 0.0;//C1
		float p = 1.0;
		for (int j = 1; j <= n; j++) {
			s = s + j;
			p = p * j;
			foo(s, p);
		}
	}
}