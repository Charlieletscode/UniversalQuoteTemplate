import streamlit as st
import subprocess
import sys
import pandas as pd
from streamlit.web import cli as stcli
import os
import webbrowser
import requests
from PIL import Image
import io
import base64
import random
import time
from io import BytesIO
from __init__ import *
from reportlab.lib.pagesizes import letter
from servertest import getCredsToken
from servertest import getAllPrice
from servertest import updateAll
from servertest import getAllTicket
from servertest import getDesc
from servertest import getBinddes
from servertest import getPartsPrice
from servertest import getBranch
from servertest import getParent
from servertest import updateParent
from servertest import getParentByTicket
from servertest import deleteTicket
from datetime import datetime
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import red, black
from reportlab.platypus import Paragraph
import numpy as np
import re
from api.fmDash import submitFmQuotes
from api.fmDash import checkout
from api.fmDash import submitFmQuotesDev
from api.fmDash import devCheckout
from api.verisae import submitQuoteVerisae
from api.circleK import circleK_wo_cost_information
from reportlab.graphics.renderPM import PMCanvas
from decimal import Decimal
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
registerFont(TTFont('Arial','arial.ttf'))

current_date = datetime.now()
formatted_date = current_date.strftime("%m/%d/%Y")
if "show" not in st.session_state:
    st.session_state.show = False
if "ticketN" not in st.session_state:
    st.session_state.ticketN = None
if "pricingDf" not in st.session_state:
    st.session_state.pricingDf = None
if "ticketDf" not in st.session_state:
    st.session_state.ticketDf = None
if "TRatesDf" not in st.session_state:
    st.session_state.TRatesDf = None
if "LRatesDf" not in st.session_state:
    st.session_state.LRatesDf = None
if "misc_ops_df" not in st.session_state:
    st.session_state.misc_ops_df = None
if "edit" not in st.session_state:
    st.session_state.edit = None
if "workDescription" not in st.session_state:
    st.session_state.workDescription = ""
if "NTE_Quote" not in st.session_state:
    st.session_state.NTE_Quote = ""
if "editable" not in st.session_state:
    st.session_state.editable = None
if "refresh_button" not in st.session_state:
    st.session_state.refresh_button = None
if "workDesDf" not in st.session_state:
    st.session_state.workDesDf = None
if 'selected_branches' not in st.session_state:
    st.session_state.selected_branches = []
if "branch" not in st.session_state:
    st.session_state.branch = getBranch()
if "parentDf" not in st.session_state:
    st.session_state.parentDf = getBranch()
if 'expand_collapse_state' not in st.session_state:
    st.session_state.expand_collapse_state = False
if 'prev_input_letters' not in st.session_state:
    st.session_state.prev_input_letters = ""
if "pdf_open" not in st.session_state:
    st.session_state.pdf_open = False
# if 'filtered_ticket' not in st.session_state:
#     st.session_state.filtered_ticket = [event for event in st.session_state.filtered_ticket if event['BranchShortName'] in st.session_state.selected_branches]

def changePdfStatus():
    st.session_state.pdf_open = not st.session_state.pdf_open

def changeEditStatus():
    st.session_state.edit = not st.session_state.edit

def changeExpandStatus():
    st.session_state.expand_collapse_state = not st.session_state.expand_collapse_state

def refresh():
    st.session_state.ticketN = ""
    state_variables = [
        "ticketN",
        "pricingDf",
        "ticketDf",
        "TRatesDf",
        "LRatesDf",
        "misc_ops_df",
        "edit",
        "workDescription",
        "NTE_Quote",
        "editable",
        "refresh_button",
        "workDesDf",
        "parentDf",
        "prev_input_letters",
        "temp_parts_df"
    ]
    for var_name in state_variables:
        st.session_state[var_name] = None
    st.session_state.edit = False
    # st.experimental_set_query_params()
    st.rerun()

@st.dialog("DeleteTicket")
def deleteTicketDiaglog(ticket):
    st.write(f"Click to delete {ticket} (double confirmation)")
    # reason = st.text_input("Because...")
    confirm_col, cancel_col = st.columns(2)
    if confirm_col.button("Confirm Delete", key="confirm"):
        deleteTicket(ticket)
        # print("Item deleted successfully.")
        time.sleep(2)  
        refresh()  
    elif cancel_col.button("Cancel", key="cancel"):
        # print("Deletion canceled.")
        st.rerun()

