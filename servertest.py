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
        print(ticketDf)
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
