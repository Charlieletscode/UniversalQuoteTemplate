import pandas as pd
import pyodbc
import json
import os

server = os.environ.get("serverGFT")
database = os.environ.get("databaseGFT")
username = os.environ.get("usernameGFT")
password = os.environ.get("passwordGFT")
SQLaddress = os.environ.get("addressGFT")

parameter_value = "230524-0173"


def getBinddes(input):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = """Exec [CF_PART_LOOK_UP_streamlit] @Search = ?;"""
    cursor.execute(sql_query, input)
    sql_query = cursor.fetchall()
    rows_transposed = [sql_query for sql_query in zip(*sql_query)]
    partNameDf = pd.DataFrame(dict(zip(['ITEMNMBR', 'ITEMDESC'], rows_transposed)))
    cursor.close()
    conn.close()
    return partNameDf

def getPartsPrice(partInfoDf):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    pricingDf = pd.DataFrame(columns=['ITEMNMBR', 'ITEMDESC', 'SellingPrice'])

    for index, row in partInfoDf.iterrows():
        item_num = row['ITEMNMBR']
        customer_num = row['Bill_Customer_Number']
    
        sql_query = """Exec [CF_Univ_Quote_Pricing_streamlit] @ItemNum = ?, @CUSTNMBR = ?;"""
        cursor.execute(sql_query, item_num, customer_num)
        result = cursor.fetchall()
        row_dict = {
            'ITEMNMBR': item_num,
            'ITEMDESC': "no Info",
            'SellingPrice': 0
        }
        if result:
            row_dict = {
                'ITEMNMBR': result[0][0],
                'ITEMDESC': result[0][1],
                'SellingPrice': result[0][2]
            }
        pricingDf = pricingDf.append(row_dict, ignore_index=True)
    
    cursor.close()
    conn.close()
    return pricingDf

def getAllPrice(ticketN):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = """Exec [CF_Univ_Quote_Ticket] @Service_TK = ?;"""
    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()
    rows_transposed = [sql_query for sql_query in zip(*sql_query)]
    ticketDf = pd.DataFrame(dict(zip(["LOC_Address", "LOC_CUSTNMBR", "LOC_LOCATNNM", "LOC_ADRSCODE", "LOC_CUSTNAME", "LOC_PHONE", "CITY", "STATE", "ZIP", "Pricing_Matrix_Name", "Divisions", "CUST_NAME", "CUST_ADDRESS1", "CUST_ADDRESS2", "CUST_ADDRESS3", "CUST_CITY", "CUST_State", "CUST_Zip", "Tax_Rate", "MailDispatch", "Purchase_Order", "Bill_Customer_Number"], rows_transposed)))

    sql_query = """Exec [CF_Univ_Quote_LRates] @Service_TK = ?;"""
    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()
    rows_transposed = [sql_query for sql_query in zip(*sql_query)]
    LRatesDf = pd.DataFrame(dict(zip(["Billing_Amount", "Pay_Code_Description"], rows_transposed)))
    
    sql_query = """Exec [CF_Univ_Quote_TRates] @Service_TK = ?;"""
    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()
    rows_transposed = [sql_query for sql_query in zip(*sql_query)]
    TRatesDf = pd.DataFrame(dict(zip([
    "Billing_Amount", "Pay_Code_Description"], rows_transposed)))

    sql_query = """Exec [CF_Univ_Quote_Fees] @Service_TK = ?;"""
    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()
    rows_transposed = [sql_query for sql_query in zip(*sql_query)]
    misc_ops_df = pd.DataFrame(dict(zip([
    "Fee_Charge_Type", "Fee_Amount"], rows_transposed)))
    cursor.close()
    conn.close()
    return ticketDf, LRatesDf, TRatesDf, misc_ops_df
def getDesc(ticket):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    select_query = "SELECT * FROM [CF_Universal_workdescription_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    cursor.close()
    conn.close()
    if len(dataset) == 0:
        return "None", 1, "None"
    return dataset[0][1], dataset[0][2], dataset[0][3]
def getAllTicket(ticket):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    select_query = "SELECT Description, Nums_of_Techs, Hours_per_Tech, QTY, Hourly_Rate, Extended FROM [CF_Universal_labor_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketLaborDf = pd.DataFrame(data, columns=["Description", "Nums of Techs", "Hours per Tech", "QTY", "Hourly Rate", "EXTENDED"])
    
    select_query = "SELECT Description, QTY, CAST([UNIT_Price] AS FLOAT) AS [UNIT_Price], CAST(EXTENDED AS FLOAT) AS EXTENDED FROM [CF_Universal_trip_charge_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketTripDf = pd.DataFrame(data, columns=["Description", "QTY", "UNIT Price", "EXTENDED"])

    select_query = "SELECT Description, QTY, CAST([UNIT_Price] AS FLOAT) AS [UNIT_Price], CAST(EXTENDED AS FLOAT) AS EXTENDED FROM [CF_Universal_parts_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketPartsDf = pd.DataFrame(data, columns=["Description", "QTY", "UNIT Price", "EXTENDED"])

    select_query = "SELECT Description, QTY, CAST([UNIT_Price] AS FLOAT) AS [UNIT_Price], CAST(EXTENDED AS FLOAT) AS EXTENDED FROM [CF_Universal_misc_charge_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketMiscDf = pd.DataFrame(data, columns=["Description", "QTY", "UNIT Price", "EXTENDED"])

    select_query = "SELECT Description, QTY, CAST([UNIT_Price] AS FLOAT) AS [UNIT_Price], CAST(EXTENDED AS FLOAT) AS EXTENDED FROM [CF_Universal_materials_rentals_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketMaterialsDf = pd.DataFrame(data, columns=["Description", "QTY", "UNIT Price", "EXTENDED"])

    select_query = "SELECT Description, QTY, CAST([UNIT_Price] AS FLOAT) AS [UNIT_Price], CAST(EXTENDED AS FLOAT) AS EXTENDED FROM [CF_Universal_subcontractor_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketSubDf = pd.DataFrame(data, columns=["Description", "QTY", "UNIT Price", "EXTENDED"])

    cursor.close()
    conn.close()
    return ticketLaborDf, ticketTripDf, ticketPartsDf, ticketMiscDf, ticketMaterialsDf, ticketSubDf

