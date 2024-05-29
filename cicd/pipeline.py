import os
import json
import time
import logging
from datetime import timedelta
from typing import List

from ai_core_sdk.ai_core_v2_client import AICoreV2Client
from ai_api_client_sdk.models.artifact import Artifact
from ai_api_client_sdk.models.parameter_binding import ParameterBinding
from ai_api_client_sdk.models.input_artifact_binding import InputArtifactBinding
from ai_api_client_sdk.models.target_status import TargetStatus
from ai_api_client_sdk.models.log_response import LogResultItem

from destinations import update_deployment_destination

logging.basicConfig(level=logging.INFO, format='%(message)s')


AICORE_AUTH_URL = os.environ["AICORE_AUTH_URL"]
AICORE_BASE_URL = os.environ["AICORE_BASE_URL"]
AICORE_CLIENT_ID = os.environ["AICORE_CLIENT_ID"]
AICORE_CLIENT_SECRET = os.environ["AICORE_CLIENT_SECRET"]
AICORE_RESOURCE_GROUP = os.environ["AICORE_RESOURCE_GROUP"]


def load_deployment_configuration():
    """load ai core deployment configuration file from json, file needs to be in the cicd folder"""
    with open("cicd/config.json") as json_file:
        configuration = json.load(json_file)
    artifacts = configuration["artifacts"]
    executions = configuration["executions"]
    deployments = configuration["deployments"]
    
    return artifacts, executions, deployments

def display_logs(logs: List[LogResultItem], filter_ai_core=True):
    """print logs and filter ai core platform logs starting with time="""
    for log in logs:
        if filter_ai_core and log.msg.startswith("time="):
            continue
        logging.info(f"{log.timestamp.isoformat()} {log.msg}")

        
def create_artifact(ai_api_v2_client: AICoreV2Client, artifact_b: Artifact):
    """create or find duplicate artifact from json configuration"""    
    available_artifacts = ai_api_v2_client.artifact.query()
    for artifact_a in available_artifacts.resources:
        if artifact_a.name == artifact_b["name"] and artifact_a.kind == Artifact.Kind(artifact_b["kind"]) and artifact_a.url == artifact_b["url"] and artifact_a.scenario_id == artifact_b["scenario_id"]:
            # duplicate check to not fill up tenant
            return artifact_a.id
    artifact_response = ai_api_v2_client.artifact.create(artifact_b["name"], Artifact.Kind(artifact_b["kind"]), artifact_b["url"], artifact_b["scenario_id"])
    return artifact_response.id


def configuration_to_string(configuration_object):
    """helper to dump config to json-string to compare nested values"""
    configuration_dict = {}
    configuration_dict["name"] = configuration_object["name"]
    configuration_dict["scenario_id"] = configuration_object["scenario_id"]
    configuration_dict["executable_id"] = configuration_object["executable_id"]
    configuration_dict["parameter_bindings"] = [p.to_dict() for p in configuration_object["parameter_bindings"]]
    configuration_dict["input_artifact_bindings"] = [p.to_dict() for p in configuration_object["input_artifact_bindings"]]
    return json.dumps(configuration_dict, sort_keys=True)
    

def create_configuration(ai_api_v2_client: AICoreV2Client, configuration, artifacts):
    """create or find duplicate configuration"""
    
    parameter_bindings = [ParameterBinding(e["key"], e["value"]) for e in configuration["parameter_bindings"]]
    input_artifact_bindings = [InputArtifactBinding(e["key"], filter(lambda d: d["key"] == e["key"], artifacts)["id"]) for e in configuration["input_artifact_bindings"]]

    available_configurations = ai_api_v2_client.configuration.query()

    config = { "name": configuration["name"], "scenario_id": configuration["scenario_id"], "executable_id": configuration["executable_id"], "parameter_bindings": parameter_bindings, "input_artifact_bindings": input_artifact_bindings}
    
    sconfig = configuration_to_string(config)
    
    for aconfiguration in available_configurations.resources:
        if configuration_to_string(aconfiguration.__dict__) == sconfig: # same configs
            return aconfiguration.id

    config_resp = ai_api_v2_client.configuration.create(**config)

    return config_resp.id


def create_execution(ai_api_v2_client: AICoreV2Client, execution, artifacts):
    """create execution"""
    
    config_id = create_configuration(ai_api_v2_client, execution["configuration"], artifacts)

    execution_response = ai_api_v2_client.execution.create(config_id)
    
    logging.info(f"CREATED EXECUTION {execution_response.id}")
    
    return execution_response.id


def create_deployment(ai_api_v2_client: AICoreV2Client, deployment, artifacts):
    """create deployment"""
    
    config_id = create_configuration(ai_api_v2_client, deployment["configuration"], artifacts)

    deployment_response = ai_api_v2_client.deployment.create(config_id)
    
    logging.info(f"CREATED DEPLOYMENT {deployment_response.id}")
    
    return deployment_response.id


