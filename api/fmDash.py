import requests
import base64
import json
import os
import pandas as pd
import numpy as np
import sys

# 240409-0055
# from servertest import getFmDashCreds
# json serializable error might still occur

# these two tokens should be pass through the database 

# print(getToken("MAJ0001").get("Decrypted_Token_Value", 0))
# token1 = getCredsToken("MAJ0001").iloc[0]['Decrypted_Token_Value']
# token2 = os.environ.get("fmDashtoken2")

def convert_numpy_types(data):
    if isinstance(data, dict):
        return {key: convert_numpy_types(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(item) for item in data]
    elif isinstance(data, np.integer):  # For NumPy integer types
        return int(data)
    elif isinstance(data, np.floating):  # For NumPy float types
        return float(data)
    elif isinstance(data, np.ndarray):  # For NumPy arrays
        return data.tolist()  # Convert arrays to lists
    else:
        return data

def devCheckout():
    work_order_id = "114468"
    token1 = "b0285bd1-e6da-436a-a318-351a64aa730b"
    urldev = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id}/checkout?token={token1}"
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "checkout": {
            "description": "Quote Submitted",
            "status": "150",
            "resolution": "Repaired"
        }
    }
    payload_json = json.dumps(payload)
    response = requests.post(urldev, headers=headers, data=payload_json)
    print("checkout success?",response.status_code)

