# CI-CD-with-AI-Core

This repository shows an example of how to use CI/CD with AI Core. This repo is used in the blog post [CI/CD with SAP AI Core](https://community.sap.com/t5/technology-blogs-by-sap/ci-cd-with-sap-ai-core/ba-p/13708965).

## How To Use

Reference of the config.json schema:

```json
{   
    "clean_up": true,                                       # true or false stop/delete old executables
    "artifacts": [
        {
            "key": "example-dataset",                       # key used to reference to input artifact binding
            "name": "Example Dataset",                      # mandatory: standard field
            "kind": "dataset",                              # mandatory: standard field
            "url": "ai://default/cicd/example.txt",         # mandatory: standard field
            "scenario_id": "cicdexample"                    # mandatory: standard field
        }
    ],
    "executions": [
        {
            "configuration": {
                "name": "Configuration Training",           # mandatory: standard field
                "scenario_id": "cicdexample",               # mandatory: standard field
                "executable_id": "cicdexample",             # mandatory: standard field
                "parameter_bindings": [                     # mandatory: list of parameter bindings matching the input parameters in the template
                    {
                        "key": "envexample",
                        "value": "test1"
                    } 
                ],
                "input_artifact_bindings": [                # mandatory: list of artifact bindings with key field, referencing above artifact - keys
                    {
                        "key": "example-dataset"
                    }
                ]
            },
            "wait_for_status": "COMPLETED"                  # optional: status to wait on, if not there, only triggers
        }
    ],
    "deployments": [
        {
            "existing_deployment_id": "de43dcb158de6825",   # optional - specify if deployment should not be re-created but updated
            "configuration": {
                "name": "Configuration Serving",            # mandatory: standard field
                "scenario_id": "cicdexample",               # mandatory: standard field
                "executable_id": "cicdexample2",            # mandatory: standard field
                "parameter_bindings": [                     # mandatory: list of parameter bindings matching the input parameters in the template
                    {
                        "key": "envexample",
                        "value": "test1"
                    } 
                ],
                "input_artifact_bindings": []               # mandatory: list of artifact bindings with key field, referencing above artifact - keys
            },
            "destination_name": "AI_CORE_DEPLOYMENT",       # optional - specify if destination should be created with deployment id
            "wait_for_status": "RUNNING"                    # optional: status to wait on, if not there, only triggers
        }
    ]
}