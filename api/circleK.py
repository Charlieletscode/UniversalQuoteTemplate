import json
import requests
import pandas as pd
import re
import os
basic = os.environ.get("CircleKkeyBasic")
# 230215-0004

if not os.path.exists('api/CircleK/wo_cost_information'):
    os.makedirs('api/CircleK/wo_cost_information')

def wo_cost_information(labor, trip, parts, misc, materials, sub, taxRate, workorder_id):

    uri = "https://circlekdev.service-now.com/api/x_nuvo_eam/update_nuvolo_wo/wo_cost_information"
    # url = "https://circlekdev.service-now.com/api/x_nuvo_eam/get_wo_information/open_wo_lists?number=<FWKD1656024>"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic "+basic
    }
    total = sum([labor, parts, misc, materials, sub]) * (1 + taxRate / 100.0)

    data = {
    "number": f"{workorder_id}",
    "u_total_labor_cost_str": f"{total:.2f}",
    "u_total_travel_cost_str": f"{trip * (1 + taxRate / 100.0):.2f}",
    "attachment_link":""
    }
    response = requests.get(uri, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        if result["result"]["result"]:
            print("Record updated successfully!")
            with open("response.json", "w") as json_file:
                json.dump(result, json_file, indent=4)
        else:
            print("Update failed. Error message:", result["result"]["msg"])
    else:
        print("Request failed with status code:", response.status_code)