def submitFmQuotesDev(token1, pdf_base64, work_order_id, incurred, proposed, labor_df, trip_df, parts_df, misc_df, materials_df, sub_df, total, taxTotal):
    devtoken1 = "b0285bd1-e6da-436a-a318-351a64aa730b"
    work_order_id = "114468"

    # # Construct the URL
    # url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id}/quotes?token={devtoken1}"

    # # Payload as a Python dictionary
    # payload = {
    #     "quote": {
    #         "id": 0,
    #         "incurred_description": "string",
    #         "proposed_description": "string",
    #         "ready": True,
    #         "incurred_trip_charge": 0,
    #         "proposed_trip_charge": 0,
    #         "total": 0,
    #         "make": "string",
    #         "model": "string",
    #         "serial_number": "string",
    #         "simple_quote": True,
    #         "document": "base64 string of PDF",
    #         "incurred_time": 0,
    #         "incurred_material": 0,
    #         "proposed_time": 0,
    #         "proposed_material": 0,
    #         "tax_total": 0
    #     }
    # }

    # # Set headers
    # headers = {
    #     'Content-Type': 'application/json'  # Explicitly set Content-Type to application/json
    # }

    # # Send the POST request using the json parameter
    # response = requests.post(url, headers=headers, json=payload)

    # # Output the response
    # print(response.text, response.status_code, "first")
    # # Construct the URL
    # url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id}/quotes?token={devtoken1}"

    # # Payload as a Python dictionary
    # payload = {
    #     "quote": {
    #         "id": 0,
    #         "incurred_description": "string",
    #         "proposed_description": "string",
    #         "ready": True,
    #         "incurred_trip_charge": 0,
    #         "proposed_trip_charge": 0,
    #         "total": 0,
    #         "make": "string",
    #         "model": "string",
    #         "serial_number": "string",
    #         "simple_quote": True,
    #         "document": "base64 string of PDF",
    #         "incurred_time": 0,
    #         "incurred_material": 0,
    #         "proposed_time": 0,
    #         "proposed_material": 0,
    #         "tax_total": 0
    #     }
    # }

    # # Convert the payload dictionary to a JSON string
    # payload_json = json.dumps(payload)

    # # Set headers
    # headers = {
    #     'Content-Type': 'application/json'
    # }

    # # Send the POST request with json.dumps() payload
    # response = requests.post(url, headers=headers, data=payload_json)

    # # Output the response
    # print(response.text, response.status_code, "second")
    # url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id}/quotes?token={devtoken1}"

    # # Raw JSON payload string
    # payload = """
    # {
    #     "quote": {
    #         "id": 0,
    #         "incurred_description": "string",
    #         "proposed_description": "string",
    #         "ready": true,
    #         "incurred_trip_charge": 0,
    #         "proposed_trip_charge": 0,
    #         "total": 0,
    #         "make": "string",
    #         "model": "string",
    #         "serial_number": "string",
    #         "simple_quote": true,
    #         "document": "base64 string of PDF",
    #         "incurred_time": 0,
    #         "incurred_material": 0,
    #         "proposed_time": 0,
    #         "proposed_material": 0,
    #         "tax_total": 0
    #     }
    # }
    # """

    # # Set headers
    # headers = {
    #     'Content-Type': 'application/json'
    # }

    # # Send the POST request with raw JSON payload
    # response = requests.post(url, headers=headers, data=payload)

    # # Output the response
    # print(response.text, response.status_code, "third")
    # url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id}/quotes?token={devtoken1}"

    # # Payload as a Python dictionary
    # payload = {
    #     "quote": {
    #         "id": 0,
    #         "incurred_description": "string",
    #         "proposed_description": "string",
    #         "ready": True,
    #         "incurred_trip_charge": 0,
    #         "proposed_trip_charge": 0,
    #         "total": 0,
    #         "make": "string",
    #         "model": "string",
    #         "serial_number": "string",
    #         "simple_quote": True,
    #         "document": "base64 string of PDF",
    #         "incurred_time": 0,
    #         "incurred_material": 0,
    #         "proposed_time": 0,
    #         "proposed_material": 0,
    #         "tax_total": 0
    #     }
    # }

    # # Set headers
    # headers = {
    #     'Content-Type': 'application/json'
    # }

    # # Send the POST request using requests.request
    # response = requests.request("POST", url, headers=headers, json=payload)

    # # Output the response
    # print(response.text, response.status_code, "fourth")

    api_url = f"https://fmdashboard-staging.herokuapp.com/api/{work_order_id}/quotes?token={devtoken1}"

    laborIncurredmask = (labor_df["Incurred/Proposed"] == "Incurred")
    laborProposedmask = (labor_df["Incurred/Proposed"] == "Proposed")
    tripIncurredmask = (trip_df["Incurred/Proposed"] == "Incurred")
    tripProposedmask = (trip_df["Incurred/Proposed"] == "Proposed")
    partsIncurredmask = (parts_df["Incurred/Proposed"] == "Incurred")
    partsProposedmask = (parts_df["Incurred/Proposed"] == "Proposed")

    # print(type(0), type(np.int64(trip_df.loc[tripProposedmask,'EXTENDED'].sum()+trip_df.loc[tripIncurredmask,'EXTENDED'].sum())), trip_df.loc[tripProposedmask,'EXTENDED'].sum()+trip_df.loc[tripIncurredmask,'EXTENDED'].sum())
    
    url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id.strip()}/quotes?token={devtoken1}"

    payload = json.dumps({
    "quote": {
        "id": work_order_id.strip(),
        "incurred_description": "string",
        "proposed_description": "Incurred Workdescription: " + incurred + "Proposed Workdescription: " + proposed,
        "incurred_trip_charge": 0,
        "proposed_trip_charge": 0,
        "total": total,
        "make": "string",
        "model": "string",
        "serial_number": "string",
        "document": pdf_base64,
        "incurred_time": 0,
        "incurred_material": 0,
        "proposed_time": convert_numpy_types(labor_df.loc[laborProposedmask,'EXTENDED'].sum() + labor_df.loc[laborIncurredmask,'EXTENDED'].sum()),
        "proposed_material": convert_numpy_types(parts_df.loc[partsIncurredmask,'EXTENDED'].sum() + parts_df.loc[partsProposedmask,'EXTENDED'].sum() + misc_df['EXTENDED'].sum() + materials_df['EXTENDED'].sum() + sub_df['EXTENDED'].sum()),
        "tax_total": convert_numpy_types(round(taxTotal - total, 2)),
    }
    })
    headers = {
    'Content-Type': 'application/json',
    # 'Cookie': '_fmdashboard_session=MukQO5VqYAPQ%2Bl3YWOzYB3gJE9M%2BKpln0f0CbB275uuubKnYhXCpjxhkHY5Jk0NZmWQQw7dcTTHg%2FI1WchRyNBxl2Hz1ZKJLwlg34bYRFr6YubdYhv67SL6%2B2VVobJHXy5J8IFtM4DpLvXO6D8ZqFU95fNdKJeH29o5zNFzlDvZpPpNiJMQNM7%2B86dToD66Eq8jY17GI1mb7JlyHV%2BYdNa1q8wKSzIPsRzJo76LlCkY3klYv43iq9N2JxDA4R1Tc1aQl9dbllktecKHTlNinUGftQPqSiN%2BrpnLfC%2FRLoC7o2ogr74wpScBvW7XYoBHZFYiJBmh%2BtW0TJPMdApkyy7nAr2o5e655ndcA3AWZhuihc7zrdQDBVt3uzqLW2oA20vSqLXucN%2BLIZ1pj4MVORo5veXWnhOwhfycYyH%2BkhvfGjAtTZeSY2a3PYp2iyhW5FGbhZ7pDt0fGJJG8oGnYuVoAFS0%3D--9vxBIpEoFvDQnhZx--WEp210ZahF3rMI%2B0J6RxWw%3D%3D'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.status_code, response.text)
    if response.status_code == 200:
        status = 1
        return 'FmDash submit successfully.'
    else:
        # print(f'Error: Status Code {response.status_code}, Message: {json.dumps(response.json(), indent=4)}')
        return f'Error: Status Code {response.status_code}, Message: {response.text}'


def check(token1, work_order_id):
    # test run
    work_order_id = "165211"
    # token1 = "b0285bd1-e6da-436a-a318-351a64aa730b"
    url = f"https://app.fmdashboard.com/api/work_orders/{work_order_id}/checkin?token={token1}"
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
    "work_order": {
        "id": 165211
    }
}
    payload_json = json.dumps(payload)
    response = requests.post(url, headers=headers, data=payload_json)
    print("checkout success:", response.status_code)

