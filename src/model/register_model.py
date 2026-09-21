import json
import logging
import os

import dagshub
import mlflow

# ---- DagsHub / MLflow auth: token in CI, browser login locally ----
dagshub_token = os.getenv("CAPSTONE_TEST")
repo_owner = "prajwal-sketch"
repo_name = "capstone-project-"

if os.getenv("GITHUB_ACTIONS") == "true" and not dagshub_token:
    raise EnvironmentError("CAPSTONE_TEST secret is not reaching this step")

if dagshub_token:
    os.environ["MLFLOW_TRACKING_USERNAME"] = repo_owner
    os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
    mlflow.set_tracking_uri(f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow")
else:
    dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
    mlflow.set_tracking_uri(f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow")


def load_model_info(file_path: str) -> dict:
    with open(file_path, "r") as file:
        return json.load(file)


def register_model(model_name: str, model_info: dict):
    model_uri = model_info["model_uri"]  # models:/m-... saved by model_evaluation.py
    model_version = mlflow.register_model(model_uri, model_name)
    logging.info("Registered %s version %s", model_name, model_version.version)

    # Stages are deprecated and may not be supported on DagsHub, so don't fail on this
    try:
        client = mlflow.tracking.MlflowClient()
        client.transition_model_version_stage(
            name=model_name, version=model_version.version, stage="Staging"
        )
    except Exception as e:
        logging.warning("Stage transition skipped: %s", e)

    return model_version


def main():
    try:
        model_info = load_model_info("reports/experiment_info.json")
        register_model("my_model", model_info)
    except Exception as e:
        logging.error("Failed to complete the model registration process: %s", e)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()