def mainPage():        
    if "labor_df" not in st.session_state:
        st.session_state.labor_df = pd.DataFrame()
        st.session_state.trip_charge_df = pd.DataFrame()
        st.session_state.parts_df = pd.DataFrame()
        st.session_state.temp_parts_df = pd.DataFrame()
        st.session_state.miscellaneous_charges_df = pd.DataFrame()
        st.session_state.materials_non_stock_and_rentals_df = pd.DataFrame()
        st.session_state.subcontractor_df = pd.DataFrame()
    
    script_directory = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_directory, "Header.jpg")
    image = Image.open(image_path)
    image_height = 200
    resized_image = image.resize((int(image_height * image.width / image.height), image_height))
    # try:
    if 'ticketN' in st.session_state and st.session_state.ticketN:
        st.image(resized_image, width=400)
        if st.session_state.ticketDf is None:
            # st.session_state.refresh_button = False
            st.session_state.ticketDf, st.session_state.LRatesDf, st.session_state.TRatesDf, st.session_state.misc_ops_df = getAllPrice(st.session_state.ticketN)
            workDes = getDesc(ticket=st.session_state.ticketN)
            if workDes is None or workDes.empty:
                st.session_state.workDescription = "Please input"
                st.session_state.workDesDf = pd.DataFrame({"TicketID":[st.session_state.ticketN], "Incurred":[st.session_state.workDescription], "Proposed":[st.session_state.workDescription]})
            else:
                st.session_state.workDesDf = workDes
            st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df = getAllTicket(ticket=st.session_state.ticketN)
        st.sidebar.write("Actions")
        if st.sidebar.button("**Find Another Quote**", key="5"):
            refresh()
        # if st.sidebar.button("Delete Quote", key="6", help="Click to delete (requires confirmation)"):
        #     st.write("Item deleted successfully.")
        #     deleteTicketDiaglog(st.session_state.ticketN)
            # deleteTicket(st.session_state.ticketN)
            # time.sleep(5)  
            # refresh()  
            # st.empty()
            # st.error("Please double confirm to delete ticket")
            # confirm_col, cancel_col = st.columns(2)
            # if confirm_col.button("Confirm Delete", key="confirm"):
            #     print("Item deleted successfully.")
            #     deleteTicket(st.session_state.ticketN)
            #     time.sleep(2)  
            #     refresh()  
            # elif cancel_col.button("Cancel", key="cancel"):
            #     print("Deletion canceled.")
        else:

            if len(st.session_state.ticketDf)==0:
                st.error("Please enter a ticket number or check the ticket number again")
                # st.session_state.refresh_button = True
            else:
                parentDf = getParentByTicket(st.session_state.ticketN)
                if parentDf["NTE_QUOTE"].get(0) is not None and int(parentDf["NTE_QUOTE"].get(0)) == 1:
                    st.session_state.NTE_Quote = "QUOTE"
                else:
                    st.session_state.NTE_Quote = "NTE"
                if parentDf["Editable"].get(0) is not None and parentDf["Editable"].get(0) != "":
                    st.session_state.editable = int(parentDf["Editable"])
                else:
                    st.session_state.editable = 1
                if parentDf["Status"].get(0) is not None and (parentDf["Status"].get(0) == "Approved" or parentDf["Status"].get(0) == "Processed"):
                    st.error("this ticket is now in GP")
                    st.session_state.editable = 0
                left_data = {
                        'To': st.session_state.ticketDf['CUST_NAME'] + " " + st.session_state.ticketDf['CUST_ADDRESS1'] + " " +
                            st.session_state.ticketDf['CUST_ADDRESS2'] + " " + st.session_state.ticketDf['CUST_ADDRESS3'] + " " +
                            st.session_state.ticketDf['CUST_CITY'] + " " + st.session_state.ticketDf['CUST_Zip'],
                        'ATTN': ['ATTN']
                    }    

                if st.session_state.edit:
                    if st.sidebar.button("**Save Changes**"):        
                        savetime = datetime.now()
                        updateAll(st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df)
                        updateParent(st.session_state.ticketN, st.session_state.editable, st.session_state.NTE_Quote, savetime, "1900-01-01 00:00:00.000",  "1900-01-01 00:00:00.000", st.session_state.ticketDf["BranchName"].get(0), "save")
                        st.success("Successfully updated to database!") 
                        time.sleep(5)  
                        st.rerun()
                    if st.sidebar.button("**Cancel**"):
                        changeEditStatus()
                        st.rerun()
                # check editable
                elif st.session_state.editable:
                    if st.sidebar.button("**Edit Quote**"):
                        changeEditStatus()
                        st.rerun()
                    
                
                df_left = pd.DataFrame(left_data)
                left_table_styles = [
                    {'selector': 'table', 'props': [('text-align', 'left'), ('border-collapse', 'collapse')]},
                    {'selector': 'th, td', 'props': [('padding', '8px'), ('border', '1px solid black')]}
                ]
                df_left_styled = df_left.style.set_table_styles(left_table_styles)

                st.dataframe(df_left_styled, hide_index=True)

                # Ticket Info table
                data = {
                    'Site': st.session_state.ticketDf['LOC_LOCATNNM'],
                    'Ticket #': st.session_state.ticketN,
                    'Address': st.session_state.ticketDf['LOC_Address'] + " " + st.session_state.ticketDf['CITY'] + " " +
                            st.session_state.ticketDf['STATE'] + " " + st.session_state.ticketDf['ZIP']
                }

                data1 = {
                    'PO #': st.session_state.ticketDf['Purchase_Order'],
                    'Date': formatted_date,
                    'BranchEmail': st.session_state.ticketDf['MailDispatch'], 
                    'Customer': st.session_state.ticketDf['LOC_CUSTNMBR']
                }

                df_info1 = pd.DataFrame(data)
                df_info2 = pd.DataFrame(data1)

                st.subheader("Ticket Info")
                st.dataframe(df_info1, hide_index=True)
                st.dataframe(df_info2, hide_index=True)
                if st.session_state.get("temp_parts_df", None) is None or st.session_state.temp_parts_df.empty:
                    parts_data = {
                        'Incurred/Proposed': [None],
                        'Description': [None],
                        'QTY': [np.nan],
                        'UNIT Price': [np.nan],
                        'EXTENDED': [np.nan]
                    }
                    st.session_state.temp_parts_df = pd.DataFrame(parts_data)
                if st.session_state.get("miscellaneous_charges_df", None) is None or st.session_state.miscellaneous_charges_df.empty:
                    misc_charges_data = {
                        'Description': [None],
                        'QTY': [np.nan],
                        'UNIT Price': [np.nan],
                        'EXTENDED': [np.nan]
                    }
                    st.session_state.miscellaneous_charges_df = pd.DataFrame(misc_charges_data)

                if st.session_state.get("materials_non_stock_and_rentals_df", None) is None or st.session_state.materials_non_stock_and_rentals_df.empty:
                    materials_rentals_data = {
                        'Incurred/Proposed': [None],
                        'Description': [None],
                        'QTY': [np.nan],
                        'UNIT Price': [np.nan],
                        'EXTENDED': [np.nan]
                    }
                    st.session_state.materials_non_stock_and_rentals_df = pd.DataFrame(materials_rentals_data)

                if st.session_state.get("subcontractor_df", None) is None or st.session_state.subcontractor_df.empty:
                    subcontractor_data = {
                        'Description': [None],
                        'QTY': [np.nan],
                        'UNIT Price': [np.nan],
                        'EXTENDED': [np.nan]
                    }
                    st.session_state.subcontractor_df = pd.DataFrame(subcontractor_data)
                st.write("**UNLESS SPECIFICALLY NOTED, THIS PROPOSAL IS VALID FOR 30 DAYS FROM THE DATE ABOVE**")
                if st.session_state.editable:
                    incol1, incol2, incol3, incol4 = st.columns([3,1,1,1])
                    # with incol1:
                    # Display custom-styled buttons and handle their actions
                    # rear butt
                    with incol2:
                        # st.sidebar.markdown('<span id="approve-after"></span>', unsafe_allow_html=True)
                        # origin "approve" in st.session_state
                        if st.sidebar.button("**Approve**"):
                            print("approved clicked")
                            approvetime = datetime.now()
                            approve = approvetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            st.session_state.editable = 0
                            updateAll(st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df)
                            updateParent(st.session_state.ticketN, st.session_state.editable, st.session_state.NTE_Quote, "1900-01-01 00:00:00.000", approve, "1900-01-01 00:00:00.000", st.session_state.ticketDf["BranchName"].get(0), "approve")
                            st.sidebar.success("Successfully updated to Gp!")
                            time.sleep(3)
                            refresh()
                    with incol3:
                        # st.markdown('<span id="decline-after"></span>', unsafe_allow_html=True)
                        # origin "decline" in st.session_state
                        if st.sidebar.button("**Decline**"):
                            declinetime = datetime.now()
                            decline = declinetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            updateAll(st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df)
                            updateParent(st.session_state.ticketN, 1, st.session_state.NTE_Quote, "1900-01-01 00:00:00.000", "1900-01-01 00:00:00.000", decline, st.session_state.ticketDf["BranchName"].get(0), "decline")
                            st.sidebar.success("Successfully updated to declined!")
                            time.sleep(3)
                            refresh()
                    
                    with incol4:
                        # st.markdown('<span id="delete-after"></span>', unsafe_allow_html=True)
                        # origin "decline" in st.session_state
                        if st.sidebar.button("**Delete Quote**"):
                            st.sidebar.warning("Ticket deleted successfully.")
                            deleteTicketDiaglog(st.session_state.ticketN)
                if st.session_state.editable and st.session_state.edit:
                    with st.expander("Work Description", expanded=True):
                        with st.container():
                            incurredStr = str(st.session_state.workDesDf["Incurred"].get(0))
                            proposedStr = str(st.session_state.workDesDf["Proposed"].get(0))
                            incurred = st.text_area('***General description of Incurred:***', value=incurredStr, placeholder="", height=100, key='incurred')
                            proposed = st.text_area('***General description of Proposed work to be performed:***', value=proposedStr, placeholder="", height=100, key='proposed')
                            if st.button("Save Work Description"):
                                if incurred is None or incurred == "None":
                                    incurred = "None"
                                if proposed is None or proposed == "None":
                                    proposed = "None"
                                st.session_state.workDesDf.at[0, "Incurred"] = incurred
                                st.session_state.workDesDf.at[0, "Proposed"] = proposed
                        st.session_state.NTE_Quote = st.radio("Select Option:", ["NTE", "Quote"])
                    col1, col2 = st.columns([1, 3])

                    categories = ['Labor', 'Trip Charge', 'Parts', 'Miscellaneous Charges', 'Other', 'Subcontractor']
                    category_totals = {category: 0 for category in categories}

                    for category in categories:
                        with st.expander(f"******{category}******", expanded=True):
                            st.title(category)                          
                            width = 1000
                            inwidth = 700
                            if category == 'Labor':
                                labor_data = {
                                    'Incurred/Proposed': [None],
                                    'Description': [None],
                                    'Nums of Techs': [None],
                                    'Hours per Tech': [None],
                                    'QTY': [None],
                                    'Hourly Rate': [None],
                                    'EXTENDED': [None],
                                }
                                string_values = [" : "+str(value).rstrip('0').rstrip('.') for value in st.session_state.LRatesDf['Billing_Amount']]
                                concatenated_values = [description + value for description, value in zip(st.session_state.LRatesDf['Pay_Code_Description'], string_values)]    
                                concatenated_values.insert(0, 'FGT Labor')
                                # new
                                with st.form(key='Labor_form', clear_on_submit=True):
                                    st.write("New Labor")
                                    newLabordf = pd.DataFrame(labor_data)
                                    newLabordf = st.data_editor(
                                        newLabordf,
                                        column_config={
                                            "Incurred/Proposed": st.column_config.SelectboxColumn(
                                                "Incurred/Proposed",
                                                help="Incurred",
                                                width=inwidth/6,
                                                options=["Incurred", "Proposed"],
                                            ),
                                            "Description": st.column_config.SelectboxColumn(
                                                "Description",
                                                help="Description",
                                                width=inwidth/6,
                                                options=concatenated_values
                                            ),
                                            "Nums of Techs": st.column_config.NumberColumn(
                                                "Nums of Techs",
                                                help="Nums of Techs",
                                                width=inwidth/6,
                                                min_value=1,
                                                step=1
                                            ),
                                            "Hours per Tech": st.column_config.NumberColumn(
                                                "Hours per Tech",
                                                help="Hours per Tech",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step = 0.25
                                            ),
                                            "QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True,
                                            ),
                                            "Hourly Rate": st.column_config.NumberColumn(
                                                "Hourly Rate",
                                                help="Hourly Rate",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True,
                                            ),
                                            "EXTENDED": st.column_config.NumberColumn(
                                                "EXTENDED",
                                                help="Extended Amount",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                format="%.2f"
                                            ),
                                        },
                                        hide_index=True,
                                        width=width,
                                        num_rows="dynamic",
                                        key=category+"df"
                                    )
                                    col1, col2 = st.columns([3,1])
                                    submit_button = col2.form_submit_button(label=f'Submit {category}')
                                    if not newLabordf.empty:
                                        if submit_button:
                                            fgt_labor_mask = newLabordf['Description'] == "FGT Labor"
                                            if fgt_labor_mask.any():
                                                fgt_labor_df = newLabordf[fgt_labor_mask]
                                                # fgt_labor_df = fgt_labor_df[['Description', 'Incurred/Proposed', 'EXTENDED']].dropna()
                                                fgt_labor_df.fillna(0.0, inplace=True)
                                                fgt_labor_df['EXTENDED'] = pd.to_numeric(fgt_labor_df['EXTENDED'], errors='coerce').round(2)
                                                # fgt_labor_df['EXTENDED'] = np.round(pd.to_numeric(fgt_labor_df['EXTENDED'], errors='coerce'), 2)
                                                st.session_state.labor_df = pd.concat([st.session_state.labor_df, fgt_labor_df], ignore_index=True)
                                            else:
                                                qty_values = newLabordf["Nums of Techs"]
                                                hours_values = newLabordf["Hours per Tech"]
                                                qty_mask = qty_values.notnull() & hours_values.notnull()
                                                newLabordf.loc[qty_mask, 'QTY'] = np.array(qty_values[qty_mask]) * np.array(hours_values[qty_mask])

                                                description_values = newLabordf['Description']
                                                rate_mask = description_values.notnull()
                                                newLabordf.loc[rate_mask, 'Hourly Rate'] = description_values[rate_mask].apply(
                                                    lambda x: re.search(r'(\d+(\.\d+)?)', x).group() if re.search(r'(\d+(\.\d+)?)', x) else 0
                                                )

                                                extended_mask = qty_mask & rate_mask
                                                qty_values = pd.to_numeric(newLabordf.loc[qty_mask, 'QTY'], errors='coerce')
                                                hourly = pd.to_numeric(newLabordf.loc[rate_mask, 'Hourly Rate'], errors='coerce')
                                                rounded_extended_values = np.round(np.array(qty_values) * np.array(hourly), 2)
                                                newLabordf.loc[extended_mask, 'EXTENDED'] = rounded_extended_values
                                                # newLabordf = newLabordf.dropna()
                                                st.session_state.labor_df = pd.concat([st.session_state.labor_df, newLabordf], ignore_index=True)
                                                st.rerun()
                                if not st.session_state.labor_df.empty:
                                    st.write("Archived Labor (Delete row when necessary please dont add rows)")
                                    tempLabor_df = st.data_editor(
                                        st.session_state.labor_df,
                                        column_config={
                                            "Incurred/Proposed": st.column_config.Column(
                                                "Incurred/Proposed",
                                                help="Incurred",
                                                width=inwidth/6,
                                                disabled=True,
                                            ),
                                            "Description": st.column_config.Column(
                                                "Description",
                                                help="Description",
                                                width=inwidth/6,
                                                disabled=True,
                                            ),
                                            "Nums of Techs": st.column_config.NumberColumn(
                                                "Nums of Techs",
                                                help="Nums of Techs",
                                                width=inwidth/6,
                                                min_value=1,
                                                disabled=True,
                                                step=1
                                            ),
                                            "Hours per Tech": st.column_config.NumberColumn(
                                                "Hours per Tech",
                                                help="Hours per Tech",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True,
                                            ),
                                            "QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True,
                                            ),
                                            "Hourly Rate": st.column_config.NumberColumn(
                                                "Hourly Rate",
                                                help="Hourly Rate",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True,
                                            ),
                                            "EXTENDED": st.column_config.NumberColumn(
                                                "EXTENDED",
                                                help="Extended Amount",
                                                width=inwidth/6,
                                                disabled=True,
                                                min_value=0.00,
                                                format="%.2f"
                                            ),
                                        },
                                        hide_index=True,
                                        width=width,
                                        num_rows="dynamic",
                                        key=category
                                    )
                                    if not tempLabor_df.equals(st.session_state.labor_df):
                                        st.session_state.labor_df = pd.DataFrame(tempLabor_df)
                                        st.rerun()
                                    category_totals[category] = st.session_state.labor_df['EXTENDED'].sum()
                            elif category == 'Trip Charge':
                                string_values = [" : "+str(value).rstrip('0').rstrip('.') for value in st.session_state.TRatesDf['Billing_Amount']]
                                concatenated_values = [description + value for description, value in zip(st.session_state.TRatesDf['Pay_Code_Description'], string_values)]
                                # new
                                with st.form(key='TripCharge_form', clear_on_submit=True):
                                    st.write("New Trip/Travel Charge")
                                    trip_charge_data = {
                                        'Incurred/Proposed': [None],
                                        'Description': [None],
                                        'QTY': [None],
                                        'UNIT Price': [None],
                                        'EXTENDED': [None],
                                    }
                                    newTripdf = pd.DataFrame(trip_charge_data)
                                    if len(concatenated_values) > 0:
                                        newTripdf = st.data_editor(
                                            newTripdf,
                                            column_config={
                                                "Incurred/Proposed": st.column_config.SelectboxColumn(
                                                    "Incurred/Proposed",
                                                    help="Incurred",
                                                    width=inwidth/6,
                                                    options=["Incurred", "Proposed"],
                                                    ),
                                                "QTY": st.column_config.NumberColumn(
                                                    "QTY",
                                                    help="Quantity",
                                                    width=inwidth/6,
                                                    min_value=0.00
                                                ),
                                                "Description": st.column_config.SelectboxColumn(
                                                    "Description",
                                                    help="Description",
                                                    width=inwidth/4,
                                                    options=concatenated_values,
                                                ),
                                                "UNIT Price": st.column_config.NumberColumn(
                                                    "UNIT Price",
                                                    help="Unit Price",
                                                    width=inwidth/4,
                                                    min_value=0.00,
                                                step = 0.25,
                                                    # disabled=True
                                                    ),
                                                "EXTENDED": st.column_config.NumberColumn(
                                                    "EXTENDED",
                                                    help="Extended Amount",
                                                    width=inwidth/4,
                                                    min_value=0.00,
                                                    format="%.2f",
                                                    disabled=True
                                                )
                                            },
                                            hide_index=True,
                                            width=width,
                                            num_rows="dynamic",
                                            key=category+"df"
                                        )
                                    else:
                                        newTripdf = st.data_editor(
                                            newTripdf,
                                            column_config={
                                                "Incurred/Proposed": st.column_config.SelectboxColumn(
                                                    "Incurred/Proposed",
                                                    help="Incurred",
                                                    width=inwidth/6,
                                                    options=["Incurred", "Proposed"],
                                                    ),
                                                "QTY": st.column_config.NumberColumn(
                                                    "QTY",
                                                    help="Quantity",
                                                    width=inwidth/6,
                                                    min_value=0.00
                                                ),
                                                "Description": st.column_config.TextColumn(
                                                    "Description",
                                                    help="Description",
                                                    width=inwidth/4
                                                ),
                                                "UNIT Price": st.column_config.NumberColumn(
                                                    "UNIT Price",
                                                    help="Unit Price",
                                                    width=inwidth/4,
                                                    min_value=0.00,
                                                step = 0.25,
                                                    ),
                                                "EXTENDED": st.column_config.NumberColumn(
                                                    "EXTENDED",
                                                    help="Extended Amount",
                                                    width=inwidth/4,
                                                    min_value=0.00,
                                                    format="%.2f",
                                                    disabled=True
                                                )
                                            },
                                            hide_index=True,
                                            width=width,
                                            num_rows="dynamic",
                                            key=category+"df"
                                        )
                                    col1, col2 = st.columns([3,1])
                                    submit_button = col2.form_submit_button(label=f'Submit {category}')
                                    if not newTripdf.empty:
                                        if submit_button:
                                            qty_mask = newTripdf['QTY'].notnull()
                                            desc_mask = newTripdf['Description'].notnull()
                                            qty_values = newTripdf.loc[qty_mask, 'QTY']
                                            descriptions = newTripdf.loc[desc_mask,'Description']
                                            incurred_mask = newTripdf['Incurred/Proposed'].notnull()
                                            newTripdf = newTripdf[incurred_mask & qty_mask & desc_mask]
                                            rate_mask = newTripdf['UNIT Price'].isnull()
                                            newTripdf.loc[rate_mask, 'UNIT Price'] = newTripdf.loc[rate_mask, 'Description'].apply(lambda x: re.search(r'(\d+(\.\d+)?)', x).group() if re.search(r'(\d+(\.\.\d+)?)', x) else 0)
                                            newTripdf['UNIT Price'] = pd.to_numeric(newTripdf['UNIT Price'], errors='coerce')
                                            if newTripdf['EXTENDED'].isnull().any():
                                                extended_mask = newTripdf['EXTENDED'].isnull()
                                                newTripdf.loc[extended_mask, 'EXTENDED'] = newTripdf.loc[extended_mask, 'UNIT Price'] * qty_values
                                            st.session_state.trip_charge_df = pd.concat([st.session_state.trip_charge_df, newTripdf], ignore_index=True)
                                            category_totals[category] = st.session_state.trip_charge_df['EXTENDED'].sum()
                                            st.rerun()
                                        col1.write("<small>Please enter Unit Price if 0</small>", unsafe_allow_html=True)
                                if not st.session_state.trip_charge_df.empty:
                                    st.write("Archived Trip/Travel Charge (Delete row when necessary please dont add rows)")
                                    tempTripDf = st.data_editor(
                                        st.session_state.trip_charge_df,
                                        column_config={
                                            "Incurred/Proposed": st.column_config.Column(
                                                "Incurred/Proposed",
                                                help="Incurred",
                                                width=inwidth/6,
                                                disabled=True
                                            ),"QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True
                                            ),
                                            "Description": st.column_config.Column(
                                                "Description",
                                                help="Description",
                                                width=inwidth/4,
                                                disabled=True
                                            ),
                                            "UNIT Price": st.column_config.NumberColumn(
                                                "UNIT Price",
                                                help="Unit Price",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True
                                            ),
                                            "EXTENDED": st.column_config.NumberColumn(
                                                "EXTENDED",
                                                help="Extended Amount",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                format="%.2f",
                                                disabled=True
                                            )
                                        },
                                        hide_index=True,
                                        width=width,
                                        num_rows="dynamic",
                                        key=category
                                    )
                                    if not tempTripDf.equals(st.session_state.trip_charge_df):
                                        st.session_state.trip_charge_df = pd.DataFrame(tempTripDf)
                                        st.rerun()
                                    category_totals[category] = st.session_state.trip_charge_df['EXTENDED'].sum()
                            elif category == 'Parts':
                                st.session_state.input_letters = st.text_input("First enter Part Id or Parts Desc:", max_chars=30).upper()
                                if st.session_state.input_letters != st.session_state.prev_input_letters and len(st.session_state.input_letters) > 0:
                                    curr = (st.session_state.input_letters or "").upper()[:15]
                                    st.session_state.pricingDf = getBinddes(curr)
                                    print(curr, st.session_state.pricingDf)
                                    st.session_state.prev_input_letters = st.session_state.input_letters
                                if st.session_state.pricingDf is None or st.session_state.pricingDf.empty:
                                    st.error("Please enter a valid Part Id or Part Desc.")
                                else:
                                    with st.form(key='parts_form', clear_on_submit=True):
                                        st.write("New Parts")
                                        parts_data = {
                                            'Incurred/Proposed': [None],
                                            'Description': [None],
                                            'QTY': [None],
                                            'UNIT Price': [None],
                                            'EXTENDED': [None],
                                        }
                                        newParts_df = pd.DataFrame(parts_data)
                                        if len(st.session_state.input_letters) > 0:
                                            filtered_descriptions = st.session_state.pricingDf[(st.session_state.pricingDf['ITEMNMBR'] + " : " + st.session_state.pricingDf['ITEMDESC']).str.contains(st.session_state.input_letters)]
                                            filtered_descriptions['bindDes'] = filtered_descriptions['ITEMNMBR'] + " : " + filtered_descriptions['ITEMDESC']
                                            newParts_df = st.data_editor(
                                                newParts_df,
                                                column_config={
                                                    "QTY": st.column_config.NumberColumn(
                                                        "QTY",
                                                        help="Quantity",
                                                        width=inwidth/4,
                                                        min_value=0,
                                                        
                                                    ),
                                                    "Description": st.column_config.SelectboxColumn(
                                                        "Description",
                                                        help="Description",
                                                        width=inwidth/4,
                                                        options=filtered_descriptions['bindDes'],
                                                    ),
                                                    "Incurred/Proposed": st.column_config.SelectboxColumn(
                                                        "Incurred/Proposed",
                                                        help="Incurred",
                                                        width=inwidth/6,
                                                        options=["Incurred", "Proposed"]
                                                    ),
                                                    "UNIT Price": st.column_config.NumberColumn(
                                                        "UNIT Price",
                                                        help="Unit Price",
                                                        width=inwidth/4,
                                                        min_value=0.00,
                                                        step = 0.25,
                                                        disabled=True
                                                    ),
                                                    "EXTENDED": st.column_config.NumberColumn(
                                                        "EXTENDED",
                                                        help="Extended Amount",
                                                        width=inwidth/4,
                                                        min_value=0.00,
                                                        format="%.2f",
                                                        disabled=True
                                                    )
                                                },
                                                hide_index=True,
                                                width=width,
                                                num_rows="dynamic",
                                                key=category+"df"
                                            )
                                        else:
                                            newParts_df = st.data_editor(
                                            newParts_df,
                                            column_config={
                                                "QTY": st.column_config.NumberColumn(
                                                    "QTY",
                                                    help="Quantity",
                                                    width=inwidth/4,
                                                    min_value=0,
                                                    disabled=True                                            
                                                ),
                                                "Description": st.column_config.SelectboxColumn(
                                                    "Description",
                                                    help="Description",
                                                    width=inwidth/4,
                                                    options=["please input something"],
                                                    disabled=True
                                                ),
                                                "Incurred/Proposed": st.column_config.SelectboxColumn(
                                                    "Incurred/Proposed",
                                                    help="Incurred",
                                                    width=inwidth/6,
                                                    options=["Incurred", "Proposed"],
                                                    disabled=True
                                                ),
                                                "UNIT Price": st.column_config.NumberColumn(
                                                    "UNIT Price",
                                                    help="Unit Price",
                                                    width=inwidth/4,
                                                    min_value=0.00,
                                                step = 0.25,
                                                    disabled=True
                                                ),
                                                "EXTENDED": st.column_config.NumberColumn(
                                                    "EXTENDED",
                                                    help="Extended Amount",
                                                    width=inwidth/4,
                                                    min_value=0.00,
                                                    format="%.2f",
                                                    disabled=True
                                                )
                                            },
                                            hide_index=True,
                                            width=width,
                                            num_rows="dynamic",
                                            key=category+"df"
                                        )
                                        col1, col2 = st.columns([3, 1])
                                    submit_button = col2.form_submit_button(label=f'Submit {category}')
                                    if not newParts_df.empty:
                                        if submit_button and len(st.session_state.input_letters) > 0:
                                            qty_mask = newParts_df['QTY'].notnull()
                                            desc_mask = newParts_df['Description'].notnull()
                                            qty_values = newParts_df.loc[qty_mask, 'QTY']
                                            descriptions = newParts_df.loc[desc_mask,'Description']
                                            incurred_mask = newParts_df['Incurred/Proposed'].notnull()
                                            newParts_df = newParts_df[incurred_mask & qty_mask & desc_mask]
                                            mask = filtered_descriptions['bindDes'].isin(descriptions)
                                            filtered_descriptions = filtered_descriptions[mask]
                                            chosen_descriptions = filtered_descriptions[['bindDes', 'ITEMNMBR']].copy()
                                            chosen_descriptions = chosen_descriptions.dropna(subset=['bindDes'])
                                            chosen_descriptions['Bill_Customer_Number'] = st.session_state.ticketDf['Bill_Customer_Number'].iloc[0]
                                            partsPriceDf = getPartsPrice(chosen_descriptions)
                                            selling_prices = pd.to_numeric(partsPriceDf['SellingPrice'], errors='coerce')
                                            unit_mask = newParts_df['UNIT Price'].isnull()
                                            newParts_df.loc[unit_mask, 'UNIT Price'] = selling_prices.values
                                            if newParts_df['EXTENDED'].isnull().any():
                                                extended_mask = newParts_df['EXTENDED'].isnull()
                                                newParts_df.loc[extended_mask, 'EXTENDED'] = newParts_df.loc[extended_mask, 'UNIT Price'] * qty_values
                                            st.session_state.parts_df = pd.concat([st.session_state.parts_df, newParts_df], ignore_index=True)
                                            st.rerun()
                                if not st.session_state.parts_df.empty:
                                    st.write("Archived Parts (Delete row when necessary please dont add rows)")
                                    st.session_state.parts_df.reset_index(drop=True, inplace=True)
                                    tempParts_df = st.data_editor(
                                        st.session_state.parts_df,
                                        column_config={
                                            "Incurred/Proposed": st.column_config.Column(
                                                "Incurred/Proposed",
                                                help="Incurred",
                                                width=inwidth/6,
                                                disabled=True
                                            ),
                                            "QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/4,
                                                min_value=0,
                                                disabled=True
                                            ),
                                            "Description": st.column_config.Column(
                                                "Description",
                                                help="Description",
                                                width=inwidth/4,
                                                disabled=True
                                            ),
                                            "UNIT Price": st.column_config.NumberColumn(
                                                "UNIT Price",
                                                help="Unit Price",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True
                                            ),
                                            "EXTENDED": st.column_config.NumberColumn(
                                                "EXTENDED",
                                                help="Extended Amount",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                format="%.2f",
                                                disabled=True
                                            )
                                        },
                                        hide_index=True,
                                        width=width,
                                        num_rows="dynamic",
                                        key=category
                                    )
                                    category_totals[category] = st.session_state.parts_df['EXTENDED'].sum()
                                    if not tempParts_df.equals(st.session_state.parts_df):
                                        st.session_state.parts_df = pd.DataFrame(tempParts_df)
                                        st.rerun()
                                st.success("Parts pricing will reflect any additional tariffs from suppliers.")
                            # elif category == 'Parts':
                            #     st.session_state.input_letters = st.text_input("First enter Part Id or Parts Desc:", max_chars=15).upper()
                            #     if st.session_state.input_letters != st.session_state.prev_input_letters and len(st.session_state.input_letters) > 0:
                            #         st.session_state.pricingDf = getBinddes(st.session_state.input_letters)
                            #         st.session_state.prev_input_letters = st.session_state.input_letters
                            #     if st.session_state.pricingDf is None or st.session_state.pricingDf.empty or len(st.session_state.input_letters) == 0:
                            #         st.error("Please enter a valid Part Id or Part Desc.")
                            #     else:              
                            #         if len(st.session_state.input_letters) > 0:
                            #             filtered_descriptions = st.session_state.pricingDf[(st.session_state.pricingDf['ITEMNMBR'] + " : " + st.session_state.pricingDf['ITEMDESC']).str.contains(st.session_state.input_letters)]
                            #             filtered_descriptions['bindDes'] = filtered_descriptions['ITEMNMBR'] + " : " + filtered_descriptions['ITEMDESC']
                                                            
                            #             string_values = [" : "+f'{value:.2f}'.rstrip('0').rstrip('.') for value in st.session_state.misc_ops_df['Fee_Amount']]
                            #             concatenated_values = [description + value for description, value in zip(st.session_state.misc_ops_df['Fee_Charge_Type'], string_values)]
                            #             with st.form(key='mismis'):
                            #                 st.session_state.temp_parts_df = st.data_editor(
                            #                     st.session_state.temp_parts_df,
                            #                     column_config={
                            #                         "Incurred/Proposed": st.column_config.SelectboxColumn(
                            #                             "Incurred/Proposed",
                            #                             help="Incurred",
                            #                             width=inwidth/6,
                            #                             options=["Incurred", "Proposed"]
                            #                         ),
                            #                         "QTY": st.column_config.NumberColumn(
                            #                             "QTY",
                            #                             help="Quantity",
                            #                             width=inwidth/4,
                            #                             min_value=0.00
                            #                         ),
                            #                         "Description": st.column_config.SelectboxColumn(
                            #                             "Description",
                            #                             help="Description",
                            #                             width=inwidth/4,
                            #                             options=filtered_descriptions['bindDes'],
                            #                         ),
                            #                         "UNIT Price": st.column_config.NumberColumn(
                            #                             "UNIT Price",
                            #                             help="Unit Price",
                            #                             width=inwidth/4,
                            #                             min_value=0.00,
                                                        # step = 0.25,
                            #                             disabled=True
                            #                         ),
                            #                         "EXTENDED": st.column_config.NumberColumn(
                            #                             "EXTENDED",
                            #                             help="Extended Amount",
                            #                             width=inwidth/4,
                            #                             min_value=0.00,
                            #                             disabled=True
                            #                         )
                            #                     },
                            #                     hide_index=True,
                            #                     width=width,
                            #                     num_rows="dynamic",
                            #                     key=category+"ddd"
                            #                 )                        
                            #                 col1, col2, col3 = st.columns([3, 1, 1])
                            #                 submit_button = col3.form_submit_button(label='Submit')
                            #                 cal_button = col2.form_submit_button(label='Calculate')
                            #                 if cal_button:
                            #                     print(st.session_state.temp_parts_df)
                            #                     st.rerun()
                            #                 if submit_button:
                            #                     st.session_state.parts_df = pd.concat([st.session_state.parts_df, st.session_state.temp_parts_df], ignore_index=True)

                            #         with st.form(key='parts_form', clear_on_submit=True):
                            #             if len(st.session_state.input_letters) > 0:
                            #                 filtered_descriptions = st.session_state.pricingDf[(st.session_state.pricingDf['ITEMNMBR'] + " : " + st.session_state.pricingDf['ITEMDESC']).str.contains(st.session_state.input_letters)]
                            #                 filtered_descriptions['bindDes'] = filtered_descriptions['ITEMNMBR'] + " : " + filtered_descriptions['ITEMDESC']
                            #                 st.session_state.temp_parts_df = st.data_editor(
                            #                     st.session_state.temp_parts_df,
                            #                     column_config={
                            #                         "QTY": st.column_config.NumberColumn(
                            #                             "QTY",
                            #                             help="Quantity",
                            #                             width=inwidth/4,
                            #                             min_value=0,
                                                        
                            #                         ),
                            #                         "Description": st.column_config.SelectboxColumn(
                            #                             "Description",
                            #                             help="Description",
                            #                             width=inwidth/4,
                            #                             options=filtered_descriptions['bindDes'],
                            #                         ),
                            #                         "Incurred/Proposed": st.column_config.SelectboxColumn(
                            #                             "Incurred/Proposed",
                            #                             help="Incurred",
                            #                             width=inwidth/6,
                            #                             options=["Incurred", "Proposed"]
                            #                         ),
                            #                         "UNIT Price": st.column_config.NumberColumn(
                            #                             "UNIT Price",
                            #                             help="Unit Price",
                            #                             width=inwidth/4,
                            #                             min_value=0.00,
                                                        # step = 0.25,
                            #                             disabled=True
                            #                         ),
                            #                         "EXTENDED": st.column_config.NumberColumn(
                            #                             "EXTENDED",
                            #                             help="Extended Amount",
                            #                             width=inwidth/4,
                            #                             min_value=0.00,
                            #                             format="%.2f",
                            #                             disabled=True
                            #                         )
                            #                     },
                            #                     hide_index=True,
                            #                     width=width,
                            #                     num_rows="dynamic",
                            #                     key=category+"df"
                            #                 )
                            #             col1, col2, col3 = st.columns([3, 1, 1])
                            #             submit_button = col3.form_submit_button(label='Submit', type="secondary")
                            #             cal_button = col2.form_submit_button(label='Calculate', type="secondary")
                            #             if cal_button:
                            #                 qty_mask = st.session_state.temp_parts_df['QTY'].notnull()
                            #                 desc_mask = st.session_state.temp_parts_df['Description'].notnull()
                            #                 qty_values = st.session_state.temp_parts_df.loc[qty_mask, 'QTY']
                            #                 descriptions = st.session_state.temp_parts_df.loc[desc_mask,'Description']
                            #                 incurred_mask = st.session_state.temp_parts_df['Incurred/Proposed'].notnull()
                            #                 st.session_state.temp_parts_df = st.session_state.temp_parts_df[incurred_mask & qty_mask & desc_mask]
                            #                 # mask = filtered_descriptions['bindDes'].isin(descriptions)
                            #                 # filtered_descriptions = filtered_descriptions[mask]
                            #                 chosen_descriptions = filtered_descriptions[['bindDes', 'ITEMNMBR']].copy()
                            #                 chosen_descriptions = chosen_descriptions.dropna(subset=['bindDes'])
                            #                 chosen_descriptions['Bill_Customer_Number'] = st.session_state.ticketDf['Bill_Customer_Number'].iloc[0]
                            #                 # partsPriceDf = getPartsPrice(chosen_descriptions)
                            #                 print(chosen_descriptions)
                            #                 selling_prices = pd.to_numeric(partsPriceDf['SellingPrice'], errors='coerce')
                            #                 unit_mask = st.session_state.temp_parts_df['UNIT Price'].isnull()
                            #                 st.session_state.temp_parts_df.loc[unit_mask, 'UNIT Price'] = selling_prices.values
                            #                 if st.session_state.temp_parts_df['EXTENDED'].isnull().any():
                            #                     extended_mask = st.session_state.temp_parts_df['EXTENDED'].isnull()
                            #                     st.session_state.temp_parts_df.loc[extended_mask, 'EXTENDED'] = st.session_state.temp_parts_df.loc[extended_mask, 'UNIT Price'] * qty_values
                            #                 if st.session_state.temp_parts_df.empty:
                            #                     parts_data = {
                            #                         'Incurred/Proposed': [None],
                            #                         'Description': [None],
                            #                         'QTY': [None],
                            #                         'UNIT Price': [None],
                            #                         'EXTENDED': [None],
                            #                     }
                            #                     st.session_state.temp_parts_df = pd.DataFrame(parts_data)
                            #                     st.rerun()
                            #             if submit_button:
                            #                 qty_mask = st.session_state.temp_parts_df['QTY'].notnull()
                            #                 desc_mask = st.session_state.temp_parts_df['Description'].notnull()
                            #                 qty_values = st.session_state.temp_parts_df.loc[qty_mask, 'QTY']
                            #                 descriptions = st.session_state.temp_parts_df.loc[desc_mask,'Description']
                            #                 incurred_mask = st.session_state.temp_parts_df['Incurred/Proposed'].notnull()
                            #                 st.session_state.temp_parts_df = st.session_state.temp_parts_df[incurred_mask & qty_mask & desc_mask]
                            #                 # binddes big problem
                            #                 mask = filtered_descriptions['bindDes'].isin(descriptions)
                            #                 filtered_descriptions = filtered_descriptions[mask]
                            #                 chosen_descriptions = filtered_descriptions[['bindDes', 'ITEMNMBR']].copy()
                            #                 chosen_descriptions = chosen_descriptions.dropna(subset=['bindDes'])
                            #                 chosen_descriptions['Bill_Customer_Number'] = st.session_state.ticketDf['Bill_Customer_Number'].iloc[0]
                            #                 print(chosen_descriptions)
                            #                 partsPriceDf = getPartsPrice(chosen_descriptions)
                            #                 selling_prices = pd.to_numeric(partsPriceDf['SellingPrice'], errors='coerce')
                            #                 unit_mask = st.session_state.temp_parts_df['UNIT Price'].isnull()
                            #                 st.session_state.temp_parts_df.loc[unit_mask, 'UNIT Price'] = selling_prices.values
                            #                 if st.session_state.temp_parts_df['EXTENDED'].isnull().any():
                            #                     extended_mask = st.session_state.temp_parts_df['EXTENDED'].isnull()
                            #                     st.session_state.temp_parts_df.loc[extended_mask, 'EXTENDED'] = st.session_state.temp_parts_df.loc[extended_mask, 'UNIT Price'] * qty_values
                            #                 st.session_state.parts_df = pd.concat([st.session_state.parts_df, st.session_state.temp_parts_df], ignore_index=True)
                            #                 st.session_state.temp_parts_df = pd.DataFrame()
                            #                 st.rerun()
                                
                            #     if not st.session_state.parts_df.empty:
                            #         st.write("Archived Parts (Delete row when necessary please dont add rows)")
                            #         tempParts_df = st.data_editor(
                            #             st.session_state.parts_df,
                            #             column_config={
                            #                 "Incurred/Proposed": st.column_config.SelectboxColumn(
                            #                     "Incurred/Proposed",
                            #                     help="Incurred",
                            #                     width=inwidth/6,
                            #                     options=[],
                            #                     disabled=True
                            #                 ),
                            #                 "QTY": st.column_config.NumberColumn(
                            #                     "QTY",
                            #                     help="Quantity",
                            #                     width=inwidth/4,
                            #                     min_value=0,
                            #                     disabled=True
                            #                 ),
                            #                 "Description": st.column_config.SelectboxColumn(
                            #                     "Description",
                            #                     help="Description",
                            #                     width=inwidth/4,
                            #                     options=[''],
                            #                     disabled=True
                            #                 ),
                            #                 "UNIT Price": st.column_config.NumberColumn(
                            #                     "UNIT Price",
                            #                     help="Unit Price",
                            #                     width=inwidth/4,
                            #                     min_value=0.00,
                                                # step = 0.25,
                            #                     disabled=True
                            #                 ),
                            #                 "EXTENDED": st.column_config.NumberColumn(
                            #                     "EXTENDED",
                            #                     help="Extended Amount",
                            #                     width=inwidth/4,
                            #                     min_value=0.00,
                            #                     format="%.2f",
                            #                     disabled=True
                            #                 )
                            #             },
                            #             hide_index=True,
                            #             width=width,
                            #             num_rows="dynamic",
                            #             key=category
                            #         )
                            #         category_totals[category] = st.session_state.parts_df['EXTENDED'].sum()
                            #         if not tempParts_df.equals(st.session_state.parts_df):
                            #             st.session_state.parts_df = pd.DataFrame(tempParts_df)
                            #             st.rerun()
                            elif category == 'Miscellaneous Charges':
                                string_values = [" : "+f'{value:.2f}'.rstrip('0').rstrip('.') for value in st.session_state.misc_ops_df['Fee_Amount']]
                                concatenated_values = [description + value for description, value in zip(st.session_state.misc_ops_df['Fee_Charge_Type'], string_values)]
                                with st.form(key='Misc_form', clear_on_submit=True):
                                    st.write("New Miscellaneous")
                                    misc_data = {
                                        'Description': [None],
                                        'QTY': [None],
                                        'UNIT Price': [None],
                                        'EXTENDED': [None],
                                    }
                                    newMisc_df = pd.DataFrame(misc_data)
                                    newMisc_df = st.data_editor(
                                                newMisc_df,
                                                column_config={
                                            "QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/4,
                                                min_value=0.00
                                            ),
                                            "Description": st.column_config.SelectboxColumn(
                                                "Description",
                                                help="Description",
                                                width=inwidth/4,
                                                options=concatenated_values
                                            ),
                                            "UNIT Price": st.column_config.NumberColumn(
                                                "UNIT Price",
                                                help="Unit Price",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True
                                            ),
                                            "EXTENDED": st.column_config.NumberColumn(
                                                "EXTENDED",
                                                help="Extended Amount",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                disabled=True
                                            )
                                        },
                                        hide_index=True,
                                        width=width,
                                        num_rows="dynamic",
                                        key=category+"df"
                                    )                         
                                    col1, col2 = st.columns([3,1])
                                    submit_button = col2.form_submit_button(label=f'Submit {category}')
                                    if submit_button:
                                        qty_values = newMisc_df['QTY']
                                        mask = qty_values.notnull() & newMisc_df['Description'].notnull()
                                        newMisc_df.loc[mask, 'UNIT Price'] = newMisc_df.loc[mask,'Description'].apply(lambda x: re.search(r'(\d+(\.\d+)?)', x).group() if re.search(r'(\d+(\.\.\d+)?)', x) else 0)
                                        unit_price_values = newMisc_df.loc[mask,'UNIT Price']
                                        newMisc_df.loc[mask, 'EXTENDED'] = pd.to_numeric(qty_values[mask], errors='coerce').values * pd.to_numeric(unit_price_values[mask], errors='coerce').values
                                        if newMisc_df.empty:
                                            misc_charges_data = {
                                                'Description': [None],
                                                'QTY': [None],
                                                'UNIT Price': [None],
                                                'EXTENDED': [None]
                                            }
                                        newMisc_df.dropna(subset=['Description', 'QTY', 'UNIT Price', 'EXTENDED'], inplace=True)
                                        st.session_state.miscellaneous_charges_df = pd.concat([st.session_state.miscellaneous_charges_df, newMisc_df], ignore_index=True)
                                        st.rerun()

                                if not st.session_state.miscellaneous_charges_df.empty:
                                    st.write("Archived Misc (Delete row when necessary please dont add rows)")
                                    tempMiscellaneous_charges_df = st.data_editor(
                                        st.session_state.miscellaneous_charges_df,
                                        column_config={
                                            "QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/4,
                                                min_value=0.00
                                            ),
                                            "Description": st.column_config.Column(
                                                "Description",
                                                help="Description",
                                                width=inwidth/4,
                                            ),
                                            "UNIT Price": st.column_config.NumberColumn(
                                                "UNIT Price",
                                                help="Unit Price",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                step = 0.25,
                                                disabled=True
                                            ),
                                            "EXTENDED": st.column_config.NumberColumn(
                                                "EXTENDED",
                                                help="Extended Amount",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                disabled=True
                                            )
                                        },
                                        hide_index=True,
                                        width=width,
                                        num_rows="dynamic",
                                        key=category
                                    )             
                                    if not tempMiscellaneous_charges_df.equals(st.session_state.miscellaneous_charges_df):
                                        st.session_state.miscellaneous_charges_df = pd.DataFrame(tempMiscellaneous_charges_df)
                                        st.rerun()
                                    category_total = st.session_state.miscellaneous_charges_df['EXTENDED'].sum()
                                    category_totals[category] = category_total
                                    
                            elif category == 'Other':
                                st.write("Include Mileage, Materials/Non Stock, Rentals, and other items here")
                                with st.form(key=f'{category}_form'):
                                    st.session_state.materials_non_stock_and_rentals_df = st.data_editor(
                                        st.session_state.materials_non_stock_and_rentals_df,
                                        column_config={
                                            "Incurred/Proposed": st.column_config.SelectboxColumn(
                                                "Incurred/Proposed",
                                                help="Incurred",
                                                width=inwidth/6,
                                                options=["Incurred", "Proposed"]
                                            ),
                                            "QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/6,
                                                min_value=0,
                                                step=0.01,
                                                format="%.2f"
                                                
                                            ),
                                            "Description": st.column_config.TextColumn(
                                                "Description",
                                                help="Description",
                                                width=inwidth/6
                                            ),
                                            "UNIT Price": st.column_config.NumberColumn(
                                                "UNIT Price",
                                                help="Unit Price",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step=0.01,
                                                format="%.2f"
                                            ),
                                            "EXTENDED": st.column_config.NumberColumn(
                                                "EXTENDED",
                                                help="Extended Amount",
                                                width=inwidth/6,
                                                min_value=0.00,
                                                step=0.01,
                                                format="%.2f",
                                                disabled=True
                                            )
                                        },
                                        hide_index=True,
                                        width=width,
                                        num_rows="dynamic",
                                        key=category
                                    )
                                    col1, col2 = st.columns([3,1])
                                    submit_button = col2.form_submit_button(label=f'Submit {category}')
                                    if submit_button:
                                        qty_values = st.session_state.materials_non_stock_and_rentals_df['QTY']
                                        unit_price_values = st.session_state.materials_non_stock_and_rentals_df['UNIT Price']
                                        extended_mask = qty_values.notnull() & unit_price_values.notnull()                                    
                                        st.session_state.materials_non_stock_and_rentals_df.loc[extended_mask, 'EXTENDED'] = np.array(qty_values[extended_mask]) * np.array(unit_price_values[extended_mask])
                                        if st.session_state.get("materials_non_stock_and_rentals_df", None) is None or st.session_state.materials_non_stock_and_rentals_df.empty:
                                            materials_rentals_data = {
                                                'Incurred/Proposed': [None],
                                                'Description': [None],
                                                'QTY': [np.nan],
                                                'UNIT Price': [np.nan],
                                                'EXTENDED': [np.nan]
                                            }
                                            st.session_state.materials_non_stock_and_rentals_df = pd.DataFrame(materials_rentals_data)
                                        st.rerun()
                                    category_total = st.session_state.materials_non_stock_and_rentals_df['EXTENDED'].sum()
                                    category_totals[category] = category_total
                            elif category == 'Subcontractor':
                                with st.form(key='sub_form'):
                                    st.session_state.subcontractor_df = st.data_editor(
                                        st.session_state.subcontractor_df,
                                        column_config={
                                            "QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/4,
                                                step=0.01,
                                                format="%.2f",
                                                min_value=0.00
                                            ),
                                            "Description": st.column_config.TextColumn(
                                                "Description",
                                                help="Description",
                                                width=inwidth/4
                                            ),
                                            "UNIT Price": st.column_config.NumberColumn(
                                                "UNIT Price",
                                                help="Unit Price",
                                                width=inwidth/4,
                                                step=0.01,
                                                format="%.2f",
                                                min_value=0.00
                                            ),
                                            "EXTENDED": st.column_config.NumberColumn(
                                                "EXTENDED",
                                                help="Extended Amount",
                                                width=inwidth/4,
                                                min_value=0.00,
                                                format="%.2f",
                                                disabled=True
                                            )
                                        },
                                        hide_index=True,
                                        width=width,
                                        num_rows="dynamic",
                                        key=category
                                    )
                                    col1, col2 = st.columns([3,1])
                                    submit_button = col2.form_submit_button(label=f'Submit {category}')
                                    if submit_button:
                                        qty_values = st.session_state.subcontractor_df['QTY']
                                        unit_price_values = st.session_state.subcontractor_df['UNIT Price']
                                        extended_mask = qty_values.notnull() & unit_price_values.notnull()
                                        st.session_state.subcontractor_df.loc[extended_mask, 'EXTENDED'] = np.array(qty_values[extended_mask]) * np.array(unit_price_values[extended_mask])
                                        if st.session_state.get("subcontractor_df", None) is None or st.session_state.subcontractor_df.empty:
                                            subcontractor_data = {
                                                'Description': [None],
                                                'QTY': [np.nan],
                                                'UNIT Price': [np.nan],
                                                'EXTENDED': [np.nan]
                                            }
                                            st.session_state.subcontractor_df = pd.DataFrame(subcontractor_data)
                                        st.rerun()
                                    category_total = st.session_state.subcontractor_df['EXTENDED'].sum()
                                    category_totals[category] = category_total
                            st.write(f"****{category} Total : {round(category_totals[category], 2)}****")
                else:
                    with st.expander("Work Description", expanded=False):
                        with st.container():
                            st.text_area('***General description of Incurred:***', value = str(st.session_state.workDesDf["Incurred"].get(0)), disabled=True, height=100)
                            st.text_area('***General description of Proposed work to be performed:***', value = str(st.session_state.workDesDf["Proposed"].get(0)), disabled=True, height=100)
                    st.write(f"NTE_Quote is {st.session_state.NTE_Quote}")
                    categories = ['Labor', 'Trip Charge', 'Parts', 'Miscellaneous Charges', 'Other', 'Subcontractor']

                    if st.session_state.expand_collapse_state:
                        if st.button("Collapse Sections"):
                            changeExpandStatus()
                            st.rerun()
                    else:
                        if st.button("Expand Sections"):
                            changeExpandStatus()
                            st.rerun()

                    category_totals = {}
                    expander_css = """
                    <style>
                    div[data-testid="stExpander"] div[role="button"] p {
                        font-weight: bold;
                    }
                    </style>
                    """
                    st.markdown(expander_css, unsafe_allow_html=True)
                    desired_width = 180
                    for category in categories:
                        if(category.lower().replace(' ', '_').replace('/', '_') == "other"):
                            table_df = getattr(st.session_state, "materials_non_stock_and_rentals_df")
                        else:
                            table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_').replace('/', '_')}_df")
                        if not table_df.empty and 'EXTENDED' in table_df.columns:
                            table_df['EXTENDED'] = pd.to_numeric(table_df['EXTENDED'], errors='coerce')
                            category_total = table_df['EXTENDED'].sum()
                            category_total = round(category_total,2)
                            category_totals[category] = category_total
                            current_title = f"{category} Total: ${category_totals[category]}"
                            # num_spaces = desired_width - len(current_title) - 3
                            num_spaces = 1
                            expanderTitle = f"{category}{'&nbsp;'}Total : ${category_totals[category]}"
                            # expanderTitle = f"{category}{'&nbsp;' * num_spaces}Total : ${category_totals[category]}"
                            # print(current_title, len(current_title), num_spaces, len(current_title) + num_spaces)
                            # print(expanderTitle)
                        else:
                            current_title = f"{category} Total : $0"
                            num_spaces = desired_width - len(current_title)
                            expanderTitle = f"{category}{'&nbsp;'}Total : $0"

                        with st.expander(expanderTitle, expanded=st.session_state.expand_collapse_state):
                            # for category in categories:
                            #     if(category.lower().replace(' ', '_').replace('/', '_') == "other"):
                            #         table_df = getattr(st.session_state, "materials_non_stock_and_rentals_df")
                            #     else:
                            #         table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_').replace('/', '_')}_df")
                            #     print(f"{category.lower().replace(' ', '_').replace('/', '_')}_df")
                            # cleaned_category = category.lower().replace(' ', '_').replace('/', '_')
                            # table_df = getattr(st.session_state, f"{cleaned_category}_df")
                            st.table(table_df)
                            if category == "Parts":
                                st.success("Parts pricing will reflect any additional tariffs from suppliers")
                                
                left_column_content = """
                *NOTE: Total (including tax) INCLUDES ESTIMATED SALES* \n*/ USE TAX*
                """

                col1, col2 = st.columns([1, 1])
                col1.write(left_column_content)
                total_price = 0.0
                tax = st.session_state.ticketDf['Tax_Rate'][0]
                if st.session_state.edit:
                    taxRate = col1.number_input("Please input a tax rate in % (by 2 decimal)",
                                                value=tax,
                                                format="%.2f",
                                                key="tax_rate_input")
                else:
                    taxRate = col1.number_input("Please input a tax rate in % (by 2 decimal)",
                                            value=tax,
                                            disabled=True,
                                            format="%.2f",
                                            key="tax_rate_input")
                if parentDf["Status"].get(0) is not None and (parentDf["Status"].get(0) == "Approved" or parentDf["Status"].get(0) == "Processed"):
                    with col1:
                        st.error("Status is now " + parentDf["Status"].get(0))
                        # incol1, incol2, incol3 = st.columns([1,1,1])            
                # else:
                #     subcol1, subcol2, subcol3 = col1.columns([1, 1, 1])
                #     with subcol1:
                #         if st.session_state.edit and st.sidebar.button("Save Changes"):        
                #             savetime = datetime.now()
                #             updateAll(st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df)
                #             updateParent(st.session_state.ticketN, st.session_state.editable, st.session_state.NTE_Quote, savetime, "1900-01-01 00:00:00.000",  "1900-01-01 00:00:00.000", st.session_state.ticketDf["BranchName"].get(0), "save")
                #             st.success("Successfully updated to database!")   
                #     with subcol2:
                #         st.markdown('<span id="cancel-after"></span>', unsafe_allow_html=True)
                #         if st.session_state.edit and st.sidebar.button("Cancel"):
                #             st.session_state.edit = not st.session_state.edit  # Set edit mode to False
                #             st.rerun()  # Refresh page to reflect changes

 
                category_table_data = []
                for category in categories:
                    if(category.lower().replace(' ', '_').replace('/', '_') == "other"):
                        table_df = getattr(st.session_state, "materials_non_stock_and_rentals_df")
                    else:
                        table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_').replace('/', '_')}_df")
                    if not table_df.empty:
                        category_table_data.append([f"{category} Total", category_totals[category]])
                        total_price += category_totals[category]
                    else:
                        category_table_data.append([f"{category} Total", 0])

                total_price_with_tax = round(total_price * (1 + taxRate / 100.0), 2)

                right_column_content = f"""
                **Price (Pre-Tax)**
                ${total_price:.2f}

                **Estimated Sales Tax**
                ${total_price*taxRate/100:.2f}

                **Total (including tax)**
                ${total_price_with_tax:.2f}
                """
                col2.dataframe(pd.DataFrame(category_table_data, columns=["Category", "Total"]), hide_index=True)
                col2.write(right_column_content)

                script_directory = os.path.dirname(os.path.abspath(__file__))
                pdf_path = os.path.join(script_directory,"input.pdf")
                input_pdf = PdfReader(open(pdf_path, 'rb'))
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                c.setFont("Arial", 9)
                c.drawString(25, 675.55, str(st.session_state.ticketDf['CUST_NAME'].values[0]))
                c.drawString(25, 665.55, str(st.session_state.ticketDf['CUST_ADDRESS1'].values[0]))
                c.drawString(25, 655.55, str(st.session_state.ticketDf['CUST_ADDRESS2'].values[0]) + " " + str(st.session_state.ticketDf['CUST_ADDRESS3'].values[0]) + " " +
                            str(st.session_state.ticketDf['CUST_CITY'].values[0]) + " " + str(st.session_state.ticketDf['CUST_Zip'].values[0]))
                
                c.drawString(50, 582, str(st.session_state.ticketDf['LOC_LOCATNNM'].values[0]))
                c.drawString(50, 572, st.session_state.ticketDf['LOC_Address'].values[0] + " " + st.session_state.ticketDf['CITY'].values[0] + " " + 
                    st.session_state.ticketDf['STATE'].values[0]+ " " + st.session_state.ticketDf['ZIP'].values[0])
                c.drawString(70, 542, str(st.session_state.ticketDf['MailDispatch'].values[0]))
                c.drawString(310, 582, str(st.session_state.ticketN))
                c.drawString(310, 562, str(st.session_state.ticketDf['Purchase_Order'].values[0]))
                
                NTE_QTE = st.session_state.NTE_Quote
                if NTE_QTE is not None:
                    NTE_QTE = "NTE/Quote# " + str(NTE_QTE)
                else:
                    NTE_QTE = "NTE/Quote# None"
                    
                c.setFont("Arial", 8)
                c.drawString(444, 580.55, str(NTE_QTE))
                c.setFont("Arial", 9)
                c.drawString(470, 551, str(formatted_date))
                c.setFont("Arial", 9)

                text_box_width = 560
                text_box_height = 100
                noise = 1.6
                
                incurred_text = "Incurred Workdescription: "+str(st.session_state.workDesDf["Incurred"].get(0))
                proposed_text = "Proposed Workdescription: "+str(st.session_state.workDesDf["Proposed"].get(0))
                general_description = incurred_text + proposed_text

                if len(general_description) > 4500:
                    if len(incurred_text) > 2500:
                        incurred_text = str(st.session_state.workDesDf["Incurred"].get(0))[:2500] + " ... max of 2500 chars"
                    if len(proposed_text) > 2000:
                        proposed_text = str(st.session_state.workDesDf["Proposed"].get(0))[:2000] + " ... max of 2000 chars"
                
                general_description = (
                    incurred_text
                    + "<br/><br/>"
                    + proposed_text
                )
                
                styles = getSampleStyleSheet()
                paragraph_style = styles["Normal"]
                if general_description is not None:
                    paragraph = Paragraph(general_description, paragraph_style)
                else:
                    paragraph = Paragraph("Nothing has been entered", paragraph_style)
                    
                paragraph.wrapOn(c, text_box_width, text_box_height)
                paragraph_height = paragraph.wrapOn(c, text_box_width, text_box_height)[1]
                paragraph.drawOn(c, 25, 485.55 - paragraph_height)

                block_x = 7
                block_width = 577
                block_height = paragraph_height+10
                block_y = 387.55 - (block_height-100)
                border_width = 1.5
                right_block_x = block_x + 10
                right_block_y = block_y
                right_block_width = block_width
                right_block_height = block_height
                c.rect(right_block_x, right_block_y, right_block_width, right_block_height, fill=0)
                c.rect(right_block_x + border_width, right_block_y + border_width, right_block_width - 2 * border_width, right_block_height - 2 * border_width, fill=0)  # Inner border
                c.setFont("Arial", 9)
                # after
                y = 386.55 - (block_height-60)
                margin_bottom = 20
                first_page = True
                new_page_needed = False

                for category in categories:
                    if new_page_needed:
                        c.showPage()
                        first_page = False
                        new_page_needed = False
                        y = 750
                    if(category.lower().replace(' ', '_').replace('/', '_') == "other"):
                        table_df = getattr(st.session_state, "materials_non_stock_and_rentals_df")
                    else:
                        table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_').replace('/', '_')}_df")
                    row_height = 20
                    category_column_width = block_width / 7

                    if table_df.notna().any().any():
                        table_rows = table_df.to_records(index=False)
                        column_names = table_df.columns
                        row_height = 20
                        if(len(column_names)==4):
                            category_column_width = block_width / 6
                        else:
                            category_column_width = block_width / 7

                        if not first_page and y - (len(table_rows) + 4) * row_height < margin_bottom:
                            c.showPage()
                            first_page = False
                            y = 750

                        x = 17
                        col_width = category_column_width
                        for col_name in column_names:
                            if category != 'Labor':
                                if col_name == 'Description':
                                    col_width = category_column_width * 3
                                elif col_name in ['QTY', 'UNIT Price', 'EXTENDED', 'Incurred/Proposed']:
                                    col_width = category_column_width
                            else:
                                if col_name == 'Description':
                                    col_width = category_column_width * noise
                                elif col_name == 'Incurred/Proposed':
                                    col_width = category_column_width 
                                else:
                                    col_width = (577 - category_column_width* (1+noise)) / 5

                            c.rect(x, y, col_width, row_height)
                            c.setFont("Arial", 9)
                            c.drawString(x + 5, y + 5, str(col_name))
                            x += col_width
                        y -= row_height
                        for row in table_rows:
                            x = 17
                            for i, col in enumerate(row):
                                col_name = column_names[i] # Get the column name for the current data cell

                                if category != 'Labor':
                                    if col_name == 'Description':
                                        col_width = category_column_width * 3
                                    elif col_name in ['QTY', 'UNIT Price', 'EXTENDED', 'Incurred/Proposed']:
                                        col_width = category_column_width
                                    else:
                                        col_width = category_column_width # Default
                                else:
                                    if col_name == 'Description':
                                        col_width = category_column_width * noise
                                    elif col_name == 'Incurred/Proposed':
                                        col_width = category_column_width
                                    else:
                                        col_width = (577 - category_column_width * (1 + noise)) / 5

                                if y - row_height < margin_bottom:
                                    c.showPage()
                                    first_page = False
                                    y = 750
                                crop = int(col_width / 7) * 15 # Adjust crop based on calculated col_width
                                c.rect(x, y, col_width, row_height)
                                c.setFont("Arial", 9)
                                if isinstance(col, str):
                                    c.drawString(x + 5, y + 5, col[:crop])
                                else:
                                    c.drawRightString(x + col_width - 5, y + 5, str(col)) # Right align numbers
                                x += col_width
                            y -= row_height
                            if new_page_needed:
                                c.showPage()
                                first_page = False
                                new_page_needed = False
                                y = 750                    

                        category_total = np.round(table_df['EXTENDED'].sum(), 2)
                        c.rect(17, y, block_width, row_height)
                        c.drawRightString(block_width + 12, y + 5, f"{category} Total: {category_total}")
                        y -= row_height

                        if y < margin_bottom:
                            c.showPage()
                            first_page = False
                            y = 750
                            
                total_price_with_tax = round(total_price * (1 + taxRate / 100.0), 2)
                if y - (3 * row_height) < margin_bottom:
                    c.showPage()  # Create a new page
                    first_page = False
                    c.setFont("Arial", 9)
                    y = 750
                c.rect(17, y, block_width, row_height)
                c.drawRightString(block_width + 12, y + 5, f"Price (Pre-Tax): ${total_price:.2f}")
                y -= row_height
                c.rect(17, y, block_width, row_height)
                c.drawRightString(block_width + 12, y + 5, f"Estimated Sales Tax: {total_price*taxRate/100:.2f}")
                y -= row_height
                c.rect(17, y, block_width, row_height)
                c.drawRightString(block_width + 12, y + 5, f"Total (including tax): ${total_price_with_tax:.2f}")
                y -= row_height
                
                c.setFont("Arial", 8)
                c.drawString(17, y - 10, "*Parts pricing will reflect any additional tariffs from suppliers.")
                c.save()
                buffer.seek(0)
                output_pdf = PdfWriter()

                input_pdf = PdfReader(pdf_path)
                text_pdf = PdfReader(buffer)

                for i in range(len(input_pdf.pages)):
                    page = input_pdf.pages[i]
                    if i == 0:
                        page.merge_page(text_pdf.pages[0])
                    output_pdf.add_page(page)

                for page in text_pdf.pages[1:]:
                    output_pdf.add_page(page)

                merged_buffer = io.BytesIO()
                output_pdf.write(merged_buffer)

                merged_buffer.seek(0)

                pdf_content = merged_buffer.read()
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

                if st.session_state.pdf_open:
                    if st.button("Close PDF"):
                        changePdfStatus()
                        st.rerun()
                else:
                    if st.button("Open PDF"):
                        # print(st.session_state.labor_df)
                        changePdfStatus()
                        st.rerun()

                # Display the PDF if open
                if st.session_state.pdf_open:
                    pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="800" height="950" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    # Add a download button for the PDF
                    st.download_button("Download PDF", merged_buffer, file_name=f'{st.session_state.ticketN}-quote.pdf', mime='application/pdf')

            if len(st.session_state.ticketDf) != 0 and "MAJ" in st.session_state.ticketDf['LOC_CUSTNMBR'].get(0):
                if st.sidebar.button("**Send to FMDash**"):
                    token1 = getCredsToken("MAJ0001")
                    checkout(token1['Decrypted_Token_Value'].values[0], st.session_state.ticketDf['Purchase_Order'].values[0])
                    # status = submitFmQuotes(token1, pdf_base64, st.session_state.ticketDf['Purchase_Order'].values[0], str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df, total_price, total_price_with_tax)
                    # dev utest
                    # devCheckout()
                    # status = submitFmQuotesDev(token1, pdf_base64, st.session_state.ticketDf['Purchase_Order'].values[0], str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df, total_price, total_price_with_tax)
                    # st.sidebar.error(status)
                    st.sidebar.error("Please log into customer portal to assess ticket. The page will refresh in 15 secs")
                    time.sleep(15)
                    st.rerun()

            if(len(st.session_state.ticketDf)!=0 and st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "CIR0001"):
                if st.sidebar.button("**Send to CircleK**"):
                    basicCreds = getCredsToken("CIR0001")
                    status = circleK_wo_cost_information(category_totals.get("Labor", 0),
                    category_totals.get("Trip Charge", 0),
                    category_totals.get("Parts", 0),
                    category_totals.get("Miscellaneous Charges", 0),
                    category_totals.get("Materials, Non Stock and Rentals", 0),
                    category_totals.get("Subcontractor", 0),
                    taxRate, st.session_state.ticketDf['Purchase_Order'], basicCreds)
                    st.sidebar.error(status)
                    st.sidebar.error("Please log into customer portal to assess ticket. The page will refresh in 15 secs")
                    time.sleep(15)
                    st.rerun()

            # if(len(st.session_state.ticketDf)!=0 and (st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "MUR0001" or st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "GPM0001" or st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "HER0008")):
            if(len(st.session_state.ticketDf)!=0 and (st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "MUR0001" or st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "HER0008")):
                if st.sidebar.button("**Send to Verisae**"):
                    status = submitQuoteVerisae(st.session_state.ticketDf['CUST_NAME'].get(0), st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)) + str(st.session_state.workDesDf["Proposed"].get(0)), 
                                    category_totals.get("Trip Charge", 0),
                                    category_totals.get("Parts", 0),
                                    category_totals.get("Labor", 0),
                                    category_totals.get("Miscellaneous Charges", 0),
                                    taxRate, st.session_state.ticketDf['Purchase_Order'][0].strip())
                    st.sidebar.error(status)
                    st.sidebar.error("Please log into customer portal to assess ticket. The page will refresh in 15 secs")
                    time.sleep(15)
                    st.rerun()

        # except Exception as e:
        #     st.error("Please enter a ticket number or check the ticket number again")

    def itemizedView():
        st.write("Itemized View function")
    def returnToBid():
        st.write("Return to Bid function")
    def savePDF():
        st.write("Save PDF & Load to Email function")
    def returnToForm():
        st.write("returntoForm")
    def feeCharge():
        fee_charge_types = st.session_state.misc_ops_df

        st.subheader("Fee Charge Types")
        
        df = pd.DataFrame(fee_charge_types, columns=["Fee Charge Type", "Fee Amount"])
        st.table(df)

    def payRate():
        st.subheader("Pay Rate Info")
        st.subheader(st.session_state.ticketN)
        if st.session_state.ticketN:
            billing_amount_1 = st.session_state.LRatesDf['Billing_Amount']
            pay_code_description_1 = st.session_state.LRatesDf['Pay_Code_Description']
            df1 = pd.DataFrame({"Billing_Amount": billing_amount_1, "Pay_Code_Description": pay_code_description_1})

            billing_amount_2 = st.session_state.TRatesDf['Billing_Amount']
            pay_code_description_2 = st.session_state.TRatesDf['Pay_Code_Description']
            df2 = pd.DataFrame({"Billing_Amount": billing_amount_2, "Pay_Code_Description": pay_code_description_2})

            st.subheader("Payrate - Labor_Charge")
            st.table(df1)

            st.subheader("Payrate - Travels")
            st.table(df2)

