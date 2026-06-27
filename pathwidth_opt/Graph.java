import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.Random;
import java.util.Scanner;

public class Graph {
	
	static ArrayList<int[]> randomGraph(int N, int p)
	{
		return randomGraph(N, p, new Random().nextLong());
	}
	static ArrayList<int[]> randomGraph(int N, int p, long seed)
	{
		Random rnd = new Random(seed);
		ArrayList<int[]> es = new ArrayList<>();
		for (int i = 0; i < N; i++) {
			for (int j = i + 1; j < N; j++) {
				if (rnd.nextInt(100) < p) {
					es.add(new int[] {i, j});
				}
			}
		}
		return es;
 	}
	
	static ArrayList<int[]> read()
	{
		Scanner sc = new Scanner(System.in);
		int M = sc.nextInt();
		ArrayList<int[]> es = new ArrayList<>();
		for (int i = 0; i < M; i++) {
			es.add(new int[] {sc.nextInt(), sc.nextInt()});
		}
		return es;
	}
	
	static ArrayList<int[]> readCol(String fileName)
	{
		try {
			ArrayList<int[]> es = new ArrayList<>();
			Scanner sc = new Scanner(new File(fileName));
			while (sc.hasNextLine()) {
				String line = sc.nextLine().trim();
				String[] tokens = line.split(" ");
				if (tokens[0].equals("p")) {
//					int M = Integer.parseInt(tokens[2]);
				} else if (tokens[0].equals("e")){
					int s = Integer.parseInt(tokens[1]) - 1;
					int t = Integer.parseInt(tokens[2]) - 1;
					es.add(new int[] {s,t});
				}
			}
			return es;
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
		return null;
	}
	
	static ArrayList<int[]> romeGraph(String fileName)
	{
		ArrayList<int[]> es = new ArrayList<>();
		try {
			Scanner sc = new Scanner(new File("rome/" + fileName));
			while (sc.hasNextLine()) {
				String line = sc.nextLine().trim();
				if (line.startsWith("<edge")) {
					String[] tokens = line.split(" ");
					int s = -1;
					int t = -1;
					for (String token: tokens) {
						token = token.trim();
						if (token.startsWith("source")) {
							token = token.substring(token.indexOf("\"") + 2, token.lastIndexOf("\""));
							s = Integer.parseInt(token);
						} else if (token.startsWith("target")) {
							token = token.substring(token.indexOf("\"") + 2, token.lastIndexOf("\""));
							t = Integer.parseInt(token);
						}
					}
					if (s >= 0 && t >= 0) {
						es.add(new int[] {s, t});
					}
				}
			}
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return es;
	}
	
	public static void main(String[] args) {
		readCol("IS_exp_instance001.col");
	}
}