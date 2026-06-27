
import java.util.ArrayList;
import java.util.Arrays;
import java.util.BitSet;
import java.util.HashSet;

public class Pathwidth {

	
	private static HashSet<VertexSet> failure;
	private static int[] best;
	private static VertexSet[] nb;
	private static String fileName;
	
	public static int run(int N, ArrayList<int[]> edges) {
		nb = new VertexSet[N];
		for (int i = 0; i < N; i++) {
			nb[i] = new VertexSet();
			nb[i].set(i);
		}
		for (int i = 0; i < N; i++) {
			for (int[] edge: edges) {
				if (edge[0] == i || edge[1] == i) {
					nb[edge[0]].set(edge[1]);
					nb[edge[1]].set(edge[0]);
				}
			}
		}
		
		int[][] edgeIds = new int[N][N];
		for (int i = 0; i < edges.size(); i++) {
			int[] edge = edges.get(i);
			edgeIds[edge[0]][edge[1]] = edgeIds[edge[1]][edge[0]] = i;
		}
		
		failure = new HashSet<>();
		best = new int[N];
		for (int i = 0; i < N; i++) {
			best[i] = i;
		}
		greedy();
		
		for (int k = N; k > 0; k--) {
			if (!search(0, k, new VertexSet(), new VertexSet(), new int[N])) {
				// vertex separation number is k + 1 (i.e., pathwidth k)
				return k + 1;
			}
			
//			int[] edgeOrder = findEdgeOrder(N, edges.size(), edgeIds);
			String str = Arrays.toString(best);
//			int lw = linearwidth(edges, edgeOrder);
//			log(k + " " + lw + "\n" + str.substring(1, str.length() - 1));
			// Ensure that pathwidth is at most k - 1
			System.out.println(k + "\n" + str.substring(1, str.length() - 1));

			return -1;
		}

		return -1;
	}
	
//	private static int[] findEdgeOrder(int N, int M, int[][] edgeIds) {
//		int[] edges = new int[M];
//		boolean[] used = new boolean[N];
//		for (int i = 0, k = 0; i < N; i++) {
//			int u = best[i];
//			used[u] = true;
//			for (int v = nb[u].nextSetBit(0); v >= 0; v = nb[u].nextSetBit(v + 1)) {
//				if (used[v]) continue;
//				edges[k++] = edgeIds[u][v];
//			}
//		}
//		return edges;
//	}
	
//	static int linearwidth(ArrayList<int[]> edges, int[] edgeOrder)
//	{
//		int k = 0;
//		int[] deg = new int[nb.length];
//		BitSet mid = new BitSet();
//		for (int i = 0; i < edgeOrder.length; i++) {
//			int[] edge = edges.get(edgeOrder[i]);
//			if (deg[edge[0]] == 0) {
//				mid.set(edge[0]);
//			}
//			if (deg[edge[1]] == 0) {
//				mid.set(edge[1]);
//			}
//			deg[edge[0]]++;
//			deg[edge[1]]++;
//			if (deg[edge[0]] == nb[edge[0]].cardinality() - 1) {
//				mid.clear(edge[0]);
//			}
//			if (deg[edge[1]] == nb[edge[1]].cardinality() - 1) {
//				mid.clear(edge[1]);
//			}
//			k = Math.max(k, mid.cardinality());
//		}
//		return k;
//	}

	// return true if there is a vertex ordering of width at most k such that U is the set of vertices in a prefix
	private static boolean search(int t, int k, VertexSet U, VertexSet NU, int[] order) {
		if (t == order.length) {
			best = Arrays.copyOf(order, order.length);
			return true;
		}
		if (failure.contains(U)) {
			return false;
		}
		
		for (int i = 0; i < order.length; i++) {
			int u = best[i];
			if (U.get(u)) continue;
			VertexSet nu = NU.union(nb[u]).delete(U);
			if (NU.cardinality() >= nu.cardinality() - 1) {
				order[t] = u;
				nu.clear(u);
				return search(t + 1, k, U.add(u), nu, order);
			}
		}
		
		if (NU.cardinality() >= k) {
			failure.add(U);
			return false;
		}
		
		for (int i = 0; i < order.length; i++) {
			int u = best[i];
			if (U.get(u)) continue;
			VertexSet nu = NU.union(nb[u]).delete(U);
			if (k < nu.cardinality() - 1) continue;
			order[t] = u;
			nu.clear(u);
			if (search(t + 1, k, U.add(u), nu, order)) {
				return true;
			}
		}
		
		failure.add(U);
		return false;
	}

	private static int greedy()
	{
		VertexSet U = new VertexSet();
		VertexSet nu = new VertexSet();
		int N = nb.length;
		int width = 0;
		for (int i = 0; i < N; i++) {
			int nw = N + 1;
			int bi = -1;
			VertexSet b = null;
			for (int j = 0; j < N; j++) {
				if (U.get(j)) continue;
				VertexSet ne = nu.union(nb[j]).delete(U);
				if (nw > ne.cardinality()) {
					nw = ne.cardinality();
					b = ne;
					bi = j;
				}
			}
			width = Math.max(width, nw - 1);
			U.set(bi);
			nu = b;
			b.clear(bi);
			best[i] = bi;
		}
		return width;
	}

	private static class VertexSet extends BitSet {
		VertexSet union(VertexSet set)
		{
			VertexSet copy = (VertexSet) clone();
			copy.or(set);
			return copy;
		}
		
		VertexSet add(int u)
		{
			VertexSet copy = (VertexSet) clone();
			copy.set(u);
			return copy;
		} 
		
		VertexSet delete(VertexSet set)
		{
			VertexSet copy = (VertexSet) clone();
			copy.andNot(set);
			return copy;
		}
	}
	
//	static void log(String message)
//	{
//		try {
//			PrintWriter pw = new PrintWriter(new File("log/pathwidth/" + fileName));
//			pw.println(message);
//			pw.close();
//		} catch (FileNotFoundException e) {
//			// TODO Auto-generated catch block
//			e.printStackTrace();
//		}
//	}
	
	public static void main(String[] args) {
//		ArrayList<int[]> es = Graph.randomGraph(5, 25, 1234L);
//		ArrayList<int[]> es = Graph.read();
//		for (int[] e: es) {
		
		fileName = args[0];
		System.out.println(fileName);
		// fileName = "IS_exp_instance011.col";
		ArrayList<int[]> es = Graph.readCol(fileName);
		
//		for (int[] e: es) {
//			System.out.println(e[0] + " " + e[1]);
//		}
//		System.out.println("=========");
		int N = 0;
		for (int[] e: es) {
			N = Math.max(N, e[0] + 1);
			N = Math.max(N, e[1] + 1);
		}
		long time = System.currentTimeMillis();
		int pw = run(N, es);
		time = System.currentTimeMillis() - time;
		// #node	#edges	pathwidth	time(ms)
		System.out.println(fileName + "\t" + N + "\t" + es.size() + "\t" + pw + "\t" + time);
	}

}
