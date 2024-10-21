import requests
import base64
import json
import os

token = os.environ.get("fmDashtoken")
# 230726-0289

def checkout(work_order_id):
    url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id}/checkout?token={token}"
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
    # print(response.text, response.status_code)

def submitFmQuotes(pdf_base64, work_order_id, incurred, proposed, labor_df, trip_df, parts_df, misc_df, materials_df, sub_df, total, taxTotal):
    url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id}/checkout?token={token}"
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
    # print(response.text, response.status_code)
    api_url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/{work_order_id}/quotes?token={token}"

    laborIncurredmask = (labor_df["Incurred/Proposed"] == "Incurred")
    laborProposedmask = (labor_df["Incurred/Proposed"] == "Proposed")
    tripIncurredmask = (trip_df["Incurred/Proposed"] == "Incurred")
    tripProposedmask = (trip_df["Incurred/Proposed"] == "Proposed")
    partsIncurredmask = (parts_df["Incurred/Proposed"] == "Incurred")
    partsProposedmask = (parts_df["Incurred/Proposed"] == "Proposed")

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
    headers = {}
    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code == 200:
        # data = response.json()
        # print(data)
        print("Quote submitted. Quote ID:", response.text)
    else:
        print("Failed to submit quote. Status code:", response.status_code)
        
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
#     pdf_content = pdf_file.read()
#     pdf_base64 = base64.b64encode(pdf_content).decode("utf-8")
# work_order_id = 122133
# incurred = "incurred test1"
# proposed = "proposed test1"
# total = 1000.0
# taxTotal = 10

# getOpenWO("getWO1.json")
# getNeedToQuote()
# checkout(work_order_id)
# submitFmQuotes(pdf_base64, work_order_id, incurred, proposed, labor_df, trip_df, parts_df, misc_df, materials_df, sub_df, total, taxTotal)
#   py api4notgit/fmdash.py

# def getOpenWO(filename):
#     api_url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders?token={token}"
#     response = requests.get(api_url)

#     if response.status_code == 200:
#         data = response.json()
#         # Save the data to a JSON file
#         with open(filename, "w") as json_file:
#             json.dump(data, json_file, indent=4)
#         print("Work orders saved to getWO.json")
#     else:
#         print("Failed to fetch work orders. Status code:", response.status_code)

# getOpenWO("getWO1.json")

# def getNeedToQuote():
#     url = f"https://fmdashboard-staging.herokuapp.com/api/work_orders/status_filter=150&?token={token}"
#     headers = {
#         'Authorization': f'Bearer :{token}',
#     }
#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         work_orders = response.json()
#         print(work_orders)
#     else:
#         print(f"Request failed with status code: {response.status_code}")
