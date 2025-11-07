import pandas as pd
import pyodbc
import json
import os
import numpy as np
import re

def sanitize_input(user_input):
    if isinstance(user_input, str):
        pattern = re.compile(r"(;|'|\"|--|/\*|\*/|xp_|sp_|exec|drop|delete|insert|update|select|union|sleep|benchmark)", re.IGNORECASE)
        if pattern.search(user_input):
            raise ValueError("Potential SQL injection detected in input: " + user_input)
    return user_input

server = os.environ.get("serverGFT")
database = os.environ.get("databaseGFT")
username = os.environ.get("usernameGFT")
password = os.environ.get("passwordGFT")
SQLaddress = os.environ.get("addressGFT")
cryptToken = os.environ.get("cryptToken")

# parameter_value = "230524-0173"
# latest param 240501-0445

# params on 7/30 CircleKkeyBasic, databaseGFT, fmDashtoken1, fmDashtoken2
def getCredsToken(custnmbr):
    custnmbr = sanitize_input(custnmbr)
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    query = f"""
    DECLARE @KEY NVARCHAR(255) = '{cryptToken}';
    SELECT 
        CUSTNMBR,
        CAST(DECRYPTBYPASSPHRASE(@KEY, Token_Value) AS NVARCHAR(255)) AS Decrypted_Token_Value
    FROM [dbo].[MR_Token_Table];
    """

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    tokenDf = pd.DataFrame.from_records(results, columns=columns)

    cursor.close()
    conn.close()

    return tokenDf[tokenDf['CUSTNMBR'].astype(str).str.contains(custnmbr, na=False)]

def getBinddes(input):
    input = sanitize_input(input)
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
        
        row_df = pd.DataFrame([row_dict])
        pricingDf = pd.concat([pricingDf, row_df], ignore_index=True)
    
    cursor.close()
    conn.close()
    return pricingDf

def getAllPrice(ticketN):
    conn = None
    cursor = None

    # yymmdd - d{4}
    # yymmdd <= currentdate 
    # max of ticket num temp no set up 2000
    # First validate input is safe
    if not sanitize_input(ticketN):
        raise ValueError("Invalid characters in ticket ID")

    try:
        conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        sql_query = """Exec [CF_Univ_Quote_Ticket] @Service_TK = ?;"""
        cursor.execute(sql_query, ticketN)
        sql_query = cursor.fetchall()
        rows_transposed = [sql_query for sql_query in zip(*sql_query)]
        ticketDf = pd.DataFrame(dict(zip(["LOC_Address", "LOC_CUSTNMBR", "LOC_LOCATNNM", "LOC_ADRSCODE", "LOC_CUSTNAME", "LOC_PHONE", "CITY", "STATE", "ZIP", "Pricing_Matrix_Name", "BranchName", "CUST_NAME", "CUST_ADDRESS1", "CUST_ADDRESS2", "CUST_ADDRESS3", "CUST_CITY", "CUST_State", "CUST_Zip", "Tax_Rate", "MailDispatch", "Purchase_Order", "Bill_Customer_Number","NTE"], rows_transposed)))
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
        return ticketDf, LRatesDf, TRatesDf, misc_ops_df
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def getDesc(ticket):
    ticket = sanitize_input(ticket)
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    select_query = "Exec CF_Univ_GetWorkDescription @TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    cursor.close()
    conn.close()
    data = [list(row) for row in dataset]
    workDes = pd.DataFrame(data, columns=["Incurred", "Proposed"])
    return workDes

def getAllTicket(ticket):
    ticket = sanitize_input(ticket)
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    select_query = "Exec CF_Univ_GetWorkLabor @TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]

    ticketLaborDf = pd.DataFrame(data, columns=["Incurred/Proposed", "Description", "Nums of Techs", "Hours per Tech", "QTY", "Hourly Rate", "EXTENDED"])
    columns_to_round = ["Hourly Rate", "Hours per Tech", "EXTENDED"] 
    for column in columns_to_round:
        ticketLaborDf[column] = pd.to_numeric(ticketLaborDf[column]).round(2)
    # print(ticketLaborDf)
    select_query = "Exec CF_Univ_GetTravelLabor @TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketTripDf = pd.DataFrame(data, columns=["Incurred/Proposed", "Description", "QTY", "UNIT Price", "EXTENDED"])
    # print(ticketTripDf)
    select_query = "Exec CF_Univ_GetParts @TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketPartsDf = pd.DataFrame(data, columns=["Incurred/Proposed", "Description", "QTY", "UNIT Price", "EXTENDED"])

    select_query = "Exec CF_Univ_GetMiscCharge @TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketMiscDf = pd.DataFrame(data, columns=["Description", "QTY", "UNIT Price", "EXTENDED"])

    select_query = "SELECT Incurred, Description, QTY, CAST([UNIT_Price] AS FLOAT) AS [UNIT_Price], CAST(EXTENDED AS FLOAT) AS EXTENDED FROM [CF_Universal_materials_rentals_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketMaterialsDf = pd.DataFrame(data, columns=["Incurred/Proposed", "Description", "QTY", "UNIT Price", "EXTENDED"])

    select_query = "SELECT Description, QTY, CAST([UNIT_Price] AS FLOAT) AS [UNIT_Price], CAST(EXTENDED AS FLOAT) AS EXTENDED FROM [CF_Universal_subcontractor_insert] WHERE TicketID = ?"
    cursor.execute(select_query, (ticket,))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    ticketSubDf = pd.DataFrame(data, columns=["Description", "QTY", "UNIT Price", "EXTENDED"])

    cursor.close()
    conn.close()
    columns_to_round = ["QTY", "UNIT Price", "EXTENDED"] 
    for df in [ticketTripDf, ticketPartsDf, ticketMiscDf, ticketMaterialsDf, ticketSubDf]:
        for column in columns_to_round:
            df[column] = pd.to_numeric(df[column]).round(2)
    return ticketLaborDf, ticketTripDf, ticketPartsDf, ticketMiscDf, ticketMaterialsDf, ticketSubDf
