#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

using Edges = vector<pair<int, int>>;  // list of pairs
// -std=c++17

int read_col(string path, Edges &edges) {
  int n;
  ifstream ifs(path, ios_base::in);
  string line;

  if (!ifs.is_open()) {
    cerr << "error opening file " << path << endl;
    exit(1);
  }

  for (; getline(ifs, line);) {
    istringstream sin(line);
    char f;
    int a, b;

    sin >> f;
    if (f == 'e') {
      sin >> a >> b;
      edges.push_back({a, b});
    } else if (f == 'p') {
      sin >> n;
    }
  }

  return n;
}

vector<int> edges_to_bags_sizes(Edges edges, int n, vector<int> &sizes) {
  vector<int> degs(n + 1);
  for (auto [e1, e2] : edges) {
    degs[e1]++;
    degs[e2]++;
  }

  vector<bool> mid(n + 1);  // misled name
  int count = 0;
  for (auto [e1, e2] : edges) {
    int prev_count = count;
    vector<bool> prev_mid = mid;

    degs[e1]--;
    degs[e2]--;

    if (degs[e1] && !mid[e1]) {
      mid[e1] = true;
      count++;
    } else if (!degs[e1] && mid[e1]) {
      mid[e1] = false;
      count--;
    }

    if (degs[e2] && !mid[e2]) {
      mid[e2] = true;
      count++;
    } else if (!degs[e2] && mid[e2]) {
      mid[e2] = false;
      count--;
    }

    sizes.push_back(prev_count + (prev_mid[e1] ? 0 : 1) +
                    (prev_mid[e2] ? 0 : 1));  // add edge
  }

  return sizes;
}

int bags_sizes_to_width(vector<int> &bags) {
  int mx = 0;
  for (auto bag : bags) {
    mx = max(mx, bag);
  }

  return mx - 1;
}

// takes .col path as an argument
int main(int argc, char *argv[]) {
  if (argc != 2) {
    cout << "Usage: " << argv[0] << " <path.col>" << endl;
    return 1;
  }

  string path = argv[1];
  Edges edges;
  int n = read_col(path, edges);

  vector<int> sizes;
  edges_to_bags_sizes(edges, n, sizes);
  cout << bags_sizes_to_width(sizes) << endl;

  return 0;
}

// vim: expandtab sw=2 sts=2