def checkout(token1, work_order_id):
    # test run
    # work_order_id = "172270"
    # token1 = "b0285bd1-e6da-436a-a318-351a64aa730b"
    url = f"https://app.fmdashboard.com/api/work_orders/{work_order_id}/checkout?token={token1}"
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "checkout": {
            "description": "Quote Submitted",
            "status": "150",
            "resolution": "Repaired"
        }
    }
    payload_json = json.dumps(payload)
    response = requests.post(url, headers=headers, data=payload_json)
    print("checkout success:", response.status_code)
    # print check session
    # if response.status_code == 200:
    #     print("token1 Request successful!")
    # else:
    #     print("token1 Request failed with status code:", response.status_code)
    # url = f"https://app.fmdashboard.com/api/work_orders/{work_order_id}/checkout?token={token2}"
    # headers = {
    #     "Content-Type": "application/json",
    # }

    # payload = {
    #     "checkout": {
    #         "description": "Quote Submitted",
    #         "status": "150",
    #         "resolution": "Repaired"
    #     }
    # }
    # payload_json = json.dumps(payload)
    # response = requests.post(url, headers=headers, data=payload_json)
    # if response.status_code == 200:
    #     print("token2 Request successful!")
    # else:
    #     print("token2 Request failed with status code:", response.status_code)
# work_order_id = "161291"
# token1 = "ace9d5db-20c6-482b-b3f2-0157a5496bf7"
# checkout(token1, work_order_id)