# getAllTicket("230215-0004")
def updateAll(ticket, incurred, proposed, laborDf,  tripDf, partsDf, miscDf, materialDf, subDf):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    delete_query = "DELETE FROM [CF_Universal_workdescription_insert] WHERE TicketID = ?"
    cursor.execute(delete_query, (ticket,))
    conn.commit()
    insert_query = "INSERT INTO [CF_Universal_workdescription_insert] (TicketID, Incurred_Workdescription, Proposed_Workdescription) VALUES (?, ?, ?)"
    insert_data = [(ticket, incurred, proposed)]
    cursor.executemany(insert_query, insert_data)
    conn.commit()

    if( not laborDf.empty):
        delete_query = "DELETE FROM [CF_Universal_labor_insert] WHERE TicketID = ?"
        cursor.execute(delete_query, (ticket,))
        conn.commit()

        # laborDf = laborDf.dropna()
        laborDf["EXTENDED"] = pd.to_numeric(laborDf["EXTENDED"], errors='coerce').round(2)
        laborDf["EXTENDED"] = laborDf["EXTENDED"].replace({np.nan: None})
        data = laborDf[["Incurred/Proposed","Description", "Nums of Techs", "Hours per Tech", "QTY", "Hourly Rate", "EXTENDED"]].values.tolist()
        data = [row + [ticket] for row in data]
        insert_query = "INSERT INTO [CF_Universal_labor_insert] (Incurred, Description, Nums_of_Techs, Hours_per_Tech, QTY, Hourly_Rate, EXTENDED, TicketID) VALUES (?,?,?,?,?,?,?,?)"
        if data:
            cursor.executemany(insert_query, data)
        conn.commit()

    if( not tripDf.empty):
        delete_query = "DELETE FROM [CF_Universal_trip_charge_insert] WHERE TicketID = ?"
        cursor.execute(delete_query, (ticket,))
        conn.commit()
        tripDf = tripDf.dropna()
        data = tripDf[["Incurred/Proposed","Description", "QTY", "UNIT Price", "EXTENDED"]].values.tolist()
        data = [row + [ticket] for row in data]
        insert_query = "INSERT INTO [CF_Universal_trip_charge_insert] (Incurred, Description, QTY, UNIT_Price, EXTENDED, TicketID) VALUES (?,?,?,?,?,?)"
        if data:
            cursor.executemany(insert_query, data)
        conn.commit()

    if( not partsDf.empty):
        delete_query = "DELETE FROM [CF_Universal_parts_insert] WHERE TicketID = ?"
        cursor.execute(delete_query, (ticket,))
        conn.commit()
        partsDf = partsDf.dropna()
        data = partsDf[["Incurred/Proposed","Description", "QTY", "UNIT Price", "EXTENDED"]].values.tolist()
        data = [row + [ticket] for row in data if all(x is not None for x in row)]
        insert_query = "INSERT INTO [CF_Universal_parts_insert] (Incurred, Description, QTY, UNIT_Price, EXTENDED, TicketID) VALUES (?,?,?,?,?,?)"
        if data:
            cursor.executemany(insert_query, data)
        conn.commit()
    
    if ( not miscDf.empty):
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
    
    if ( not materialDf.empty):
        delete_query = "DELETE FROM [CF_Universal_materials_rentals_insert] WHERE TicketID = ?"
        cursor.execute(delete_query, (ticket,))
        conn.commit()
        materialDf = materialDf.dropna()
        data = materialDf[["Incurred/Proposed", "Description", "QTY", "UNIT Price", "EXTENDED"]].values.tolist()
        data = [row + [ticket] for row in data if all(x is not None for x in row)]
        insert_query = "INSERT INTO [CF_Universal_materials_rentals_insert] (Incurred, Description, QTY, UNIT_Price, EXTENDED, TicketID) VALUES (?,?,?,?,?,?)"
        if data:
            cursor.executemany(insert_query, data)
        conn.commit()
    
    if ( not subDf.empty):
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

def getBranch():
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    sql_query = '''
        SELECT DISTINCT RTrim(Wennsoft_Branch) as Wennsoft_Branch , Rtrim(BranchName) as BranchName FROM [dbo].[GFT_SV00077_Ext]
        WHERE Wennsoft_Branch <> 'Pensacola' AND BranchName NOT IN ('Pensacola', 'Corporate', 'Guardian Connect')
        '''    
    cursor.execute(sql_query)
    result = cursor.fetchall()
    rows_transposed = [result for result in zip(*result)]
    branchDf = pd.DataFrame(dict(zip(['Wennsoft_Branch', 'BranchName'], rows_transposed)))
    cursor.close()
    conn.close()
    return branchDf

