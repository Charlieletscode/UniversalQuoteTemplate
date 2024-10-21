import requests
import os

# 230823-0151
username = os.environ.get("verisaeUsername")
password = os.environ.get("verisaePassword")

url = 'https://training2.verisae.com/DataNett/action/workOrderActions'
login_page = 'https://training2.verisae.com/DataNett/test/webservices/test_workOrderActions.html'

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
def submitQuoteVerisae(username, ticketID, des, travelTotal, partsTotal, laborTotal, miscTotal, tax):
    xml_request = f'''<?xml version="1.0" encoding="UTF-8"?>
<WorkOrderActions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xsi:noNamespaceSchemaLocation="https://wbs.verisae.com/DataNett/xsd/WorkOrderActions.xsd"
                  updateDataBase="true">
  <copyright>Verisae, Inc.</copyright>
  <work_orders>
    <work_order>
      <work_order_number>67756162</work_order_number>
      <wo_actions>
        <submit_quote>
          <user_name>aerb</user_name>
              <provider>{username}</provider>
              <quote_number>{ticketID}</quote_number>
              <description>{des}</description>
              <travel>{travelTotal}</travel>
              <parts>{partsTotal}</parts>
              <labor>{laborTotal}</labor>
              <misc>{miscTotal}</misc>
              <travel_tax_rate></travel_tax_rate>
              <parts_tax_rate></parts_tax_rate>
              <labor_tax_rate></labor_tax_rate>
              <misc_tax_rate></misc_tax_rate>
              <travel_second_tax_rate></travel_second_tax_rate>
              <parts_second_tax_rate></parts_second_tax_rate>
              <labor_second_tax_rate></labor_second_tax_rate>
              <misc_second_tax_rate></misc_second_tax_rate>
              <manual_tax>{tax}</manual_tax>
        </submit_quote>
      </wo_actions>
    </work_order>
  </work_orders>
</WorkOrderActions>
    '''
    data = {                                            
        'login':username,
        'password':password,
        'loginPage':"webservice",
        'xml': xml_request,
    }
    print(xml_request)
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print('Accept successfully.')
        with open('api/Verisae/VerisaeQuote/submitQuoteVerisaeResult.xml', 'w') as file:
            file.write(response.text)
    else:
        print('Error occurred:', response.status_code)
    
    with open('api/Verisae/VerisaeQuote/submitQuoteVerisae.xml', 'w') as file:
        file.write(xml_request)
