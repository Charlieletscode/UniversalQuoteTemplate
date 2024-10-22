import json
import requests
import pandas as pd
import re
import os

# creds sync change
# basic = os.environ.get("CircleKkeyBasic")
# 230215-0004

if not os.path.exists('api/CircleK/wo_cost_information'):
    os.makedirs('api/CircleK/wo_cost_information')

def circleK_wo_cost_information(labor, trip, parts, misc, materials, sub, taxRate, Purchase_Order, basicCreds):
    uri = "https://circlek.service-now.com/api/x_nuvo_eam/update_nuvolo_wo/wo_cost_information"
    # url = "https://circlekdev.service-now.com/api/x_nuvo_eam/get_wo_information/open_wo_lists?number=<FWKD1656024>"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic "+basicCreds["Decrypted_Token_Value"][0]
    }
    total = sum([labor, parts, misc, materials, sub]) * (1 + taxRate / 100.0)
    
    data = {
    "number": f"{Purchase_Order.iloc[0].strip()}",
    "u_total_labor_cost_str": f"{total:.2f}",
    "u_total_travel_cost_str": f"{trip * (1 + taxRate / 100.0):.2f}",
    "attachment_link":""
    }
    response = requests.put(uri, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        if result["result"]["result"]:
            with open("response.json", "w") as json_file:
                json.dump(result, json_file, indent=4)
            return "circlek quote submit successfully!"
        else:
            
            return f"circlek quote submit failed. Error message: {result['result']['msg']}" 
    else:
        return f"circlek quote submit failed with status code: {response.status_code}"