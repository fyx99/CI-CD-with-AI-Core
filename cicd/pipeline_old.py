from ai_api_client_sdk.ai_api_v2_client import AIAPIV2Client
import os

    
AICORE_AUTH_URL = os.environ["AICORE_AUTH_URL"]
AICORE_BASE_URL = os.environ["AICORE_BASE_URL"]
AICORE_CLIENT_ID = os.environ["AICORE_CLIENT_ID"]
AICORE_CLIENT_SECRET = os.environ["AICORE_CLIENT_SECRET"]
AICORE_RESOURCE_GROUP = os.environ["AICORE_RESOURCE_GROUP"]

SCENARIO_ID = "transformers"
SERVING_EXECUTABLE = "transformers"


ai_api_v2_client = AIAPIV2Client(
    base_url=AICORE_BASE_URL + "/lm", 
    auth_url=AICORE_AUTH_URL + "/oauth/token", 
    client_id=AICORE_CLIENT_ID,
    client_secret=AICORE_CLIENT_SECRET, 
    resource_group=AICORE_RESOURCE_GROUP
)


resource_group_create = ai_api_v2_client.resource_groups.create(resource_group_id=AICORE_RESOURCE_GROUP)
print(f"RESOURCE GROUP CREATED {AICORE_RESOURCE_GROUP}")



serving_configuration = {
    "name": "transformers config",
    "scenario_id": "transformers",
    "executable_id": "transformers",
    "parameter_bindings": [ ],
    "input_artifact_bindings": [ ]
}

serving_config_resp = ai_api_v2_client.configuration.create(**serving_configuration)
assert serving_config_resp.message == 'Configuration created'



deployment_resp = ai_api_v2_client.deployment.create(serving_config_resp.id)
deployment_resp.id


deployment = ai_api_v2_client.deployment.get(deployment_resp.id)
deployment.status_details   # check status