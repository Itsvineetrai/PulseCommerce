import logging
import subprocess
import sys
from pathlib import Path

from prefect import flow, task


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

logger = logging.getLogger(__name__)


@task
def run_pipeline_stage(script_name: str) -> None:
    """
    Execute one PulseCommerce pipeline script.

    Raises:
        FileNotFoundError: If the requested script does not exist.
        RuntimeError: If the script exits with a non-zero return code.
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(
            f"Pipeline script does not exist: {script_path}"
        )

    logger.info("Starting pipeline stage: %s", script_name)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        logger.info(
            "Output from %s:\n%s",
            script_name,
            result.stdout,
        )

    if result.returncode != 0:
        if result.stderr:
            logger.error(
                "Pipeline stage failed: %s\n%s",
                script_name,
                result.stderr,
            )

        raise RuntimeError(
            f"Pipeline stage failed: {script_name}"
        )

    logger.info("Completed pipeline stage: %s", script_name)


@flow(name="pulsecommerce_pipeline")
def pulsecommerce_pipeline() -> None:
    """
    Run the complete PulseCommerce analytics, experimentation,
    churn prediction, and intervention optimization pipeline.
    """
    pipeline_stages = [
        "load_warehouse.py",
        "run_analytics.py",
        "run_experiment_population.py",
        "run_experiment_analysis.py",
        "run_churn_feature_dataset.py",
        "train_final_churn_model.py",
        "score_churn_risk.py",
        "generate_intervention_candidates.py",
        "generate_intervention_economics.py",
        "generate_intervention_portfolio.py",
        "generate_intervention_roi.py",
    ]

    for script_name in pipeline_stages:
        run_pipeline_stage(script_name)


if __name__ == "__main__":
    pulsecommerce_pipeline()