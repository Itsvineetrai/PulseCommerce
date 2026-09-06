from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pulsecommerce.orchestration.pipeline_flow import (
    PROJECT_ROOT,
    SCRIPTS_DIR,
    pulsecommerce_pipeline,
    run_pipeline_stage,
)


EXPECTED_PIPELINE_STAGES = [
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


def test_project_root_exists() -> None:
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()


def test_scripts_directory_exists() -> None:
    assert SCRIPTS_DIR.exists()
    assert SCRIPTS_DIR.is_dir()


def test_all_pipeline_scripts_exist() -> None:
    for script_name in EXPECTED_PIPELINE_STAGES:
        script_path = SCRIPTS_DIR / script_name

        assert script_path.exists(), (
            f"Expected pipeline script does not exist: {script_name}"
        )


@patch("pulsecommerce.orchestration.pipeline_flow.subprocess.run")
def test_pipeline_stage_executes_python_script(
    mock_subprocess_run: MagicMock,
) -> None:
    mock_subprocess_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="Stage completed successfully.",
        stderr="",
    )

    run_pipeline_stage.fn("load_warehouse.py")

    expected_script_path = SCRIPTS_DIR / "load_warehouse.py"

    mock_subprocess_run.assert_called_once_with(
        [
            sys.executable,
            str(expected_script_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_missing_pipeline_script_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        run_pipeline_stage.fn("script_that_does_not_exist.py")


@patch("pulsecommerce.orchestration.pipeline_flow.subprocess.run")
def test_failed_pipeline_stage_raises_runtime_error(
    mock_subprocess_run: MagicMock,
) -> None:
    mock_subprocess_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="",
        stderr="Stage failed.",
    )

    with pytest.raises(
        RuntimeError,
        match="Pipeline stage failed: load_warehouse.py",
    ):
        run_pipeline_stage.fn("load_warehouse.py")


@patch(
    "pulsecommerce.orchestration.pipeline_flow.run_pipeline_stage"
)
def test_pipeline_execution_order(
    mock_run_pipeline_stage: MagicMock,
) -> None:
    mock_run_pipeline_stage.return_value = None

    pulsecommerce_pipeline.fn()

    executed_stages = [
        call.args[0]
        for call in mock_run_pipeline_stage.call_args_list
    ]

    assert executed_stages == EXPECTED_PIPELINE_STAGES


@patch(
    "pulsecommerce.orchestration.pipeline_flow.run_pipeline_stage"
)
def test_pipeline_contains_expected_number_of_stages(
    mock_run_pipeline_stage: MagicMock,
) -> None:
    mock_run_pipeline_stage.return_value = None

    pulsecommerce_pipeline.fn()

    assert mock_run_pipeline_stage.call_count == 11