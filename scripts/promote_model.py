import os
import mlflow
import dagshub
from mlflow.tracking import MlflowClient

repo_owner = "prajwal-sketch"
repo_name = "capstone-project-"
model_name = "my_model"

dagshub_token = os.getenv("CAPSTONE_TEST")
if os.getenv("GITHUB_ACTIONS") == "true" and not dagshub_token:
    raise EnvironmentError("CAPSTONE_TEST secret is not reaching this step")

if dagshub_token:
    os.environ["MLFLOW_TRACKING_USERNAME"] = repo_owner
    os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
    mlflow.set_tracking_uri(f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow")
else:
    dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
    mlflow.set_tracking_uri(f"https://dagshub.com/{repo_owner}/{repo_name}.mlflow")


def promote_model():
    client = MlflowClient()

    versions = client.search_model_versions(f"name='{model_name}'")
    if not versions:
        raise RuntimeError(f"No versions found for '{model_name}'")

    latest = max(versions, key=lambda v: int(v.version))
    print(f"Promoting {model_name} version {latest.version} to Production")

    # Archive whatever is currently in Production
    for v in versions:
        if v.current_stage == "Production" and v.version != latest.version:
            client.transition_model_version_stage(model_name, v.version, "Archived")

    client.transition_model_version_stage(model_name, latest.version, "Production")


if __name__ == "__main__":
    promote_model()