from pathlib import Path

from sklearn.datasets import load_iris


def main(raw_path: str):
    Path(raw_path).parent.mkdir(parents=True, exist_ok=True)
    iris = load_iris(as_frame=True)
    df = iris.frame
    df.columns = [*iris.feature_names, "target"]
    df.to_csv(raw_path, index=False)


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
