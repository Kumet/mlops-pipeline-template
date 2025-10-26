from pathlib import Path

import pandas as pd


def main(raw_path: str, features_path: str):
    df = pd.read_csv(raw_path)
    Path(features_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(features_path)


if __name__ == "__main__":
    import sys

    main(sys.argv[1], sys.argv[2])
