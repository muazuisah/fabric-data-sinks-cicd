"""Deploy the Fabric items in ./workspace to a target workspace using fabric-cicd."""

import os
import sys
from pathlib import Path

from azure.identity import ClientSecretCredential
from fabric_cicd import (
    FabricWorkspace,
    append_feature_flag,
    change_log_level,
    publish_all_items,
    unpublish_all_orphan_items,
)

REPO_DIR = Path(__file__).resolve().parent.parent / "workspace"
ITEM_TYPES = ["Lakehouse", "Warehouse", "DataPipeline"]


def require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    environment = require("ENVIRONMENT")
    require("ORACLE_CONNECTION_ID")  # consumed by parameter.yml via $ENV:

    credential = ClientSecretCredential(
        tenant_id=require("AZURE_TENANT_ID"),
        client_id=require("AZURE_CLIENT_ID"),
        client_secret=require("AZURE_CLIENT_SECRET"),
    )

    append_feature_flag("enable_environment_variable_replacement")
    if os.environ.get("ACTIONS_STEP_DEBUG") == "true":
        change_log_level("DEBUG")

    workspace = FabricWorkspace(
        workspace_id=require("FABRIC_WORKSPACE_ID"),
        environment=environment,
        repository_directory=str(REPO_DIR),
        item_type_in_scope=ITEM_TYPES,
        token_credential=credential,
    )

    publish_all_items(workspace)
    # Removes pipelines no longer in git. Lakehouse/Warehouse are never deleted
    # unless their unpublish feature flags are explicitly enabled (protects data).
    unpublish_all_orphan_items(workspace)


if __name__ == "__main__":
    main()
