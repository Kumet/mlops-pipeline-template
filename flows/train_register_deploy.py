from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import mlflow
from mlflow.tracking import MlflowClient
from omegaconf import OmegaConf
from prefect import flow, get_run_logger, task

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "configs"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"


def _load_merged_config() -> Any:
    cfg_base = OmegaConf.load(CONFIG_DIR / "config.yaml")
    cfg_data = OmegaConf.load(CONFIG_DIR / "data.yaml")
    cfg_train = OmegaConf.load(CONFIG_DIR / "train.yaml")
    cfg_eval = OmegaConf.load(CONFIG_DIR / "eval.yaml")
    return OmegaConf.merge(cfg_base, cfg_data, cfg_train, cfg_eval)


def _run_command(command: list[str]) -> None:
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)


@task
def run_dvc_pipeline(force: bool) -> None:
    cmd = ["uv", "run", "dvc", "repro"]
    if force:
        cmd.append("--force")
    _run_command(cmd)


@task
def load_metrics(metrics_path: Path = METRICS_PATH) -> dict[str, float]:
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Metrics file not found at {metrics_path}. Did the evaluation stage run?"
        )
    raw = json.loads(metrics_path.read_text())
    return {key: float(value) for key, value in raw.items()}


@task
def evaluate_against_thresholds(
    metrics: dict[str, float], thresholds: dict[str, float | None]
) -> bool:
    logger = get_run_logger()
    all_pass = True
    for metric, threshold in thresholds.items():
        if threshold is None:
            continue
        observed = metrics.get(metric)
        if observed is None:
            logger.warning("Metric '%s' missing in evaluation output", metric)
            all_pass = False
            continue
        if observed < threshold:
            logger.warning("Metric '%s' below threshold: %.4f < %.4f", metric, observed, threshold)
            all_pass = False
        else:
            logger.info("Metric '%s' meets threshold: %.4f ≥ %.4f", metric, observed, threshold)
    return all_pass


@task
def register_latest_model(mlflow_uri: str, model_name: str) -> tuple[str, str]:
    logger = get_run_logger()
    mlflow.set_tracking_uri(mlflow_uri)
    client = MlflowClient()
    experiment = client.get_experiment_by_name("training")
    if experiment is None:
        raise RuntimeError("MLflow experiment 'training' not found.")
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["attributes.start_time DESC"],
        max_results=1,
    )
    if not runs:
        raise RuntimeError("No MLflow runs found for experiment 'training'.")
    run = runs[0]
    source = f"runs:/{run.info.run_id}/model.joblib"
    model_version = mlflow.register_model(source, model_name)
    logger.info(
        "Registered MLflow model '%s' version %s from run %s",
        model_name,
        model_version.version,
        run.info.run_id,
    )
    return run.info.run_id, model_version.version


@task
def build_serving_image(flavor: str, image_name: str) -> None:
    logger = get_run_logger()
    cmd = [
        "docker",
        "build",
        "-f",
        "src/serving/Dockerfile",
        "--build-arg",
        f"FLAVOR={flavor}",
        "-t",
        image_name,
        ".",
    ]
    logger.info("Building serving image '%s' with flavor '%s'", image_name, flavor)
    _run_command(cmd)


@flow(name="train-register-deploy")
def train_register_deploy(
    force_repro: bool = False,
    build_image: bool = False,
    image_name: str = "mlops-serving:auto",
    flavor: str = "cpu",
    model_name: str | None = None,
) -> dict[str, Any]:
    """
    Run the training pipeline via DVC, evaluate the metrics, register the model to MLflow,
    and optionally build the serving Docker image.
    """
    logger = get_run_logger()
    cfg = _load_merged_config()
    run_dvc_pipeline(force_repro)
    metrics = load_metrics()
    thresholds_cfg = OmegaConf.to_container(cfg.eval.thresholds or {}, resolve=True)
    thresholds = {k: float(v) if v is not None else None for k, v in thresholds_cfg.items()}
    meets_thresholds = evaluate_against_thresholds(metrics, thresholds)

    if not meets_thresholds:
        logger.warning("Threshold checks failed. Skipping model registration and deployment.")
        return {"status": "skipped", "metrics": metrics}

    resolved_model_name = model_name or cfg.train.get("model_name", "mlops-model")
    run_id, version = register_latest_model(cfg.mlflow.tracking_uri, resolved_model_name)

    if build_image:
        build_serving_image(flavor=flavor, image_name=image_name)
        status = "deployed"
    else:
        status = "registered"

    return {
        "status": status,
        "model_name": resolved_model_name,
        "model_version": version,
        "run_id": run_id,
        "metrics": metrics,
    }


if __name__ == "__main__":
    # Allow running as a script: `uv run python flows/train_register_deploy.py`
    train_register_deploy()