def executable_status(ai_api_v2_client: AICoreV2Client, executable, last_time):
    """get executable status"""
    try:
        if executable["type"] == "EXECUTION":
            executable_object = ai_api_v2_client.execution.get(executable["id"])
        else:
            executable_object = ai_api_v2_client.deployment.get(executable["id"])    
    except:
        return "UNKNOWN", [], last_time
    
    status = executable_object.status.value
    
    if not last_time:
        start_time = executable_object.submission_time
    else:
        start_time = last_time + timedelta(seconds=1)
    
    try:
        if executable["type"] == "EXECUTION":
            logs = ai_api_v2_client.execution.query_logs(executable["id"], start=start_time).data.result
        else:
            logs = ai_api_v2_client.deployment.query_logs(executable["id"], start=start_time).data.result
    except:
        return "UNKNOWN", [], last_time
    
    new_last_time = logs[-1].timestamp if logs else last_time
    
    return status, logs, new_last_time


def wait_on_executable_logs(ai_api_v2_client: AICoreV2Client, executable):
    """polling logs and displaying them to console until status is reached"""
    logging.info("#"*55)
    logging.info(f"""POLLING LOGS {executable["type"]} {executable["configuration"]["executable_id"]} {executable["id"]}""")
    
    last_time = None
    logs_started = False
    reached_status = False
    for _ in range(60):
        
        status, logs, last_time = executable_status(ai_api_v2_client, executable, last_time)

        if not logs_started and len(logs) < 1:
            logging.info("POLLING LOGS")
        else:
            logs_started = True
        
        display_logs(logs)
        
        if status == executable["wait_for_status"]:
            reached_status = True
            break
        if status == "DEAD":
            break
        
        if logs_started:
            time.sleep(2)  
        else:
            time.sleep(15) # sleep longer if not ready
    return reached_status


def clean_up_tenant(ai_api_v2_client: AICoreV2Client):
    """gracefully clean up tenant from old instances, by stopping/deleting"""
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
        logging.info(f"DELETED DEPLOYMENT {deployment.id}")
        
    old_executions = ai_api_v2_client.execution.query()
    for execution in old_executions.resources:
        try:
            ai_api_v2_client.execution.delete(execution.id)
        except:
            pass
        logging.info(f"DELETED EXECUTION {execution.id}")
        

def deploy(cleanup=True, wait_for_status=True, update_destination=True):
    """manage deployment of artifacts, executions and deployments from config file"""
    
    logging.info(f"START DEPLOYING TO RESOURCE GROUP {AICORE_RESOURCE_GROUP}")
    
    artifacts, executions, deployments = load_deployment_configuration()

    ai_api_v2_client = AICoreV2Client(
        base_url=AICORE_BASE_URL, 
        auth_url=AICORE_AUTH_URL + "/oauth/token", 
        client_id=AICORE_CLIENT_ID,
        client_secret=AICORE_CLIENT_SECRET, 
        resource_group=AICORE_RESOURCE_GROUP
    )
    
    ai_api_v2_client.resource_groups.create(resource_group_id=AICORE_RESOURCE_GROUP)
    logging.info(f"RESOURCE GROUP CREATED {AICORE_RESOURCE_GROUP}")
    
    ai_api_v2_client.applications.refresh("felix-cicd")
    
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
        execution["type"] = "EXECUTION"

    for deployment in deployments:
        deployment["id"] = create_deployment(ai_api_v2_client, deployment, artifacts)
        deployment["type"] = "DEPLOYMENT"

    if wait_for_status:
        for execution in executions:
            wait_on_executable_logs(ai_api_v2_client, execution)
        for deployment in deployments:
            deployment["reached_status"] = wait_on_executable_logs(ai_api_v2_client, deployment)
            
    if update_destination:
        for deployment in deployments:
            if deployment["wait_for_status"] and deployment["reached_status"]:
                update_deployment_destination(deployment["destination_name"], deployment["id"])

            
            
if __name__ == "__main__":
    
    deploy()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # ai_api_v2_client = AICoreV2Client(
    #     base_url=AICORE_BASE_URL, 
    #     auth_url=AICORE_AUTH_URL + "/oauth/token", 
    #     client_id=AICORE_CLIENT_ID,
    #     client_secret=AICORE_CLIENT_SECRET, 
    #     resource_group=AICORE_RESOURCE_GROUP
    # )
    # executable = {
    #     "id": "dda52040be151157",
    #     "configuration": {
    #         "executable_id": "test"
    #     },
    #     "type": "DEPLOYMENT",
    #     "wait_for_status": "COMPLETED"
    # }
    
    # wait_on_executable_logs(ai_api_v2_client, executable)