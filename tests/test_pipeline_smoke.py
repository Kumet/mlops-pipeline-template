from pathlib import Path

from omegaconf import OmegaConf


def test_hydra_config_loads():
    cfg_path = Path("configs") / "config.yaml"
    assert cfg_path.exists(), "configs/config.yaml is missing"
    cfg = OmegaConf.load(cfg_path)
    assert cfg.mlflow.tracking_uri, "mlflow.tracking_uri must be set"
