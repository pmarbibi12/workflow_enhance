import requests
import pathlib
import pandas as pd
import json
from datetime import datetime
import pytz

productGuids = [
    "07d1c32e-8f8d-41ba-b0c1-6755b12261fb","08696a82-139e-43c8-b54c-dedc568f0073","086eb3e4-89d0-4f46-b6ed-11a8834deb3e","086d9f2e-cc52-4086-a898-e540b862e5c0","085d3421-a6b2-4448-8242-7a59f7e5226a","0859d695-fa50-4a51-8c30-2a73f9453991","085a3eb2-9c57-4825-a171-bef771aa30f4","083f1e90-47fb-414e-a228-f89ab678b646","08470d8e-e7bd-4062-8d2c-5c7057c83289","083d7b1a-1ebb-4cd5-9576-1acabcfbba44","081c8426-ae3f-4f36-a0af-ef7730708352","081b39c0-1ac1-405c-9f66-747e2c74e305","07f25bf3-9f78-48dd-9cbe-46349d86987b","07d0a0c5-985b-482f-ba1d-c8cdfcd0032d","07d0fb5f-3240-4bfd-8d55-eb9bb363a55c"
]

workflowId = "c0c48edf-2645-4271-b8b6-cfa33d720876"
auth = "EN AkVOZZ4SaRThrEuRm/U8cL6KKAhwbWFyYmliaXT9eVFP6tkBdT1ees/v2QECAAAAEkVOLlJvb3RQZXJtaXNzaW9ucwMxMjYAAA9FTi5Vc2VyRnVsbE5hbWULUGFuIE1hcmJpYmkAAIscXAbqdbcCteYGlP6CJ1TLYqVi3vNx2gUnkVyUYnEM3zMiNKM+CwAmhr2AKW9cUFqw0UcwwBXL2FH87+e76hKPok65AP0Tf9+7P8fPZd/uV1iDH600hSxVf/w8LkFQc1Uh1JXlexAzQEDRXhvLYU9C5UR73ITqWiX+L6mJYoxl" 
headers = {
    "User-Agent": "PostmanRuntime/y.32.3",
    "Accept": "*/*",
    "Accept-Encoding": "gzip,deflate,br" ,
    "Connection" : "keep-alive",
    "Authorization": auth
    }
env = "api.syndigo.com"

dataowner = "c7407733-1be6-452b-82b1-95a89c0cb2a1"

def save_worfklow_info(workflowid, dataowner, environment, auth):
    workflowId = workflowid
    dataowner = dataowner
    env = environment
    auth = auth

    return workflowId, dataowner, env, auth


def get_statuses(dataowner):
    wf_name_and_statuses = f"https://{env}/api/workflow/workflowgrain/bydataowner/{dataowner}"

    name_response = requests.get(wf_name_and_statuses, headers=headers)

    wf_statuses = []
    step_ids = []
    step_desc = []

    if name_response.status_code == 200:
        response_json = name_response.json()
        step_names = response_json[workflowId]
        for step_id, step_data in step_names.get("StepNames", {}).items():
            step_ids.append(step_id)
            step_desc.append(step_data.get("InvariantCultureDescription"))
        steps_with_names = {step_id : desc for step_id, desc in zip(step_ids, step_desc)}
    else:
        wf_statuses.append("No Statuses")

    return steps_with_names

steps_with_names = get_statuses(dataowner)

def statusId_to_statusName(step_id):

    if step_id in steps_with_names:
        return steps_with_names[step_id]
    else:
        return step_id

def getStatuses(productGuids):   
    timeStamp = []
    statuses = []
    wf_version = []
    instaceIds = []

    cst_timezone = pytz.timezone('America/Chicago')

    for product in productGuids:
        status_search_url = f"https://{env}/api/workflow/WorkflowGrain/status/{workflowId}/{product}"
        response = requests.get(status_search_url, headers=headers)
        if response.status_code == 200:
            json_response = response.json()
            timestamp_response = json_response["Timestamp"]
            timestamp_without_fractional_seconds = timestamp_response.split('.')[0]
            parsed_datetime = datetime.fromisoformat(timestamp_without_fractional_seconds)
            cst_datetime = parsed_datetime.astimezone(cst_timezone)
            readable_format = cst_datetime.strftime("%Y-%m-%d %H:%M:%S %Z")
            timeStamp.append(readable_format)
            status_response = json_response["Statuses"]
            stat_names = []
            for status in status_response:
                name = statusId_to_statusName(status)
                stat_names.append(name)
            statuses.append(stat_names)
            wf_version.append(json_response["WorkflowVersion"])
            instaceIds.append(json_response["WorkflowInstanceId"])
        else:
            timeStamp.append("Null")
            statuses.append("Null")
            wf_version.append("Null")
            instaceIds.append("Null")

    data = {
        "Product ID" : productGuids,
        "Updated" : timeStamp,
        "Status" : statuses,
        "Instance ID": instaceIds,
        "Version" : wf_version
    }

    return data

data = getStatuses(productGuids)

def output_to_csv(data):
    workflow_statuses = pd.DataFrame(data)
    workflow_statuses.to_csv('output.csv', index=False)


output_to_csv(data)
