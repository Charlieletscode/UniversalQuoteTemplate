import requests
import os
import json
import xml.etree.ElementTree as ET
import sys
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)
from servertest import getVerisaeCreds
# 230823-0151

url = 'https://wbs.verisae.com/DataNett/action/workOrderActions'
login_page = 'https://wbs.verisae.com/DataNett/test/webservices/test_workOrderActions.html'

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    "Cache-Control": "no-cache",
}

# if not os.path.exists('Verisae/VerisaeEstimate'):
#     os.makedirs('Verisae/VerisaeEstimate')
    
if not os.path.exists('api/Verisae/VerisaeQuote'):
    os.makedirs('api/Verisae/VerisaeQuote')

# nte
# def submitEstimateVerisae():
#     xml_request = '''<?xml version="1.0" encoding="UTF-8"?>
# <WorkOrderActions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#                   xsi:noNamespaceSchemaLocation="https://wbs.verisae.com/DataNett/xsd/WorkOrderActions.xsd"
#                   updateDataBase="true">
#   <copyright>Verisae, Inc.</copyright>
#   <work_orders>
#     <work_order>
#       <work_order_number></work_order_number>
#       <wo_actions>
#         <submit_estimate>
#           <user_name></user_name>
#               <description></description>
#               <travel></travel>
#               <parts></parts>
#               <labor></labor>
#               <misc></misc>
#               <travel_tax_rate></travel_tax_rate>
#               <parts_tax_rate></parts_tax_rate>
#               <labor_tax_rate></labor_tax_rate>
#               <misc_tax_rate></misc_tax_rate>
#               <travel_second_tax_rate></travel_second_tax_rate>
#               <parts_second_tax_rate></parts_second_tax_rate>
#               <labor_second_tax_rate></labor_second_tax_rate>
#               <misc_second_tax_rate></misc_second_tax_rate>
#               <manual_tax></manual_tax>
#         </submit_estimate>
#       </wo_actions>
#     </work_order>
#   </work_orders>
# </WorkOrderActions>
#     '''
#     data = {                                            
#         'login':username,
#         'password':password,
#         'loginPage':"webservice",
#         'xml': xml_request,
#     }

#     response = requests.post(url, headers=headers, data=data)
#     if response.status_code == 200:
#         print('Accept successfully.')
#         with open('Verisae/VerisaeEstimate/work_order_accept.xml', 'w') as file:
#             file.write(response.text)
#         with open('Verisae/VerisaeEstimate/work_order_accept.xml', 'w') as file:
#             file.write(xml_request)
#     else:
#         print('Error occurred:', response.status_code)

# quote
def submitQuoteVerisae(provider, ticketID, des, travelTotal, partsTotal, laborTotal, miscTotal, tax, work_order_number):
    xml_request = f'''<?xml version="1.0" encoding="UTF-8"?>
<WorkOrderActions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xsi:noNamespaceSchemaLocation="https://wbs.verisae.com/DataNett/xsd/WorkOrderActions.xsd"
                  updateDataBase="true">
  <copyright>Verisae, Inc.</copyright>
  <work_orders>
    <work_order>
      <work_order_number>{work_order_number}</work_order_number>
      <wo_actions>
        <submit_quote>
          <user_name>aerb</user_name>
              <provider>{provider}</provider>
              <quote_number>{ticketID}</quote_number>
              <description>{des}</description>
              <travel>{travelTotal}</travel>
              <parts>{partsTotal}</parts>
              <labor>{laborTotal}</labor>
              <misc>{miscTotal}</misc>
              <manual_tax>{tax}</manual_tax>
        </submit_quote>
      </wo_actions>
    </work_order>
  </work_orders>
</WorkOrderActions>
    '''
    (username, password) = getVerisaeCreds(ticketID)
    if username.any() or password.any():
        data = {                                            
            'login':username[0],   
            'password':password[0],
            'loginPage':"webservice",
            'xml': xml_request,
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            with open('api/Verisae/VerisaeQuote/submitQuoteVerisaeResult.xml', 'w') as file:
                file.write(response.text)
            root = ET.fromstring(response.text)      
            exception_message_element = root.find(".//exception_message")
            work_order_status_element = root.find(".//work_order_status")
            # print(exception_message_element.text, work_order_status_element.text)
            if work_order_status_element:
                exception_message_element = root.find(".//exception_message")
                exception_message = f"{exception_message_element.text} workorderstatus: {work_order_status_element.text}"
                return f"Verisae quote submit failed. WORKORDERNUMBER: {work_order_number} WORKORDERSTATUS: {work_order_status_element.text} EXCEPTION: {exception_message_element.text}"
            elif exception_message_element or exception_message_element is not None:
                exception_message = exception_message_element.text
                return f"Verisae quote submit failed. WORKORDERNUMBER: {work_order_number} WORKORDERSTATUS: no status return EXCEPTION: {exception_message_element.text}"
            else:
                return 'Verisae quote submit successfully.'
        else:
            return f'str(response.status_code))+"creds error'
    else:
        return f'EXEC [GFT].[dbo].[MR_Univ_User_Info]  @ticket_no = {ticketID} is empty please take a screenshot and report to IT'
    
    with open('api/Verisae/VerisaeQuote/submitQuoteVerisae.xml', 'w') as file:
        file.write(xml_request)
