import re, os, shutil
from os import path


def extract_hour(p: str, TIMEOUT: str):
    item = re.search(f"(?<={TIMEOUT})[0-9.]+(?=h.log)", p)
    return float(item.group(0)) * 60 * 60 if item else None


def extract_sec(p: str, TIMEOUT: str):
    item = re.search(f"(?<={TIMEOUT})[0-9.]+(?=s.log)", p)
    return float(item.group(0)) if item else None

def extract_min(p: str, TIMEOUT: str):
    item = re.search(f"(?<={TIMEOUT})[0-9.]+(?=m.log)", p)
    return float(item.group(0)) * 60 if item else None


def extract_common(p: str, TIMEOUT: str):
    item = re.search(f".+(?={TIMEOUT}[0-9.]+(s|h|m).log)", p)
    return item.group(0) if item else None


def main(logs: str, big_logs: str, timeout: str):
    to_copy: dict[str, tuple[str, float]] = {}

    for root, _dirs, files in os.walk(logs):
        for file in files:
            common = extract_common(file, timeout)
            secs = extract_hour(file, timeout) or extract_sec(file, timeout) or extract_min(file, timeout)

            if not common or not secs:
                print("ignore", file)
                continue

            prev = to_copy.get(common)
            fullpath = path.join(root, file)
            print("walk", fullpath)

            # ugly
            if prev:
                (_path, prev_secs) = prev

                if prev_secs < secs:
                    to_copy[common] = (fullpath, secs)
            else:
                to_copy[common] = (fullpath, secs)

    for fullpath, _ in to_copy.values():
        print("copy", fullpath)
        _ran = shutil.copy(fullpath, big_logs)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("read_from",
                        type=str,
                        help="path to directory containing log files",
                        )
    parser.add_argument("copy_to",
                        type=str,
                        help="path to directory to log files to",
                        )
    parser.add_argument("timeout",
                        type=str,
                        help="file name format is ...{timeout}<float>[hms].log",
                        )

    args = parser.parse_args()

    main(args.read_from, args.copy_to, args.timeout)