def ticketInfo():
    st.subheader("Ticket Info")
    st.subheader(st.session_state.ticketN)
    if st.session_state.ticketN:
        transposed_df = st.session_state.ticketDf.transpose()
        st.table(transposed_df)
    else:
        st.warning("no ticket Number")

def pricing():
    st.subheader("Pricing")
    st.subheader(st.session_state.ticketN)
    if st.session_state.ticketN:
        st.table(st.session_state.pricingDf)
    else:
        st.warning("no ticket Number")

# def NTEQuoteQue():
#     st.subheader("this is the ticket approval page")
#     if 'ticketN' in st.session_state and st.session_state.ticketN:
#         # if st.session_state.refresh_button or st.session_state.ticketDf is None:
#         #     st.session_state.refresh_button = False
#             concatenated_branches = ""
#             if len(st.session_state.selected_branches) >= 2:
#                 concatenated_branches = ", ".join(st.session_state.selected_branches[:2])
#             elif len(st.session_state.selected_branches) == 1:
#                 concatenated_branches = st.session_state.selected_branches[0]
#             print(concatenated_branches)
#             st.session_state.parentDf = getParent(st.session_state.selected_branches)
#             st.session_state.parentDf = st.data_editor(
#                 st.session_state.parentDf,
#                 column_config={
#                     "QTY": st.column_config.NumberColumn(
#                         "QTY",
#                         help="Quantity",
#                         width=700/4,
#                         min_value=0,
#                         step=1
#                     ),
#                     },
#                     hide_index=False,
#                     key="parent"
#                     )

