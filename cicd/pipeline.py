from ai_core_sdk.ai_core_v2_client import AICoreV2Client
from ai_api_client_sdk.models.artifact import Artifact
from ai_api_client_sdk.models.parameter_binding import ParameterBinding
from ai_api_client_sdk.models.input_artifact_binding import InputArtifactBinding
from ai_api_client_sdk.models.target_status import TargetStatus



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

def display_logs(logs, last_date, filter_ai_core=True):
    for log in logs:
        if last_date and log.timestamp < last_date:
            continue
        if filter_ai_core and log.msg.startswith("time="):
            continue
        print(f"{log.timestamp.isoformat()} {log.msg}")
    last_date = logs[0].timestamp if logs else None
    return last_date
        
        
def create_artifact(ai_api_v2_client: AICoreV2Client, artifact):
    available_artifacts = ai_api_v2_client.artifact.query()
    for aartifact in available_artifacts.resources:
        if aartifact.name == artifact["name"] and aartifact.kind == Artifact.Kind(artifact["kind"]) and aartifact.url == artifact["url"] and aartifact.scenario_id == artifact["scenario_id"]:
            # duplicate check to not fill up tenant
            return aartifact.id
    artifact_response = ai_api_v2_client.artifact.create(artifact["name"], Artifact.Kind(artifact["kind"]), artifact["url"], artifact["scenario_id"])
    return artifact_response.id


def find_artifact_by_key(key, artifacts):
    for artifact in artifacts:
        if artifact["key"] == key:
            return artifact


def configurations_to_string(config):
    dconfig = {}
    dconfig["name"] = config["name"]
    dconfig["scenario_id"] = config["scenario_id"]
    dconfig["executable_id"] = config["executable_id"]
    dconfig["parameter_bindings"] = [p.to_dict() for p in config["parameter_bindings"]]
    dconfig["input_artifact_bindings"] = [p.to_dict() for p in config["input_artifact_bindings"]]
    return json.dumps(dconfig, sort_keys=True)
    

def executable_status(ai_api_v2_client: AICoreV2Client, executable):
    if executable["type"] == "execution":
        execution_object = ai_api_v2_client.execution.get(executable["id"])
        status = execution_object.status.value
        status_details = execution_object.status_details
        status_message = execution_object.status_message
        logs = ai_api_v2_client.execution.query_logs(executable["id"]).data.result
    elif executable["type"] == "deployment":
        execution_object = ai_api_v2_client.deployment.get(executable["id"])
        status = execution_object.status.value
        status_details = execution_object.status_details
        status_message = execution_object.status_message
        logs = ai_api_v2_client.deployment.query_logs(executable["id"]).data.result
    return status, status_details, status_message, logs


def wait_on_executable_logs(ai_api_v2_client: AICoreV2Client, executable):
    
    print("#"*50)
    
    last_date = None
    for _ in range(60):
        try:
            status, status_details, status_message, logs = executable_status(ai_api_v2_client, executable)
        except Exception as e:
            time.sleep(15)
            print("POLLING LOGS", executable["type"], executable["configuration"]["executable_id"], executable["id"])
            continue
        if len(logs) < 1:
            print("POLLING LOGS", executable["type"], executable["configuration"]["executable_id"], executable["id"])
        last_date = display_logs(logs, last_date)
        
        if status == executable["wait_for_status"] or status == "DEAD":
            break
        if len(logs) < 1:
            time.sleep(13)  # sleep longer if not ready
        time.sleep(2)


def create_configuration(ai_api_v2_client: AICoreV2Client, configuration, artifacts):
    
    parameter_bindings = [ParameterBinding(e["key"], e["value"]) for e in configuration["parameter_bindings"]]
    input_artifact_bindings = [InputArtifactBinding(e["key"], find_artifact_by_key(e["key"], artifacts)["id"]) for e in configuration["input_artifact_bindings"]]

    available_configurations = ai_api_v2_client.configuration.query()

    config = { "name": configuration["name"], "scenario_id": configuration["scenario_id"], "executable_id": configuration["executable_id"], "parameter_bindings": parameter_bindings, "input_artifact_bindings": input_artifact_bindings}
    
    sconfig = configurations_to_string(config)
    
    for aconfiguration in available_configurations.resources:
        if configurations_to_string(aconfiguration.__dict__) == sconfig: # same configs
            return aconfiguration.id

    config_resp = ai_api_v2_client.configuration.create(**config)
    assert config_resp.message == 'Configuration created'
    return config_resp.id


def create_execution(ai_api_v2_client: AICoreV2Client, execution, artifacts):
    
    config_id = create_configuration(ai_api_v2_client, execution["configuration"], artifacts)

    execution_resp = ai_api_v2_client.execution.create(config_id)
    
    print("CREATED EXECUTION", execution_resp.id)
    
    return execution_resp.id


def create_deployment(ai_api_v2_client: AICoreV2Client, deployment, artifacts):
    
    config_id = create_configuration(ai_api_v2_client, deployment["configuration"], artifacts)

    deployment_resp = ai_api_v2_client.deployment.create(config_id)
    
    print("CREATED DEPLOYMENT", deployment_resp.id)
    
    return deployment_resp.id

def clean_up_tenant(ai_api_v2_client):
    old_deployments = ai_api_v2_client.deployment.query()
    for deployment in old_deployments.resources:
        try:
            ai_api_v2_client.deployment.modify(deployment.id, TargetStatus.STOPPED)
        except:
            pass
        try:
            ai_api_v2_client.deployment.delete(deployment.id)
        except:
            pass
        print("DELETED DEPLOYMENT", deployment.id)
        
    old_executions = ai_api_v2_client.execution.query()
    for execution in old_executions.resources:
        try:
            ai_api_v2_client.execution.delete(execution.id)
        except:
            pass
        print("DELETED EXECUTION", execution.id)
        
    

def deploy(cleanup=True, wait_for_logs=True):
    
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

    if cleanup:
        clean_up_tenant(ai_api_v2_client)


    for artifact in artifacts:
        artifact["id"] = create_artifact(ai_api_v2_client, artifact)

    for execution in executions:
        execution["id"] = create_execution(ai_api_v2_client, execution, artifacts)
        execution["type"] = "execution"

    for deployment in deployments:
        deployment["id"] = create_deployment(ai_api_v2_client, deployment, artifacts)
        deployment["type"] = "deployment"


        
    if wait_for_logs:
        for deployment in deployments:
            wait_on_executable_logs(ai_api_v2_client, deployment)

        for execution in executions:
            wait_on_executable_logs(ai_api_v2_client, execution)

            
            
if __name__ == "__main__":
    
    deploy()