def getParentByTicket(ticket):
    ticket = sanitize_input(ticket)
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    select_query = '''
        SELECT [TicketID]
               ,[Status]
               ,[NTE_QUOTE]
               ,[Editable]
               ,[Insertdate]
               ,[Approvedate]
               ,[Declinedate]
        FROM [GFT].[dbo].[CF_Universal_Quote_Parent]
        WHERE TicketID = ?
    '''
    cursor.execute(select_query, (ticket))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    parentDf = pd.DataFrame(data, columns=["TicketID", "Status", "NTE_QUOTE", "Editable", "Insertdate", "Approvedate", "Declinedate"])
    conn.close()
    # ticket_prefix, ticket_number = ticket.split('-')
    # lower_bound = int(ticket_number) - 10
    # upper_bound = int(ticket_number) + 10
    # lower_ticket = f"{ticket_prefix}-{lower_bound:04d}"
    # upper_ticket = f"{ticket_prefix}-{upper_bound:04d}"
    # if parentDf.empty:
    #     start_ticket = 173 
    #     num_rows = 10
    #     data = {
    #         'TicketID': [f'230524-{str(start_ticket + i).zfill(4)}' for i in range(num_rows)],
    #         'Status': ['Open', 'Closed', 'Pending', 'Closed', 'Open', 'Pending', 'Closed', 'Open', 'Pending', 'Closed'],
    #         'NTE_QUOTE': [random.randint(0, 1) for _ in range(num_rows)],
    #         'Editable': [random.randint(0, 1) for _ in range(num_rows)],
    #         'Insertdate': [datetime(2023, 8, 15), datetime(2023, 8, 10), datetime(2023, 8, 20), datetime(2023, 8, 25),
    #                     datetime(2023, 8, 5), datetime(2023, 8, 18), datetime(2023, 8, 12), datetime(2023, 8, 22),
    #                     datetime(2023, 8, 8), datetime(2023, 8, 28)],
    #         'Approvedate': [datetime(2023, 8, 14), datetime(2023, 8, 9), datetime(2023, 8, 19), datetime(2023, 8, 24),
    #                         datetime(2023, 8, 4), datetime(2023, 8, 17), datetime(2023, 8, 11), datetime(2023, 8, 21),
    #                         datetime(2023, 8, 7), datetime(2023, 8, 27)],
    #         'Declinedate': [datetime(2023, 8, 13), datetime(2023, 8, 8), datetime(2023, 8, 18), datetime(2023, 8, 23),
    #                         datetime(2023, 8, 3), datetime(2023, 8, 16), datetime(2023, 8, 10), datetime(2023, 8, 20),
    #                         datetime(2023, 8, 6), datetime(2023, 8, 26)],
    #     }
    #     parentDf = pd.DataFrame(data)
    return parentDf
def getParent(branchName):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    select_query = '''
       SELECT [TicketID]
            ,[Status]
            ,[NTE_QUOTE]
            ,[Editable]
            ,[Insertdate]
            ,[Approvedate]
            ,[Declinedate]
        FROM [GFT].[dbo].[CF_Universal_Quote_Parent]
        WHERE BranchName IN ({})
        ORDER BY
        COALESCE([Approvedate], [Declinedate]) DESC
        OFFSET 0 ROWS
        FETCH NEXT 10 ROWS ONLY;
    '''.format(', '.join(['?'] * len(branchName)))
    
    cursor.execute(select_query, branchName)
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    parentDf = pd.DataFrame(data, columns=["TicketID", "Status", "NTE_QUOTE", "Editable", "Insertdate", "Approvedate", "Declinedate"])
    mapping = {1: 'QUOTE', 3: 'NTE'}
    parentDf['NTE_QUOTE'] = parentDf['NTE_QUOTE'].replace(mapping)
    conn.close()
    return parentDf