def main():
    st.set_page_config("Universal Quote Template",layout="wide")
    help_icon = Image.open("help.png")

    with open("help.png", "rb") as img_file:
        encoded_img = base64.b64encode(img_file.read()).decode()

    # Display the image as a clickable "button"
    st.markdown(
        """
        <style>
        /* Universal Button Styling */
        .stButton button {
            background-color: #0099FF; /* Default blue background */
            color: #FFFFFF; /* White text */
            border: 2px solid #003366; /* Dark blue border */
            width: 160px; /* Fixed width */
            min-height: 50px; /* Minimum height */
            padding: 10px 20px; /* Consistent padding */
            font-size: 16px; /* Font size */
            border-radius: 5px; /* Rounded corners */
            text-align: center;
            display: inline-block;
            line-height: 1.2; /* Allow multiple lines of text */
            word-wrap: break-word; /* Wrap long words */
            white-space: normal; /* Allow text wrapping */
            transition: all 0.3s ease; /* Smooth transition for hover effects */
        }
        [data-testid="stSidebar"] .stButton button {
            background-color: #003356; /* Dark blue background */
            color: #ffffff; /* White text */
            font-weight: bold; /* Bold text for better emphasis */
            border: 1px solid #002740; /* Darker blue border */
            width: 140px; /* Fixed width */
            min-height: 40px; /* Minimum height */
            padding: 8px 16px; /* Smaller padding */
            font-size: 14px; /* Smaller font size */
            border-radius: 3px; /* Slightly rounded corners */
            text-align: center;
            display: inline-block;
            line-height: 1.2; /* Allow multiple lines of text */
            word-wrap: break-word; /* Wrap long words */
            white-space: normal; /* Allow text wrapping */
            transition: all 0.3s ease; /* Smooth transition for hover effects */
        }
        [data-testid="stSidebar"] .stButton button:hover {
            background-color: #002740; /* Darker blue on hover */
            color: #ffffff; /* White text on hover */
            transform: scale(1.02); /* Slight scale on hover */
            box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.1); /* Subtle shadow */
            font-weight: bold; /* Ensure bold text is retained on hover */
        }
        
        .stFormSubmitButton button {
            background-color: #0099FF; /* Default blue background */
            color: #FFFFFF; /* White text */
            border: 2px solid #003366; /* Dark blue border */
            width: 250px; /* Fixed width */
            min-height: 50px; /* Minimum height */
            padding: 10px 20px; /* Consistent padding */
            font-size: 16px; /* Font size */
            border-radius: 5px; /* Rounded corners */
            text-align: center;
            display: inline-block;
            line-height: 1.2; /* Allow multiple lines of text */
            # word-wrap: break-word; /* Wrap long words */
            white-space: normal; /* Allow text wrapping */
            transition: all 0.3s ease; /* Smooth transition for hover effects */
        }
        .stButton button:hover, .stFormSubmitButton button:hover {
            background-color: #003366; /* Darker blue on hover */
            color: #FFFFFF; /* White text on hover */
            transform: scale(1.05); /* Slight scale on hover */
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2); /* Subtle shadow */
        }

        /* Adjust Dynamic Height Based on Content */
        .stButton button {
            display: flex; /* Flexbox layout for dynamic sizing */
            align-items: center; /* Center align vertically */
            justify-content: center; /* Center align horizontally */
            min-height: 50px; /* Base height */

        }/* Floating Help Button */
        .floating-help-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            z-index: 1000;
            cursor: pointer;
        }
        .floating-help-button img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .floating-help-button img:hover {
            transform: scale(1.1);
            box-shadow: 0px 6px 10px rgba(0, 0, 0, 0.2);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # cancel button
    st.markdown(
        """
        <style>
        .element-container:has(#approve-after) + div [data-testid="stSidebar"] .stButton button {
            background-color: #159223; /* Green */
            border-color: #034f0c;
            position: fixed;
            top: 10%; /* 10% from the top of the screen */
            right: 35%; /* 30% from the right of the screen */
            z-index: 1000;
        }

            
        .element-container:has(#approve-after) {
            display: none; /* Hide certain elements */
        }

        .element-container:has(#decline-after) + div [data-testid="stSidebar"] .stButton button {
            background-color: #d30000; /* Red */
            border-color: #921515;
            position: fixed;
            top: 10%; /* 10% from the top of the screen */
            right: 20%; /* 20% from the right of the screen */
            z-index: 1000;
        }

        .element-container:has(#decline-after) {
            display: none; /* Hide certain elements */
        }

        .element-container:has(#delete-after) + div [data-testid="stSidebar"] .stButton button {
            background-color:rgb(211, 123, 0); /* Red */
            border-color:rgba(202, 118, 1, 0.69);
            position: fixed;
            top: 10%; /* 10% from the top of the screen */
            right: 5%; /* 20% from the right of the screen */
            z-index: 1000;
            border: 2px solid #414141; /* Border color */
            padding: 10px 20px; /* Padding for better button spacing */
            font-size: 16px; /* Font size */
            border-radius: 5px; /* Rounded corners */
            text-align: center; /* Align text in the center */
            cursor: pointer; /* Pointer cursor on hover */
            transition: all 0.3s ease; /* Smooth hover effect */
            display: inline-block; /* Keeps button inline */
        }

        .element-container:has(#delete-after) {
            display: none; /* Hide certain elements */
        }

        /* Hide content when an element with 'cancel' ID exists */
        .element-container:has(#cancel-after) + div button {
        background-color: #898989; /* Button color */
        border: 2px solid #414141; /* Border color */
        color: #ffffff; /* Text color */
        padding: 10px 20px; /* Padding for better button spacing */
        font-size: 16px; /* Font size */
        border-radius: 5px; /* Rounded corners */
        text-align: center; /* Align text in the center */
        cursor: pointer; /* Pointer cursor on hover */
        transition: all 0.3s ease; /* Smooth hover effect */
        display: inline-block; /* Keeps button inline */
        }

        .element-container:has(#cancel-after) {
            display: none; /* Hide certain elements */
        }

        /* General button styling */
        .stButton > button {
            font-size: 16px;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #414141;
            color: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Floating Help Button
    st.markdown(
        f"""
        <a href="https://scribehow.com/embed/Universal_Quote_Template__237rIL_ESWei_zzNG1yp8A?as=scrollable" 
        target="_blank" class="floating-help-button">
            <img src="data:image/png;base64,{encoded_img}" alt="Help Icon">
        </a>
        """,
        unsafe_allow_html=True,
    )

    #         if st.button("⭳", type="primary"):
    #             st.session_state.show = False
    #             st.rerun()
    #     else:
    #         if st.button("⭱", type="secondary"):
    #             st.session_state.show = True
    #             st.rerun()

    # if st.session_state.show:
    # vid_y_pos = "0px"  
    # button_css = float_css_helper(width="2.2rem", right="4rem", bottom="400px", transition=0)
    # else:

    selected_branches = st.sidebar.multiselect("Select Branches", st.session_state.branch['BranchName'], key="select_branches", default=["Sanford"])
    if len(selected_branches) > 0 and selected_branches != st.session_state.selected_branches:
        st.session_state.selected_branches = selected_branches  

    if ('ticketN' in st.session_state and not st.session_state.ticketN):
            st.session_state.parentDf = getParent(st.session_state.selected_branches) 
            st.session_state.parentDf = st.data_editor(
                st.session_state.parentDf,
                column_config={
                    "TicketID": st.column_config.Column(
                        "TicketID",
                        help="Ticket ID",
                        disabled=True
                    ),
                    "Branch": st.column_config.Column(
                        "Branch",
                        help="Branch",
                        disabled=True
                    ),
                    "Status": st.column_config.Column(
                        "Status",
                        help="Status",
                        # options=["open", "close", "pending"],
                        disabled=True

                    ),
                    "NTE_QUOTE": st.column_config.SelectboxColumn(
                        "NTE_QUOTE",
                        help="NTE QUOTE",
                        options=["NTE", "QUOTE"],
                        required=True,
                        disabled=True
                    ),
                    "Editable": st.column_config.CheckboxColumn(
                        "Editable",
                        help="Editable",
                        required=True,
                        disabled=True
                    ),
                    "Insertdate": st.column_config.Column(
                        "Insertdate",
                        help="Insert Date",
                        disabled=True
                    ),
                    "Approvedate": st.column_config.Column(
                        "Approvedate",
                        help="Approve Date",
                        disabled=True
                    ),
                    "Declinedate": st.column_config.Column(
                        "Declinedate",
                        help="Decline Date",
                        disabled=True
                    )
                    },
                    hide_index=True,
                    key="parent"
                    )
                # NTEQuoteQue()
            # if(not st.session_state.refresh_button):
            #     st.session_state.refresh_button = st.sidebar.button("Refresh")
            st.session_state.ticketN = st.text_input("Enter ticket number:")
            # params = st.experimental_get_query_params()
            # if params and params['TicketID']:
            #     st.session_state.ticketN = params['TicketID'][0]
            if(st.session_state.ticketN):
                st.rerun()
    else:
        mainPage()
        

    # mainPage()
    # st.sidebar.title("Select Page")
    # hide_menu_style = """
    #     <style>
    #     #MainMenu {visibility: hidden; }
    #     footer {visibility: hidden;}
    #     </style>
    #         """
    # st.markdown(hide_menu_style, unsafe_allow_html=True)
    # selection = st.sidebar.radio("Select Page", ["Main Page", "Fee Charge", "Pay Rate", "Ticket Info", "Pricing"])

    # if selection == "Main Page":
    # elif selection == "Fee Charge":
    #     feeCharge()
    # elif selection == "Pay Rate":
    #     payRate()
    # elif selection == "Ticket Info":
    #     ticketInfo()
    # elif selection == "Pricing":
    #     pricing()
import threading
import threading, time, pytz
from datetime import datetime, timedelta
from gilbarco_scrape import devscrape   # make sure this import path matches your project

def run_daily_dev_scrape():
    """Run devscrape() every day at 6 AM Eastern Time."""
    tz_est = pytz.timezone("US/Eastern")

    while True:
        now_est = datetime.now(tz_est)
        target_time = now_est.replace(hour=6, minute=0, second=0, microsecond=0)

        # if it's already past 6 AM today → schedule for tomorrow
        if now_est >= target_time:
            target_time += timedelta(days=1)

        wait_seconds = (target_time - now_est).total_seconds()

        print(f"🕕 Next devscrape() scheduled for: {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')} "
              f"({int(wait_seconds)} seconds from now)")
        time.sleep(wait_seconds)

        try:
            print(f"🚀 Starting devscrape() at {datetime.now(tz_est).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            devscrape()
            print(f"✅ devscrape() finished at {datetime.now(tz_est).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        except Exception as e:
            print(f"❌ Error during devscrape run: {e}")

        # Sleep 60 seconds to avoid retriggering immediately if system clock drifts
        time.sleep(60)

if __name__ == "__main__":
    # Start your main process
    main()
    threading.Thread(target=run_daily_dev_scrape, daemon=True).start()
    # --- optional: start another process like Streamlit, etc.
    # print("Go to: http://localhost:8501/")
    # sys.argv = ["streamlit", "run", "app2.py"]
    # sys.exit(stcli.main())

    # Keep main alive if needed
    while True:
        pass
