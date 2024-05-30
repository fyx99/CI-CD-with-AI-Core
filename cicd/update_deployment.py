import os
import json
import logging
import time

from ai_core_sdk.ai_core_v2_client import AICoreV2Client
from ai_api_client_sdk.models.artifact import Artifact
from ai_api_client_sdk.models.parameter_binding import ParameterBinding
from ai_api_client_sdk.models.input_artifact_binding import InputArtifactBinding


logging.basicConfig(level=logging.INFO, format='%(message)s')


AICORE_AUTH_URL = os.environ["AICORE_AUTH_URL"]
AICORE_BASE_URL = os.environ["AICORE_BASE_URL"]
AICORE_CLIENT_ID = os.environ["AICORE_CLIENT_ID"]
AICORE_CLIENT_SECRET = os.environ["AICORE_CLIENT_SECRET"]
AICORE_RESOURCE_GROUP = os.environ["AICORE_RESOURCE_GROUP"]


def load_deployment_configuration():
    """load ai core deployment configuration file from json, file needs to be in the cicd folder"""
    with open("cicd/update.json") as json_file:
        configuration = json.load(json_file)
    artifacts = configuration["artifacts"]
    executions = configuration["executions"]
    deployments = configuration["deployments"]
    
    return artifacts, executions, deployments

        
def create_artifact(ai_api_v2_client: AICoreV2Client, artifact_b: Artifact):
    """create or find duplicate artifact from json configuration"""    
    available_artifacts = ai_api_v2_client.artifact.query()
    for artifact_a in available_artifacts.resources:
        if artifact_a.name == artifact_b["name"] and artifact_a.kind == Artifact.Kind(artifact_b["kind"]) and artifact_a.url == artifact_b["url"] and artifact_a.scenario_id == artifact_b["scenario_id"]:
            # duplicate check to not fill up tenant
            return artifact_a.id
    artifact_response = ai_api_v2_client.artifact.create(artifact_b["name"], Artifact.Kind(artifact_b["kind"]), artifact_b["url"], artifact_b["scenario_id"])
    return artifact_response.id


def create_configuration(ai_api_v2_client: AICoreV2Client, configuration, artifacts):
    """create or find duplicate configuration"""
    
    parameter_bindings = [ParameterBinding(e["key"], e["value"]) for e in configuration["parameter_bindings"]]
    input_artifact_bindings = [InputArtifactBinding(e["key"], next(filter(lambda d: d["key"] == e["key"], artifacts))["id"]) for e in configuration["input_artifact_bindings"]]

    config = { "name": configuration["name"], "scenario_id": configuration["scenario_id"], "executable_id": configuration["executable_id"], "parameter_bindings": parameter_bindings, "input_artifact_bindings": input_artifact_bindings}


    config_resp = ai_api_v2_client.configuration.create(**config)

    return config_resp.id


def update_deployment(ai_api_v2_client: AICoreV2Client, deployment, artifacts):
    """create deployment"""
    
    config_id = create_configuration(ai_api_v2_client, deployment["configuration"], artifacts)

    deployment_response = ai_api_v2_client.deployment.modify(deployment["id"], None, config_id)
    
    logging.info(f"UPDATED DEPLOYMENT {deployment_response.id}")
    
    return deployment_response.id


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

    for artifact in artifacts:
        artifact["id"] = create_artifact(ai_api_v2_client, artifact)

    

    for deployment in deployments:
        update_deployment(ai_api_v2_client, deployment, artifacts)

    for n in range(300):
        try:
            res = ai_api_v2_client.rest_client.post("/inference/deployments/d500245f18ff405f/v2/hello/")
            print(res)
        except:
            print("fail")
        time.sleep(1)
    a= 1
            
if __name__ == "__main__":
    
    deploy()
    