from ai_api_client_sdk.ai_api_v2_client import AIAPIV2Client
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
    executions = configuration["executions"]
    deployments = configuration["deployments"]
    
    return executions, deployments

def display_logs(logs, filter_ai_core=True):
    for log in logs:
        if filter_ai_core and log.msg.startswith("time="):
            continue
        print(f"{log.timestamp.isoformat()} {log.msg}")


def create_execution(ai_api_v2_client: AIAPIV2Client, execution):
    

    config_resp = ai_api_v2_client.configuration.create(**execution["configuration"])
    assert config_resp.message == 'Configuration created'

    deployment_resp = ai_api_v2_client.execution.create(config_resp.id)

    for _ in range(60):
        execution_object = ai_api_v2_client.execution.get(deployment_resp.id)
        status = execution_object.status.value
        if status == execution["wait_for_status"] or status == "DEAD":
            break
        logs = ai_api_v2_client.execution.query_logs(deployment_resp.id).data.result
        print(status, execution_object.status_details, "N LOGS", str(len(logs)))
        display_logs(logs)
        time.sleep(15)
    
    return 1
    
        
def create_deployment(ai_api_v2_client: AIAPIV2Client, deployment):
    
    
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
    
    executions, deployments = load_deployment_configuration()

    ai_api_v2_client = AIAPIV2Client(
        base_url=AICORE_BASE_URL + "/lm", 
        auth_url=AICORE_AUTH_URL + "/oauth/token", 
        client_id=AICORE_CLIENT_ID,
        client_secret=AICORE_CLIENT_SECRET, 
        resource_group=AICORE_RESOURCE_GROUP
    )


    resource_group_create = ai_api_v2_client.resource_groups.create(resource_group_id=AICORE_RESOURCE_GROUP)
    print(f"RESOURCE GROUP CREATED {AICORE_RESOURCE_GROUP}")
    

    for execution in executions:
        create_execution(ai_api_v2_client, execution)

    for deployment in deployments:
        create_deployment(ai_api_v2_client, deployment)
        
    
    
if __name__ == "__main__":
    
    deploy()