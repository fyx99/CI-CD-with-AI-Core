from ai_core_sdk.ai_core_v2_client import AICoreV2Client
from ai_api_client_sdk.models.artifact import Artifact
from ai_api_client_sdk.models.parameter_binding import ParameterBinding
from ai_api_client_sdk.models.input_artifact_binding import InputArtifactBinding
from ai_api_client_sdk.models.target_status import TargetStatus
      

from datetime import datetime

import os
import json
import time

AICORE_AUTH_URL = os.environ["AICORE_AUTH_URL"]
AICORE_BASE_URL = os.environ["AICORE_BASE_URL"]
AICORE_CLIENT_ID = os.environ["AICORE_CLIENT_ID"]
AICORE_CLIENT_SECRET = os.environ["AICORE_CLIENT_SECRET"]
AICORE_RESOURCE_GROUP = os.environ["AICORE_RESOURCE_GROUP"]

if __name__ == "__main__":
    
    #deploy()
    
    ai_api_v2_client = AICoreV2Client(
        base_url=AICORE_BASE_URL, 
        auth_url=AICORE_AUTH_URL + "/oauth/token", 
        client_id=AICORE_CLIENT_ID,
        client_secret=AICORE_CLIENT_SECRET, 
        resource_group=AICORE_RESOURCE_GROUP
    )
    res = ai_api_v2_client.rest_client.post("/inference/deployments/dda52040be151157/v2/hello/")
    print(res.__dict__)