# •	Ability to attach PDF to ticket in GP (open to discussion My suggestion is to also store it in parent table)
def updateParent(ticket, editable, ntequote, savetime, approved, declined, branchname, button):
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    if(ntequote=="NTE"):
        ntequote = 3
    else:
        ntequote = 1

    select_query = '''
        SELECT *
        FROM [GFT].[dbo].[CF_Universal_Quote_Parent]
        WHERE TicketID = ?
    '''
    cursor.execute(select_query, (ticket,))
    firstdata = cursor.fetchall()
    if button == "save":
        if not firstdata:
            insert_query = '''INSERT INTO [GFT].[dbo].[CF_Universal_Quote_Parent] (
            TicketID, Status
            ,NTE_QUOTE
            ,Editable
            ,Insertdate
            ,Approvedate,Declinedate, BranchName) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
            cursor.execute(insert_query, (ticket, "Pending", ntequote, 1, savetime, "1900-01-01 00:00:00.000", "1900-01-01 00:00:00.000", branchname))
            conn.commit()
        else:
            update_query = '''
                    UPDATE [GFT].[dbo].[CF_Universal_Quote_Parent]
                    SET Status = ?, NTE_QUOTE = ?, Editable = ?, BranchName = ?
                    WHERE TicketID = ? 
                '''
            cursor.execute(update_query, ("Pending", ntequote, 1, branchname, ticket))
            conn.commit()
    if button == "decline":
        if not firstdata:
            insert_query = '''INSERT INTO [GFT].[dbo].[CF_Universal_Quote_Parent] (
            TicketID, Status
            ,NTE_QUOTE
            ,Editable
            ,Insertdate
            ,Approvedate,Declinedate, BranchName) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
            cursor.execute(insert_query, (ticket, "Declined", ntequote, 1, declined, "1900-01-01 00:00:00.000", declined, branchname))
            conn.commit()
        else:
            insert_query = '''UPDATE [GFT].[dbo].[CF_Universal_Quote_Parent]
            SET Status = ?, NTE_QUOTE = ?, Editable = ?, Declinedate = ?
            WHERE TicketID = ? '''
            cursor.execute(insert_query, ("Declined", ntequote, 1, declined, ticket))
            conn.commit()
    if button == "approve":
        if not firstdata:
            insert_query = '''INSERT INTO [GFT].[dbo].[CF_Universal_Quote_Parent] (
            TicketID, Status
            ,NTE_QUOTE
            ,Editable
            ,Insertdate
            ,Approvedate,Declinedate, BranchName) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
            cursor.execute(insert_query, (ticket, "Approved", ntequote, 0, approved, approved, "1900-01-01 00:00:00.000", branchname))
            conn.commit()
        else:
            insert_query = '''UPDATE [GFT].[dbo].[CF_Universal_Quote_Parent]
            SET Status = ?, NTE_QUOTE = ?, Editable = ?, Approvedate = ?
            WHERE TicketID = ? '''
            cursor.execute(insert_query, ("Approved", ntequote, 0, approved, ticket))
            conn.commit()
    
    cursor.close()
    conn.close()

def getVerisaeCreds(ticket):
    ticket = sanitize_input(ticket)
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    select_query = '''EXEC [GFT].[dbo].[MR_Univ_User_Info] @ticket_no = ?'''
    cursor.execute(select_query, (ticket))
    dataset = cursor.fetchall()
    data = [list(row) for row in dataset]
    credsDf = pd.DataFrame(data, columns=["Purchase_Order", "Divisions", "Username", "Password"])
    conn.close()
    return (credsDf["Username"], credsDf["Password"])

# def execute_stored_procedure(ticket_id):
#     """Function to execute the stored procedure."""
#     # Establish connection
#     conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
#     conn = pyodbc.connect(conn_str)
#     cursor = conn.cursor()
#     ticket_id = ticket_id.ljust(15)
#     sql = """
#     DECLARE @TicketID CHAR(17) = ?;
#     EXEC sp_executesql N'EXEC [GFT].[dbo].[CF_SP_Delete_UnvQuotTbles] @TicketID = @P1',
#                     N'@P1 CHAR(17)', @P1 = @TicketID;
#     """

#     # Execute the SQL
#     cursor.execute(sql, ticket_id)
#     conn.commit()
# execute_stored_procedure("240630-0027")

def deleteTicket(ticket):
    ticket = sanitize_input(ticket)
    conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    ticket = ticket.ljust(15)
    query = '''
        DECLARE @TicketID CHAR(17) = ?;
        EXEC sp_executesql N'EXEC [GFT].[dbo].[CF_SP_Delete_UnvQuotTbles] @TicketID = @P1',
                           N'@P1 CHAR(17)', @P1 = @TicketID;
    '''
    cursor.execute(query, ticket)
    # print(query, (ticket), conn_str)
    # dataset = cursor.fetchall()
    conn.commit()
    conn.close()
# deleteTicket("240630-0027")

# def getFmDashCreds():
#     conn_str = f"DRIVER={SQLaddress};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
#     conn = pyodbc.connect(conn_str)
#     cursor = conn.cursor()
    
#     select_query = '''EXEC [GFT].[dbo].[MR_Univ_User_Info] @ticket_no = ?'''
#     cursor.execute(select_query, (ticket))
#     dataset = cursor.fetchall()
#     data = [list(row) for row in dataset]
#     credsDf = pd.DataFrame(data, columns=["Purchase_Order", "AppointmentID", "Divisions", "Username", "Password"])
#     conn.close()
#     return (credsDf["Username"], credsDf["Password"])



# gilgil
import pandas as pd
import pyodbc
import json
import os
from datetime import datetime, timedelta
import time
import numpy as np
from io import StringIO
import pyodbc

server = os.environ.get("serverGFT")
database = os.environ.get("databaseGFT")
username = os.environ.get("usernameGFT")
password = os.environ.get("passwordGFT")
SQLaddress = os.environ.get("addressGFT")
conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
current_date = datetime.now()
current_date = current_date.strftime('%Y-%m-%d')

def getCredsToken(custnmbr):
    query = f"""
    DECLARE @KEY NVARCHAR(255) = 'MyS3cur3P@ssw0rd!';
    SELECT 
        CUSTNMBR,
        CUSTNAME,
        CAST(DECRYPTBYPASSPHRASE(@KEY, Token_Value) AS NVARCHAR(255)) AS Decrypted_Token_Value
    FROM [dbo].[MR_Token_Table];
    """
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    tokenDf = pd.DataFrame.from_records(results, columns=columns)

    cursor.close()
    conn.close()

    return tokenDf[tokenDf['CUSTNMBR'].astype(str).str.contains(custnmbr, na=False)]

def insertCommPayment(df, printQuery = False):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = '''INSERT INTO [dbo].[CF_T_GVR_Comm_Payment] (
                    [ASC],
                    [DateExecution],
                    [Incident],
                    [Commission],
                    [Approve_Date],
                    [Payment_Amt],
                    [Check],
                    [Check_Date],
                    [CB1],
                    [CB2],
                    [CB3]
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        for index, row in df.iterrows():
            if printQuery:
                print(query, (
                    row['ASC'],
                    row['DateExecution'],
                    row['Incident'],
                    row['Commission'],
                    row['Approve Date'],
                    row['Payment Amt'],
                    row['Check'],
                    row['Check Date'],
                    0,0,0))
            cursor.execute(query, (
                row['ASC'],
                row['DateExecution'],
                row['Incident'],
                row['Commission'],
                row['Approve Date'],
                row['Payment Amt'],
                row['Check'],
                row['Check Date'],
                0,0,0
            ))
            
        conn.commit()
        print("Data inserted successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            

def selectCommPayment():
    select_query = '''SELECT * FROM [dbo].[CF_T_GVR_Comm_Payment]'''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(select_query)
        rows = cursor.fetchall()
        
        if not rows:
            print("The table is empty.")
        else:
            for row in rows:
                print(row)
        print(cursor.description)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def selectByDateCommPayment(exec_date: str):
    """
    Fetch rows from CF_T_GVR_Comm_Payment where DateExecution = exec_date.
    exec_date should be a string in 'YYYY-MM-DD' format.
    """
    select_query = '''
        SELECT * 
        FROM [dbo].[CF_T_GVR_Comm_Payment]
        WHERE [DateExecution] = ?
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(select_query, (exec_date,))
        rows = cursor.fetchall()
        
        if not rows:
            return []
        else:
            col_names = [desc[0] for desc in cursor.description]
            return [dict(zip(col_names, row)) for row in rows] 

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def deleteCommPayment():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        delete_query = '''DELETE FROM [dbo].[CF_T_GVR_Comm_Payment]'''
        cursor.execute(delete_query)
        conn.commit()
        print("All records deleted successfully.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# WarrPay
def insertWarrPayment(df, printQuery = False):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = '''INSERT INTO [dbo].[CF_T_GVR_Warr_Payment] (
                    [ASC],
                    [DateExecution],
                    [Incident],
                    [Close_Date],
                    [D_A],
                    [Expense],
                    [Miles],
                    [Cost],
                    [Travel_Time],
                    [Travel_Cost],
                    [Labor_Hours],
                    [Labor_Cost],
                    [Check],
                    [Check_Date],
                    [Total_Amount],
                    [CB1],
                    [CB2],
                    [CB3]
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

        for index, row in df.iterrows():
            if printQuery:
                print(query, (
                    row['ASC'],
                    row['DateExecution'],
                    row['Incident'],
                    row['Close Date'],
                    row['D/A'],
                    row['Expense'],
                    row['Miles'],
                    row['Cost'],
                    row['Travel Time'],
                    row['Travel Cost'],
                    row['Labor Hours'],
                    row['Labor Cost'],
                    row['Check'],
                    row['Check Date'],
                    row['Total Amount'],0,0,0
                ))
            cursor.execute(query, (
                row['ASC'],
                row['DateExecution'],
                row['Incident'],
                row['Close Date'],
                row['D/A'],
                row['Expense'],
                row['Miles'],
                row['Cost'],
                row['Travel Time'],
                row['Travel Cost'],
                row['Labor Hours'],
                row['Labor Cost'],
                row['Check'],
                row['Check Date'],
                row['Total Amount'],0,0,0
            ))
        
        conn.commit()
        print("Data inserted successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def selectWarrPayment():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        select_query = '''SELECT * FROM [dbo].[CF_T_GVR_Warr_Payment]'''
        cursor.execute(select_query)
        rows = cursor.fetchall()
        
        if not rows:
            print("The table is empty.")
        else:
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def selectByDateWarrPayment(exec_date: str):
    """
    Fetch rows from CF_T_GVR_Comm_Payment where DateExecution = exec_date.
    exec_date should be a string in 'YYYY-MM-DD' format.
    """
    select_query = '''
        SELECT * 
        FROM [dbo].[CF_T_GVR_Warr_Payment]
        WHERE [DateExecution] = ?
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(select_query, (exec_date,))
        rows = cursor.fetchall()
        if not rows:
            return []
        else:
            col_names = [desc[0] for desc in cursor.description]
            return [dict(zip(col_names, row)) for row in rows] 

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def deleteWarrPayment():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        select_query = '''SELECT * FROM [dbo].[CF_T_GVR_Warr_Payment]'''
        cursor.execute(select_query)
        rows = cursor.fetchall()
        
        if not rows:
            print("The table is empty.")
        else:
            for row in rows:
                print(row)
                
        delete_query = '''DELETE FROM [dbo].[CF_T_GVR_Warr_Payment]'''
        cursor.execute(delete_query)
        conn.commit()
        print("All records deleted successfully.")
        
        select_query = '''SELECT * FROM [dbo].[CF_T_GVR_Warr_Payment]'''
        cursor.execute(select_query)
        rows = cursor.fetchall()
        
        if not rows:
            print("The table is empty.")
        else:
            for row in rows:
                print(row)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def staticData():
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    csv_data = """
    ASC,DateExecution,Incident,Commission,Approve Date,Payment Amt,Check,Check Date
    0001846782,2024-05-21,15141068,15141068,05/20/2024,$800.00,,
    0001846806,2024-05-21,15140387,15140387,05/20/2024,$875.00,,
    """
    df = pd.read_csv(StringIO(csv_data))
    df = df.replace({np.nan: None})
    insertCommPayment(df, printQuery = False)
    deleteCommPayment()
    csv_data="""ASC,DateExecution,Incident,Close Date,D/A,Expense,Miles,Cost,Travel Time,Travel Cost,Labor Hours,Labor Cost,Check,Check Date,Total Amount
    0001745226,2024-05-21,14938919,05/20/2024,$0.00,$12.30,55,$40.70,1.00,$91.00,1.00,$91.00,,,$235.00
    0001745226,2024-05-21,14938989,05/20/2024,$0.00,$171.05,80,$59.20,1.25,$113.75,1.00,$91.00,,,$435.00
    0001745226,2024-05-21,14938990,05/20/2024,$0.00,$10.44,119,$88.06,0.00,$0.00,1.50,$136.50,,,$235.00
    0001745226,2024-05-21,14938941,05/20/2024,$0.00,$10.82,57,$42.18,1.00,$91.00,1.00,$91.00,,,$235.00
    0001745226,2024-05-21,15120024,05/20/2024,$139.93,$10.00,85,$62.90,1.50,$136.50,1.00,$91.00,,,$440.33
    0001745226,2024-05-21,15126319,05/20/2024,$18.16,$10.00,30,$22.20,0.75,$68.25,1.25,$113.75,,,$232.36"""

    df = pd.read_csv(StringIO(csv_data)) 
    df = df.replace({np.nan: None})
    insertWarrPayment(df, printQuery = False)
    deleteWarrPayment()

def selectFmdash():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        exe_query = '''EXEC [dbo].[MR_INV_FMDASH] ? , ?'''
        # cursor.execute(exe_query, ('2024-06-18 00:00:00.000', 'MJJUN061824-MAJ'))
        cursor.execute(exe_query, ('2024-06-17 00:00:00.000', 'CDJUN061724-MJ2'))
        rows = cursor.fetchall()
        
        
        if not rows:
            print("The table is empty.")
        else:
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def insertAuditLog(status, table_name, record_count, timestamp=None, printQuery=False):
    """
    Insert an audit log record into [dbo].[CF_T_GVR_AuditLog].
    
    :param status: str - status text (e.g. 'SUCCESS', 'FAILED')
    :param table_name: str - table name where records were inserted
    :param record_count: int - number of records affected
    :param timestamp: datetime or None (default now)
    :param printQuery: bool - print the query and values
    """
    try:
        if timestamp is None:
            timestamp = datetime.now()

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        sql = """
            INSERT INTO [dbo].[CF_T_GVR_AuditLog]
            ([Status], [TableName], [RecordCount], [TimeStamp])
            VALUES (?, ?, ?, ?)
        """

        values = (status, table_name, record_count, timestamp)
        cursor.execute(sql, values)
        conn.commit()
        print("Audit log inserted successfully.")

    except Exception as e:
        print(f"[insertAuditLog] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def selectAuditLog(limit=50, printQuery=False):
    """
    Select the most recent audit log records from [dbo].[CF_T_GVR_AuditLog].

    :param limit: int - number of rows to return (default 50)
    :return: list of rows (each row is a tuple)
    """
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = f'''
            SELECT TOP {limit} [Status], [Timestamp], [TableInserted], [RecordCount]
            FROM [dbo].[CF_T_GVR_AuditLog]
            ORDER BY [Timestamp] DESC
        '''

        if printQuery:
            print(query)

        cursor.execute(query)
        rows = cursor.fetchall()

        # Print nicely
        for row in rows:
            print(row)

        return rows

    except Exception as e:
        print(f"[selectAuditLog] Error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

# print(selectAuditLog())
# staticData()
# deleteWarrPayment()
# deleteCommPayment()
# print("comm:")
# print(selectCommPayment())
# print("warr:")
# print(selectWarrPayment())
# print("comm", current_date)
# print(len(selectByDateCommPayment(current_date)))
# print("warr", current_date)
# print(len(selectByDateWarrPayment(current_date)))
# print("fmdash")
# selectFmdash()
# selectByDateCommPaymentDev(current_date)


# //// DEV
# ================================================================
# 🟢 COMM PAYMENT DEV FUNCTIONS
# ================================================================
def insertCommPaymentDev(df, printQuery=False):
    query = '''
        INSERT INTO [dbo].[CF_T_GVR_Comm_Payment_DEV] (
            [ASC], [DateExecution], [Incident], [Commission],
            [Approve_Date], [Payment_Amt], [Check],
            [Check_Date], [CB1], [CB2], [CB3]
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            vals = (
                row.get("ASC"),
                row.get("DateExecution"),
                row.get("Incident"),
                row.get("Commission"),
                row.get("Approve Date"),
                row.get("Payment Amt"),
                row.get("Check"),
                row.get("Check Date"),
                0, 0, 0
            )
            if printQuery:
                print(query, vals)
            cursor.execute(query, vals)
        conn.commit()
        print("✅ Data inserted into CF_T_GVR_Comm_Payment_DEV successfully.")
    except Exception as e:
        print(f"[insertCommPaymentDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def selectCommPaymentDev():
    query = '''SELECT * FROM [dbo].[CF_T_GVR_Comm_Payment_DEV]'''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("ℹ️ Table CF_T_GVR_Comm_Payment_DEV is empty.")
            return []
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print(f"[selectCommPaymentDev] Error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def selectByDateCommPaymentDev(exec_date: str):
    query = '''
        SELECT * FROM [dbo].[CF_T_GVR_Comm_Payment_DEV]
        WHERE [DateExecution] = ?
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query, (exec_date,))
        rows = cursor.fetchall()
        if not rows:
            return []
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print(f"[selectByDateCommPaymentDev] Error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def deleteCommPaymentDev():
    query = 'DELETE FROM [dbo].[CF_T_GVR_Comm_Payment_DEV]'
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        print(f"🗑️ Deleted {cursor.rowcount} record(s) from CF_T_GVR_Comm_Payment_DEV.")
    except Exception as e:
        print(f"[deleteCommPaymentDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def deleteCommPaymentByDateDev(exec_date: str):
    query = '''
        DELETE FROM [dbo].[CF_T_GVR_Comm_Payment_DEV]
        WHERE [DateExecution] = ?
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query, (exec_date,))
        conn.commit()
        print(f"🗑️ Deleted {cursor.rowcount} records for {exec_date} from Comm_Payment_DEV.")
    except Exception as e:
        print(f"[deleteCommPaymentByDateDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


# ================================================================
# 🟢 WARRANT PAYMENT DEV FUNCTIONS
# ================================================================
def insertWarrPaymentDev(df, printQuery=False):
    query = '''
        INSERT INTO [dbo].[CF_T_GVR_Warr_Payment_DEV] (
            [ASC],[DateExecution],[Incident],[Close_Date],
            [D_A],[Expense],[Miles],[Cost],[Travel_Time],
            [Travel_Cost],[Labor_Hours],[Labor_Cost],
            [Check],[Check_Date],[Total_Amount],[CB1],[CB2],[CB3]
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            vals = (
                row["ASC"], row["DateExecution"], row["Incident"], row["Close Date"],
                row["D/A"], row["Expense"], row["Miles"], row["Cost"],
                row["Travel Time"], row["Travel Cost"], row["Labor Hours"], row["Labor Cost"],
                row["Check"], row["Check Date"], row["Total Amount"], 0, 0, 0
            )
            if printQuery:
                print(query, vals)
            cursor.execute(query, vals)
        conn.commit()
        print("✅ Data inserted into CF_T_GVR_Warr_Payment_DEV successfully.")
    except Exception as e:
        print(f"[insertWarrPaymentDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def selectWarrPaymentDev():
    query = '''SELECT * FROM [dbo].[CF_T_GVR_Warr_Payment_DEV]'''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("ℹ️ Table CF_T_GVR_Warr_Payment_DEV is empty.")
            return []
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print(f"[selectWarrPaymentDev] Error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def selectByDateWarrPaymentDev(exec_date: str):
    query = '''
        SELECT * FROM [dbo].[CF_T_GVR_Warr_Payment_DEV]
        WHERE [DateExecution] = ?
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query, (exec_date,))
        rows = cursor.fetchall()
        if not rows:
            return []
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print(f"[selectByDateWarrPaymentDev] Error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def deleteWarrPaymentDev():
    query = 'DELETE FROM [dbo].[CF_T_GVR_Warr_Payment_DEV]'
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        print(f"🗑️ Deleted {cursor.rowcount} record(s) from CF_T_GVR_Warr_Payment_DEV.")
    except Exception as e:
        print(f"[deleteWarrPaymentDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def deleteWarrPaymentByDateDev(exec_date: str):
    query = '''
        DELETE FROM [dbo].[CF_T_GVR_Warr_Payment_DEV]
        WHERE [DateExecution] = ?
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query, (exec_date,))
        conn.commit()
        print(f"🗑️ Deleted {cursor.rowcount} record(s) for {exec_date} from Warr_Payment_DEV.")
    except Exception as e:
        print(f"[deleteWarrPaymentByDateDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


# ================================================================
# 🟢 AUDIT LOG DEV FUNCTIONS
# ================================================================
def insertAuditLogDev(status, table_name, record_count, notes="", timestamp=None, printQuery=False):
    """
    Inserts a log into CF_T_GVR_AuditLog_DEV including the terminal (cwd) location.
    """
    query = '''
        INSERT INTO [dbo].[CF_T_GVR_AuditLog_DEV] 
        ([Status],[Timestamp],[TableInserted],[NOTES],[RecordCount])
        VALUES (?, ?, ?, ?, ?)
    '''

    # auto-detect current working directory (terminal location)
    place = os.getcwd()
    ts = timestamp or datetime.now()
    note_text = f"[{place}] {notes}" if notes else place

    vals = (status, ts, table_name, note_text, record_count)
    print(vals)

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        if printQuery:
            print(query, vals)
        cursor.execute(query, vals)
        conn.commit()
        print("✅ AuditLog entry inserted successfully.")
    except Exception as e:
        print(f"[insertAuditLogDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def selectAuditLogDev(limit=50, save_json=True, output_dir="audit_logs"):
    """
    Fetch latest audit logs from CF_T_GVR_AuditLog_DEV,
    pretty-print them, and optionally save as JSON.
    """
    query = f'''
        SELECT * 
        FROM [dbo].[CF_T_GVR_AuditLog_DEV]
        ORDER BY [Timestamp] DESC
    '''
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        data = [dict(zip(cols, row)) for row in rows]

        # ✅ Pretty-print to console
        print("\n📋 --- Latest Audit Logs ---")
        for i, entry in enumerate(data, start=1):
            print(f"\n🔹 Log #{i}")
            for k, v in entry.items():
                print(f"   {k}: {v}")

        # ✅ Optionally save to JSON file
        if save_json:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(output_dir, f"audit_log_DEV_{timestamp}.json")

            # Convert datetimes to strings for JSON compatibility
            def default_serializer(obj):
                if isinstance(obj, (datetime, )):
                    return obj.isoformat()
                return str(obj)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4, default=default_serializer)

            print(f"\n💾 Logs saved to: {file_path}\n")

        return data

    except Exception as e:
        print(f"[selectAuditLogDev] Error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def deleteAuditLogDev(before_date=None, status=None, printQuery=False):
    where_clauses, params = [], []
    if before_date:
        where_clauses.append("[Timestamp] < ?")
        params.append(before_date)
    if status:
        where_clauses.append("[Status] = ?")
        params.append(status)
    if not where_clauses:
        print("⚠️ No filters specified. Use deleteAllNotesDev() for full wipe.")
        return
    where_sql = " AND ".join(where_clauses)
    query = f"DELETE FROM [dbo].[CF_T_GVR_AuditLog_DEV] WHERE {where_sql}"
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        if printQuery:
            print(query, params)
        cursor.execute(query, tuple(params))
        conn.commit()
        print(f"🗑️ Deleted {cursor.rowcount} record(s) from AuditLog_DEV.")
    except Exception as e:
        print(f"[deleteAuditLogDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def deleteAllNotesDev():
    """⚠️ Deletes ALL records from CF_T_GVR_AuditLog_DEV — irreversible."""
    query = 'DELETE FROM [dbo].[CF_T_GVR_AuditLog_DEV]'
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        print(f"🚨 Fully cleared CF_T_GVR_AuditLog_DEV ({cursor.rowcount} records deleted).")
    except Exception as e:
        print(f"[deleteAllNotesDev] Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


# ================================================================
# 🧪 SAMPLE DATAFRAME DEV TESTS
# ================================================================
comm_df = pd.DataFrame([
    {"ASC": "0001846017", "DateExecution": '2025-10-07',
        "Incident": "14578887", "Commission": 0, "Approve Date": "01/03/2024",
        "Payment Amt": 1930, "Check": "CHK-001", "Check Date": "01/29/2024"}
])

warr_df = pd.DataFrame([
    {"ASC": "199808", "DateExecution": "2025-10-07",
        "Incident": "INC12345", "Close Date": "2025-10-03", "D/A": "D",
        "Expense": 150.75, "Miles": 32.5, "Cost": 450.0, "Travel Time": 1.5,
        "Travel Cost": 75.0, "Labor Hours": 3.0, "Labor Cost": 180.0,
        "Check": "CHK9876", "Check Date": "2025-10-03", "Total Amount": 705.75}
])

# insertCommPaymentDev(comm_df, printQuery=True)
# insertAuditLogDev("SUCCESS", "CF_T_GVR_Comm_Payment_DEV", 1, "github container devop insert complete")
# print(selectCommPaymentDev())
# insertWarrPaymentDev(warr_df, printQuery=True)
# insertAuditLogDev("SUCCESS", "CF_T_GVR_Warr_Payment_DEV", 1, "Test insert complete")
# print(selectWarrPaymentDev())
# print(len(selectByDateCommPaymentDev(current_date))+len(selectByDateWarrPaymentDev(current_date)))


# print(selectAuditLogDev())
# print(selectCommPaymentDev())
# print(len(selectByDateCommPaymentDev(current_date))+len(selectByDateWarrPaymentDev(current_date)))
# deleteCommPaymentByDateDev(current_date)
# deleteWarrPaymentByDateDev(current_date)

# deleteWarrPaymentDev()
# deleteCommPaymentDev()
# deleteAllNotesDev()