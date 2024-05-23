from ai_core_sdk.ai_core_v2_client import AICoreV2Client
from ai_api_client_sdk.models.artifact import Artifact
from ai_api_client_sdk.models.parameter_binding import ParameterBinding
from ai_api_client_sdk.models.input_artifact_binding import InputArtifactBinding


import os
import json
import time

AICORE_AUTH_URL = os.environ["AICORE_AUTH_URL"]
AICORE_BASE_URL = os.environ["AICORE_BASE_URL"]
AICORE_CLIENT_ID = os.environ["AICORE_CLIENT_ID"]
AICORE_CLIENT_SECRET = os.environ["AICORE_CLIENT_SECRET"]
AICORE_RESOURCE_GROUP = os.environ["AICORE_RESOURCE_GROUP"]



def load_deployment_configuration():
    with open("cicd/config.json") as json_file:
        configuration = json.load(json_file)
    artifacts = configuration["artifacts"]
    executions = configuration["executions"]
    deployments = configuration["deployments"]
    
    return artifacts, executions, deployments

def display_logs(logs, filter_ai_core=True):
    for log in logs:
        if filter_ai_core and log.msg.startswith("time="):
            continue
        print(f"{log.timestamp.isoformat()} {log.msg}")
        
        
def create_artifact(ai_api_v2_client: AICoreV2Client, artifact):
    
    artifact_response = ai_api_v2_client.artifact.create(artifact["name"], Artifact.Kind(artifact["kind"]), artifact["url"], artifact["scenario_id"])
    return artifact_response.id


def find_artifact_by_key(key, artifacts):
    for artifact in artifacts:
        if artifact["key"] == key:
            return artifact


def create_execution(ai_api_v2_client: AICoreV2Client, execution, artifacts):
    
    parameter_bindings = [ParameterBinding(e["key"], e["value"]) for e in execution["configuration"]["parameter_bindings"]]
    input_artifact_bindings = [InputArtifactBinding(e["key"], find_artifact_by_key(e["key"], artifacts)["id"]) for e in execution["configuration"]["input_artifact_bindings"]]

    config_resp = ai_api_v2_client.configuration.create(execution["configuration"]["name"], execution["configuration"]["scenario_id"], execution["configuration"]["executable_id"], parameter_bindings, input_artifact_bindings)
    
    
    assert config_resp.message == 'Configuration created'

    deployment_resp = ai_api_v2_client.execution.create(config_resp.id)

    for _ in range(60):
        execution_object = ai_api_v2_client.execution.get(deployment_resp.id)
        status = execution_object.status.value
        logs = ai_api_v2_client.execution.query_logs(deployment_resp.id).data.result
        print(status, execution_object.status_details, "N LOGS", str(len(logs)))
        display_logs(logs)
        if status == execution["wait_for_status"] or status == "DEAD":
            break
        time.sleep(15)
    
    return 1
    
        
def create_deployment(ai_api_v2_client: AICoreV2Client, deployment):
    
    
    config_resp = ai_api_v2_client.configuration.create(**deployment["configuration"])
    assert config_resp.message == 'Configuration created'

    deployment_resp = ai_api_v2_client.execution.create(config_resp.id)

    for _ in range(60):
        execution_object = ai_api_v2_client.deployment.get(deployment_resp.id)
        status = execution_object.status.value
        if status == deployment["wait_for_status"] or status == "DEAD":
            break
        logs = ai_api_v2_client.execution.query_logs(deployment_resp.id).data.result
        print(status, execution_object.status_details, "N LOGS", str(len(logs)))
        try:
            display_logs(logs)
        except:
            pass
        time.sleep(15)
    
    return 1


def deploy():
    
    artifacts, executions, deployments = load_deployment_configuration()

    ai_api_v2_client = AICoreV2Client(
        base_url=AICORE_BASE_URL, 
        auth_url=AICORE_AUTH_URL + "/oauth/token", 
        client_id=AICORE_CLIENT_ID,
        client_secret=AICORE_CLIENT_SECRET, 
        resource_group=AICORE_RESOURCE_GROUP
    )


    resource_group_create = ai_api_v2_client.resource_groups.create(resource_group_id=AICORE_RESOURCE_GROUP)
    print(f"RESOURCE GROUP CREATED {AICORE_RESOURCE_GROUP}")
    sync = ai_api_v2_client.applications.refresh("felix-cicd")
    
    for _ in range(60):
        status = ai_api_v2_client.applications.get_status("felix-cicd")
        if status.sync_status == "Synced":
            break
        time.sleep(2)
    
    # # Get executables
    # executables = ai_api_v2_client.executable.query(name)
    # for e in executables.resources:
    #     print(f"Executable {e.id} v{e.version_id} found")
    for artifact in artifacts:
        artifact["id"] = create_artifact(ai_api_v2_client, artifact)


    for execution in executions:
        create_execution(ai_api_v2_client, execution, artifacts)

    for deployment in deployments:
        create_deployment(ai_api_v2_client, deployment, artifacts)
        
    
    
if __name__ == "__main__":
    
    deploy()