def submitFmQuotes(token1, pdf_base64, work_order_id, incurred, proposed, labor_df, trip_df, parts_df, misc_df, materials_df, sub_df, total, taxTotal):
    # work_order_id = "128161"
    url = f"https://app.fmdashboard.com/api//work_orders/{work_order_id.strip()}/quotes?token={token1}"

    laborIncurredmask = (labor_df["Incurred/Proposed"] == "Incurred")
    laborProposedmask = (labor_df["Incurred/Proposed"] == "Proposed")
    tripIncurredmask = (trip_df["Incurred/Proposed"] == "Incurred")
    tripProposedmask = (trip_df["Incurred/Proposed"] == "Proposed")
    partsIncurredmask = (parts_df["Incurred/Proposed"] == "Incurred")
    partsProposedmask = (parts_df["Incurred/Proposed"] == "Proposed")

    # print(type(0), type(np.int64(trip_df.loc[tripProposedmask,'EXTENDED'].sum()+trip_df.loc[tripIncurredmask,'EXTENDED'].sum())), trip_df.loc[tripProposedmask,'EXTENDED'].sum()+trip_df.loc[tripIncurredmask,'EXTENDED'].sum())
    
    payload = json.dumps({
    "quote": {
        "id": work_order_id.strip(),
        "incurred_description": "string",
        "proposed_description": "Incurred Workdescription: " + incurred + "Proposed Workdescription: " + proposed,
        "incurred_trip_charge": 0,
        "proposed_trip_charge": 0,
        "total": total,
        "make": "string",
        "model": "string",
        "serial_number": "string",
        "document": pdf_base64,
        "incurred_time": 0,
        "incurred_material": 0,
        "proposed_time": convert_numpy_types(labor_df.loc[laborProposedmask,'EXTENDED'].sum() + labor_df.loc[laborIncurredmask,'EXTENDED'].sum()),
        "proposed_material": convert_numpy_types(parts_df.loc[partsIncurredmask,'EXTENDED'].sum() + parts_df.loc[partsProposedmask,'EXTENDED'].sum() + misc_df['EXTENDED'].sum() + materials_df['EXTENDED'].sum() + sub_df['EXTENDED'].sum()),
        "tax_total": convert_numpy_types(round(taxTotal - total, 2)),
    }
    })
    headers = {
    'Content-Type': 'application/json',
    # 'Cookie': '_fmdashboard_session=MukQO5VqYAPQ%2Bl3YWOzYB3gJE9M%2BKpln0f0CbB275uuubKnYhXCpjxhkHY5Jk0NZmWQQw7dcTTHg%2FI1WchRyNBxl2Hz1ZKJLwlg34bYRFr6YubdYhv67SL6%2B2VVobJHXy5J8IFtM4DpLvXO6D8ZqFU95fNdKJeH29o5zNFzlDvZpPpNiJMQNM7%2B86dToD66Eq8jY17GI1mb7JlyHV%2BYdNa1q8wKSzIPsRzJo76LlCkY3klYv43iq9N2JxDA4R1Tc1aQl9dbllktecKHTlNinUGftQPqSiN%2BrpnLfC%2FRLoC7o2ogr74wpScBvW7XYoBHZFYiJBmh%2BtW0TJPMdApkyy7nAr2o5e655ndcA3AWZhuihc7zrdQDBVt3uzqLW2oA20vSqLXucN%2BLIZ1pj4MVORo5veXWnhOwhfycYyH%2BkhvfGjAtTZeSY2a3PYp2iyhW5FGbhZ7pDt0fGJJG8oGnYuVoAFS0%3D--9vxBIpEoFvDQnhZx--WEp210ZahF3rMI%2B0J6RxWw%3D%3D'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.status_code, response.text)
    if response.status_code == 200:
        status = 1
        return 'FmDash submit successfully.'
    else:
        # print(f'Error: Status Code {response.status_code}, Message: {json.dumps(response.json(), indent=4)}')
        return f'Error: Status Code {response.status_code}, Message: {response.text}'
# GPM is currently not needed
    url = f"https://app.fmdashboard.com/api/work_orders/{work_order_id}/checkout?token={token2}"
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "checkout": {
            "description": "This is the description of my checkout. Thanks!",
            "status": "150",
            "resolution": "Repaired"
        }
    }
    payload_json = json.dumps(payload)
    response = requests.post(url, headers=headers, data=payload_json)
    api_url = f"https://app.fmdashboard.com/api/work_orders/{work_order_id}/quotes?token={token2}"

    laborIncurredmask = (labor_df["Incurred/Proposed"] == "Incurred")
    laborProposedmask = (labor_df["Incurred/Proposed"] == "Proposed")
    tripIncurredmask = (trip_df["Incurred/Proposed"] == "Incurred")
    tripProposedmask = (trip_df["Incurred/Proposed"] == "Proposed")
    partsIncurredmask = (parts_df["Incurred/Proposed"] == "Incurred")
    partsProposedmask = (parts_df["Incurred/Proposed"] == "Proposed")

    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "quote": {
        "id": work_order_id,
        "incurred_description": "",
        "proposed_description": "Incurred Workdescription: " + incurred + "Proposed Workdescription: " + proposed,
        "ready": True,
        "incurred_trip_charge": 0, 
        "proposed_trip_charge": trip_df.loc[tripProposedmask,'EXTENDED'].sum()+trip_df.loc[tripIncurredmask,'EXTENDED'].sum(), 
        "total": total,
        "make": "string",
        "model": "string",
        "serial_number": "string",
        "simple_quote": False,
        "document": pdf_base64,
        "document_cache": "string",
        "incurred_time" : 0,
        "proposed_time" : labor_df.loc[laborProposedmask,'EXTENDED'].sum() + labor_df.loc[laborIncurredmask,'EXTENDED'].sum(),
        "incurred_material": 0,
        "proposed_material": parts_df.loc[partsIncurredmask,'EXTENDED'].sum() + parts_df.loc[partsProposedmask,'EXTENDED'].sum() + misc_df['EXTENDED'].sum() + materials_df['EXTENDED'].sum() + sub_df['EXTENDED'].sum(),
        "tax_total": taxTotal - total,
        "approval_document_file": "string"
    }
    }
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(api_url, headers=headers, json=payload)
    


