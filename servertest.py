import pandas as pd
import pyodbc
import json
import os

server = os.environ.get("serverGFT")
database = os.environ.get("databaseGFT")
username = os.environ.get("usernameGFT")
password = os.environ.get("passwordGFT")
parameter_value = "230524-0173"

def getPricing(ticketN):
    conn_str = f"DRIVER={{/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.2.so.1.1}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = """Exec [CF_Univ_Quote_Pricing] @Service_TK = ?;"""

    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()
    # expected_columns = 5
    # print(sql_query)
    # if len(sql_query[0]) != expected_columns:
    #     raise ValueError(f"Expected {expected_columns} columns, but received {len(sql_query[0])} columns from the SQL query.")

    rows_transposed = [sql_query for sql_query in zip(*sql_query)]

    df = pd.DataFrame(dict(zip(['ITEMNMBR', 'ITEMDESC', 'SellingPrice', 'Cost', 'CUSTNMBR'], rows_transposed)))
    cursor.close()
    conn.close()
    return df

def getTicketInfo(ticketN):
    conn_str = f"DRIVER={{/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.2.so.1.1}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = """Exec [CF_Univ_Quote_Ticket] @Service_TK = ?;"""

    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()

    rows_transposed = [sql_query for sql_query in zip(*sql_query)]

    df = pd.DataFrame(dict(zip([
    "LOC_Address", "LOC_CUSTNMBR", "LOC_LOCATNNM", "LOC_ADRSCODE", "LOC_CUSTNAME", "LOC_PHONE", "CITY", "STATE", "ZIP", "Pricing_Matrix_Name", "Divisions", "CUST_NAME", "CUST_ADDRESS1", "CUST_ADDRESS2", "CUST_ADDRESS3", "CUST_CITY", "CUST_State", "CUST_Zip", "Tax_Rate", "MailDispatch", "Purchase_Order", "Tax_Rate"], rows_transposed)))
    cursor.close()
    conn.close()
    return df

def getLRates(ticketN):
    conn_str = f"DRIVER={{/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.2.so.1.1}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = """Exec [CF_Univ_Quote_LRates] @Service_TK = ?;"""

    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()
    rows_transposed = [sql_query for sql_query in zip(*sql_query)]

    df = pd.DataFrame(dict(zip([
    "Billing_Amount", "Pay_Code_Description"], rows_transposed)))
    # df.to_json('LRates.json', orient='records', indent=4)
    
    cursor.close()
    conn.close()
    return df

def getTRates(ticketN):
    conn_str = f"DRIVER={{/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.2.so.1.1}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = """Exec [CF_Univ_Quote_TRates] @Service_TK = ?;"""

    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()

    rows_transposed = [sql_query for sql_query in zip(*sql_query)]

    df = pd.DataFrame(dict(zip([
    "Billing_Amount", "Pay_Code_Description"], rows_transposed)))
    
    cursor.close()
    conn.close()
    return df

def getTicketprice(ticketN):
    conn_str = f"DRIVER={{/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.2.so.1.1}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = """Exec [CF_Univ_Quote_Pricing] @Service_TK = ?;"""

    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()

    rows_transposed = [sql_query for sql_query in zip(*sql_query)]

    df = pd.DataFrame(dict(zip([
    "Billing_Amount", "Pay_Code_Description"], rows_transposed)))
    json_data = df.to_json(orient='records')

    with open(f"{str(parameter_value)}.json", 'w') as file:
        file.write(json_data)
        
    cursor.close()
    conn.close()

    # data_str = '\n'.join('\t'.join(map(str, row)) for row in sql_query)

    # # Save the data as a text file
    # with open('data.txt', 'w') as file:
    #     file.write(data_str)
    # return df

def getMisc(ticketN):
    conn_str = f"DRIVER={{/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.2.so.1.1}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = """Exec [CF_Univ_Quote_Fees] @Service_TK = ?;"""

    cursor.execute(sql_query, ticketN)
    sql_query = cursor.fetchall()
    rows_transposed = [sql_query for sql_query in zip(*sql_query)]

    df = pd.DataFrame(dict(zip([
    "Fee_Charge_Type", "Fee_Amount"], rows_transposed)))
    # df.to_json('Misc.json', orient='records', indent=4)
    
    cursor.close()
    conn.close()
    return df