def updateAll(ticket, desc, editable, NTE_Quote, laborDf,  tripDf, partsDf, miscDf, materialDf, subDf):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # if desc != "None":
    delete_query = "DELETE FROM [CF_Universal_workdescription_insert] WHERE TicketID = ?"
    cursor.execute(delete_query, (ticket,))
    conn.commit()

    insert_query = "INSERT INTO [CF_Universal_workdescription_insert] (TicketID, workdescription, editable, NTE_Quote) VALUES (?, ?, ?, ?)"
    insert_data = [(ticket, desc, editable, NTE_Quote)]
    cursor.executemany(insert_query, insert_data)
    conn.commit()

    delete_query = "DELETE FROM [CF_Universal_labor_insert] WHERE TicketID = ?"
    cursor.execute(delete_query, (ticket,))
    conn.commit()

    laborDf = laborDf.dropna()
    data = laborDf[["Description", "Nums of Techs", "Hours per Tech", "QTY", "Hourly Rate", "EXTENDED"]].values.tolist()
    data = [row + [ticket] for row in data]
    insert_query = "INSERT INTO [CF_Universal_labor_insert] (Description, Nums_of_Techs, Hours_per_Tech, QTY, Hourly_Rate, EXTENDED, TicketID) VALUES (?,?,?,?,?,?,?)"
    if data:
        cursor.executemany(insert_query, data)
    conn.commit()

    delete_query = "DELETE FROM [CF_Universal_trip_charge_insert] WHERE TicketID = ?"
    cursor.execute(delete_query, (ticket,))
    conn.commit()

    tripDf = tripDf.dropna()
    data = tripDf[["Description", "QTY", "UNIT Price", "EXTENDED"]].values.tolist()
    data = [row + [ticket] for row in data]
    insert_query = "INSERT INTO [CF_Universal_trip_charge_insert] (Description, QTY, UNIT_Price, EXTENDED, TicketID) VALUES (?,?,?,?,?)"
    if data:
        cursor.executemany(insert_query, data)
    conn.commit()

    delete_query = "DELETE FROM [CF_Universal_parts_insert] WHERE TicketID = ?"
    cursor.execute(delete_query, (ticket,))
    conn.commit()
    partsDf = partsDf.dropna()
    data = partsDf[["Description", "QTY", "UNIT Price", "EXTENDED"]].values.tolist()
    data = [row + [ticket] for row in data if all(x is not None for x in row)]
    insert_query = "INSERT INTO [CF_Universal_parts_insert] (Description, QTY, UNIT_Price, EXTENDED, TicketID) VALUES (?,?,?,?,?)"
    if data:
        cursor.executemany(insert_query, data)
    conn.commit()

    
    delete_query = "DELETE FROM [CF_Universal_misc_charge_insert] WHERE TicketID = ?"
    cursor.execute(delete_query, (ticket,))
    conn.commit()
    miscDf = miscDf.dropna()
    data = miscDf[["Description", "QTY", "UNIT Price", "EXTENDED"]].values.tolist()
    data = [row + [ticket] for row in data if all(x is not None for x in row)]
    insert_query = "INSERT INTO [CF_Universal_misc_charge_insert] (Description, QTY, UNIT_Price, EXTENDED, TicketID) VALUES (?,?,?,?,?)"
    if data:
        cursor.executemany(insert_query, data)
    conn.commit()
    
    delete_query = "DELETE FROM [CF_Universal_materials_rentals_insert] WHERE TicketID = ?"
    cursor.execute(delete_query, (ticket,))
    conn.commit()
    materialDf = materialDf.dropna()
    data = materialDf[["Description", "QTY", "UNIT Price", "EXTENDED"]].values.tolist()
    data = [row + [ticket] for row in data if all(x is not None for x in row)]
    insert_query = "INSERT INTO [CF_Universal_materials_rentals_insert] (Description, QTY, UNIT_Price, EXTENDED, TicketID) VALUES (?,?,?,?,?)"
    if data:
        cursor.executemany(insert_query, data)
    conn.commit()
    
    delete_query = "DELETE FROM [CF_Universal_subcontractor_insert] WHERE TicketID = ?"
    cursor.execute(delete_query, (ticket,))
    conn.commit()
    subDf = subDf.dropna()
    data = subDf[["Description", "QTY", "UNIT Price", "EXTENDED"]].values.tolist()
    data = [row + [ticket] for row in data if all(x is not None for x in row)]
    insert_query = "INSERT INTO [CF_Universal_subcontractor_insert] (Description, QTY, UNIT_Price, EXTENDED, TicketID) VALUES (?,?,?,?,?)"
    if data:
        cursor.executemany(insert_query, data)
    conn.commit()

    cursor.close()
    conn.close()

# getBinddes("microphone")
# getPartsPrice('GILT20011 G1','GIL0001')

# getPartsPrice(partInfoDf)
