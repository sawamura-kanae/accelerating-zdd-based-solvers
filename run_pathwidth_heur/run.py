import os
import subprocess
import json

# where to find .col files
instances = "../2023result/docs/solver/benchmark/"
# where to store log files
output = "output/"

cache_json = "cache.json"
state_json = "state.json"

EXT = ".col"

def format_outname(graph_col, time):
  return f"{graph_col}.pathwidth.time{time}.log"

def read_json(file):
  with open(file, encoding="utf8", newline="") as j:
    return json.load(j)

def write_json(file, data):
  with open(file, mode="w", encoding="utf8", newline="") as j:
    json.dump(data, j, separators=(',', ':'))

def next_state(state):
  state["current_iter_min"] *= 2
  return state

def main():
  cache = read_json(cache_json)
  state = read_json(state_json)

  while True:
    minute = state["current_iter_min"]

    nochange = True
    for root, _dirs, files in os.walk(instances):
      for file in files:
        if not file.endswith(EXT): continue # iteration twice!

        key = file[:-len(EXT)]

        if key not in cache:
          cache[key] = 0
          write_json(cache_json, cache)

        if cache[key] == 0:
          path = os.path.join(root, file)

          mins = f"{minute}m"
          outpath = os.path.join(output, format_outname(file, mins))

          if os.path.isfile(outpath): continue

          nochange = False
          ran = None
          with open(outpath, mode="w", encoding="utf8", newline="") as out:
            ran = subprocess.run(
                ["bash", "run.sh", path, mins],
                stdout=out,
                stderr=out,
            )

          if ran.returncode == 0:
            cache[key] = 1
            write_json(cache_json, cache)

    if nochange:
      return

    state = next_state(state)
    write_json(state_json, state)

if __name__ == "__main__":
  main()

# vim: expandtab sts=2 sw=2