# data = {
#     "Incurred/Proposed": ["Incurred", "Incurred", "Proposed", "Incurred", "Proposed"],
#     "Description": ["Description1", "Description2", "Description3", "Description4", "Description5"],
#     "Nums of Techs": [2, 3, 1, 2, 1],
#     "Hours per Tech": [4.5, 3.0, 5.5, 4.0, 6.0],
#     "QTY": [1.0, 2.0, 3.0, 1.5, 2.5],
#     "Hourly Rate": [25.0, 30.0, 20.0, 22.0, 18.0],
#     "EXTENDED": [225.0, 180.0, 110.0, 176.0, 108.0],
# }

# labor_df = pd.DataFrame(data)

# trip_charge_data = {
#     'Incurred/Proposed': ['Incurred', 'Proposed', 'Incurred'],
#     'Description': ['Travel Expense', 'Lodging', 'Meal Expense'],
#     'QTY': [2, 1, 3],
#     'UNIT Price': [50.00, 120.00, 25.00],
#     'EXTENDED': [100.00, 120.00, 75.00]
# }
# trip_df = pd.DataFrame(trip_charge_data)

# parts_data = {
#     'Incurred/Proposed': ['Incurred', 'Proposed', 'Incurred'],
#     'Description': ['Part A', 'Part B', 'Part C'],
#     'QTY': [5, 2, 3],
#     'UNIT Price': [10.00, 15.00, 8.00],
#     'EXTENDED': [50.00, 30.00, 24.00]
# }
# parts_df = pd.DataFrame(parts_data)

# miscellaneous_data = {
#     'Description': ['Charge X', 'Charge Y', 'Charge Z'],
#     'QTY': [1, 2, 3],
#     'UNIT Price': [50.00, 25.00, 30.00],
#     'EXTENDED': [50.00, 50.00, 90.00]
# }
# misc_df = pd.DataFrame(miscellaneous_data)

# materials_rentals_data = {
#     'Description': ['Material 1', 'Material 2', 'Rental A'],
#     'QTY': [10, 5, 2],
#     'UNIT Price': [5.00, 8.00, 50.00],
#     'EXTENDED': [50.00, 40.00, 100.00]
# }
# materials_df = pd.DataFrame(materials_rentals_data)

# subcontractor_data = {
#     'Description': ['Subcontractor X', 'Subcontractor Y', 'Subcontractor Z'],
#     'QTY': [1, 2, 3],
#     'UNIT Price': [500.00, 750.00, 600.00],
#     'EXTENDED': [500.00, 1500.00, 1800.00]
# }
# sub_df = pd.DataFrame(subcontractor_data)

# with open("input.pdf", "rb") as pdf_file:
    # pdf_content = pdf_file.read()
    # pdf_base64 = base6
    # 4.b64encode(pdf_content).decode("utf-8")
# pdf_base64 = "just test"
# work_order_id = 128161
# incurred = "incurred test1"
# proposed = "proposed test1"
# total = 1000.0
# taxTotal = 10

# submitFmQuotes(pdf_base64, work_order_id, incurred, proposed, labor_df, trip_df, parts_df, misc_df, materials_df, sub_df, total, taxTotal)