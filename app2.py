import streamlit as st
import pandas as pd
import requests
from PIL import Image
from streamlit_float import *
import io
import base64
import random
from streamlit.components.v1 import html
import time
from io import BytesIO
from reportlab.lib.pagesizes import letter
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
from datetime import datetime
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Paragraph
import numpy as np
import re
from api.fmDash import submitFmQuotes
from api.fmDash import checkout
from api.verisae import submitQuoteVerisae
from api.circleK import wo_cost_information
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
# if 'filtered_ticket' not in st.session_state:
#     st.session_state.filtered_ticket = [event for event in st.session_state.filtered_ticket if event['BranchShortName'] in st.session_state.selected_branches]

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
    ]
    for var_name in state_variables:
        st.session_state[var_name] = None
    st.session_state.edit = False
    st.experimental_set_query_params()
    st.experimental_rerun()
def mainPage():
    if "labor_df" not in st.session_state:
        st.session_state.labor_df = pd.DataFrame()
        st.session_state.trip_charge_df = pd.DataFrame()
        st.session_state.parts_df = pd.DataFrame()
        st.session_state.miscellaneous_charges_df = pd.DataFrame()
        st.session_state.materials_non_stock_and_rentals_df = pd.DataFrame()
        st.session_state.subcontractor_df = pd.DataFrame()
    image = Image.open("Header.jpg")
    image_height = 200
    resized_image = image.resize((int(image_height * image.width / image.height), image_height))

    st.subheader("Main Page")
    st.write("Welcome to the main page of the Fee Charge Types application.")
    # try:
    if 'ticketN' in st.session_state and st.session_state.ticketN:
        if st.session_state.ticketDf is None:
            # st.session_state.refresh_button = False
            st.session_state.ticketDf, st.session_state.LRatesDf, st.session_state.TRatesDf, st.session_state.misc_ops_df= getAllPrice(st.session_state.ticketN)
            workDes = getDesc(ticket=st.session_state.ticketN)
            if workDes is None or workDes.empty:
                st.session_state.workDescription = "Please input"
                st.session_state.workDesDf = pd.DataFrame({"TicketID":[st.session_state.ticketN], "Incurred":[st.session_state.workDescription], "Proposed":[st.session_state.workDescription]})
            else:
                st.session_state.workDesDf = workDes
            st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df = getAllTicket(ticket=st.session_state.ticketN)
        if st.sidebar.button("goBack", key="5"):
            refresh()
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
                    
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("Edit", key="1"):
                    st.session_state.edit = True
            with col2:
                if st.button("View", key="2"):
                    st.session_state.edit = False
            
            col1, col2 = st.columns((2,1))
            df_left = pd.DataFrame(left_data)
            left_table_styles = [
                {'selector': 'table', 'props': [('text-align', 'left'), ('border-collapse', 'collapse')]},
                {'selector': 'th, td', 'props': [('padding', '8px'), ('border', '1px solid black')]}
            ]
            df_left_styled = df_left.style.set_table_styles(left_table_styles)

            col1.dataframe(df_left_styled, hide_index=True)
            col2.image(resized_image, width=300)

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
            if st.session_state.get("miscellaneous_charges_df", None) is None or st.session_state.miscellaneous_charges_df.empty:
                misc_charges_data = {
                    'Description': [None],
                    'QTY': [None],
                    'UNIT Price': [None],
                    'EXTENDED': [None]
                }
                st.session_state.miscellaneous_charges_df = pd.DataFrame(misc_charges_data)

            if st.session_state.get("materials_non_stock_and_rentals_df", None) is None or st.session_state.materials_non_stock_and_rentals_df.empty:
                materials_rentals_data = {
                    'Description': [None],
                    'QTY': [None],
                    'UNIT Price': [None],
                    'EXTENDED': [None]
                }
                st.session_state.materials_non_stock_and_rentals_df = pd.DataFrame(materials_rentals_data)

            if st.session_state.get("subcontractor_df", None) is None or st.session_state.subcontractor_df.empty:
                subcontractor_data = {
                    'Description': [None],
                    'QTY': [None],
                    'UNIT Price': [None],
                    'EXTENDED': [None]
                }
                st.session_state.subcontractor_df = pd.DataFrame(subcontractor_data)
            st.write("**UNLESS SPECIFICALLY NOTED, THIS PROPOSAL IS VALID FOR 30 DAYS FROM THE DATE ABOVE**")
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

                categories = ['Labor', 'Trip Charge', 'Parts', 'Miscellaneous Charges', 'Materials/Non Stock and Rentals', 'Subcontractor']
                category_totals = {category: 0 for category in categories}

                for category in categories:
                    with st.expander(f"******{category}******", expanded=True):
                        st.title(category)
                        if category == 'Parts':
                            prev_input_letters = ""
                            st.session_state.input_letters = st.text_input("First enter Part Id or Parts Desc:", max_chars=15).upper()
                            if st.session_state.input_letters != prev_input_letters and len(st.session_state.input_letters) > 0:
                                st.session_state.pricingDf = getBinddes(st.session_state.input_letters)
                                prev_input_letters = st.session_state.input_letters
                        width = 800
                        inwidth = 500
                        if category == 'Labor':
                            category_total = 0
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
                                    key=category+"df"
                                )
                                col1, col2 = st.columns([3,1])
                                submit_button = col2.form_submit_button(label='Submit')
                                if not newLabordf.empty:
                                    if submit_button:
                                        qty_values = newLabordf["Nums of Techs"]
                                        hours_values = newLabordf["Hours per Tech"]
                                        qty_mask = qty_values.notnull() & hours_values.notnull()
                                        newLabordf.loc[qty_mask, 'QTY'] = np.array(qty_values[qty_mask]) * np.array(hours_values[qty_mask])
                                        description_values = newLabordf['Description']
                                        rate_mask = description_values.notnull()
                                        newLabordf.loc[rate_mask, 'Hourly Rate'] = description_values[rate_mask].apply(lambda x: float(re.search(r'(\d+(\.\d+)?)', x).group()))
                                        extended_mask = qty_mask & rate_mask
                                        qty_values = np.array(newLabordf.loc[qty_mask, 'QTY'], dtype=float)
                                        hourly = np.array(newLabordf.loc[rate_mask, 'Hourly Rate'], dtype=float)
                                        rounded_extended_values = np.round(np.array(qty_values) * np.array(hourly), 2)
                                        newLabordf.loc[extended_mask, 'EXTENDED'] = rounded_extended_values
                                        newLabordf = newLabordf.dropna()
                                        st.session_state.labor_df = pd.concat([st.session_state.labor_df, newLabordf], ignore_index=True)
                                        st.empty()
                                        st.experimental_rerun()
                                    category_totals[category] = newLabordf['EXTENDED'].sum() + category_total
                                    st.session_state.labor_df.dropna(how='all', inplace=True)
                                if not st.session_state.labor_df.empty:
                                    st.write("Archived Labor (Delete row when necessary please dont add rows)")
                                    st.session_state.labor_df = st.data_editor(
                                        st.session_state.labor_df,
                                        column_config={
                                            "Incurred/Proposed": st.column_config.SelectboxColumn(
                                                "Incurred/Proposed",
                                                help="Incurred",
                                                width=inwidth/6,
                                                disabled=True,
                                                options=["Incurred", "Proposed"],
                                            ),
                                            "Description": st.column_config.SelectboxColumn(
                                                "Description",
                                                help="Description",
                                                width=inwidth/6,
                                                disabled=True,
                                                options=concatenated_values
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
                                                disabled=True,
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
                                    category_total = st.session_state.labor_df['EXTENDED'].sum()
                        elif category == 'Trip Charge':
                            category_total = 0
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
                                                min_value=0,
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
                                                min_value=0,
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
                                submit_button = col2.form_submit_button(label='Submit')
                                if not newTripdf.empty:
                                    if submit_button:
                                        desc_mask = newTripdf['Description'].notnull()
                                        qty_mask = newTripdf["QTY"].notnull()
                                        qty_values = newTripdf.loc[qty_mask,"QTY"]
                                        description_values = newTripdf.loc[desc_mask,"Description"]
                                        incurred_mask = newTripdf['Incurred/Proposed'].notnull()
                                        rate_mask = desc_mask & newTripdf['UNIT Price'].isnull() 
                                        newTripdf = newTripdf[incurred_mask & qty_mask & desc_mask]
                                        newTripdf.loc[rate_mask, 'UNIT Price'] = description_values[rate_mask].apply(lambda x: float(re.search(r'(\d+(\.\d+)?)', x).group()))
                                        rate_mask = newTripdf['UNIT Price'].notnull()
                                        extended_mask = qty_mask & rate_mask
                                        qty_values = np.array(newTripdf.loc[rate_mask, 'QTY'], dtype=float)
                                        unitPrice = np.array(newTripdf.loc[rate_mask, 'UNIT Price'], dtype=float)
                                        extended_values = np.array(qty_values) * np.array(unitPrice)
                                        rounded_extended_values = np.round(extended_values, 2)
                                        newTripdf.loc[extended_mask, 'EXTENDED'] = rounded_extended_values
                                        newTripdf = newTripdf.dropna()
                                        st.session_state.trip_charge_df = pd.concat([st.session_state.trip_charge_df, newTripdf], ignore_index=True)
                                        st.experimental_rerun()
                                    category_totals[category] = newTripdf['EXTENDED'].sum() + category_total
                                    col1.write("<small>Please enter Unit Price if 0</small>", unsafe_allow_html=True)
                                if not st.session_state.trip_charge_df.empty:
                                    st.write("Archived Trip/Travel Charge (Delete row when necessary please dont add rows)")
                                    st.session_state.trip_charge_df = st.data_editor(
                                        st.session_state.trip_charge_df,
                                        column_config={
                                            "Incurred/Proposed": st.column_config.SelectboxColumn(
                                                "Incurred/Proposed",
                                                help="Incurred",
                                                width=inwidth/6,
                                                options=["Incurred", "Proposed"],
                                                disabled=True
                                            ),"QTY": st.column_config.NumberColumn(
                                                "QTY",
                                                help="Quantity",
                                                width=inwidth/6,
                                                min_value=0,
                                                disabled=True
                                            ),
                                            "Description": st.column_config.SelectboxColumn(
                                                "Description",
                                                help="Description",
                                                width=inwidth/4,
                                                options=concatenated_values,
                                                disabled=True
                                            ),
                                            "UNIT Price": st.column_config.NumberColumn(
                                                "UNIT Price",
                                                help="Unit Price",
                                                width=inwidth/4,
                                                min_value=0.00,
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
                                    category_total = st.session_state.trip_charge_df['EXTENDED'].sum()
                        elif category == 'Parts':
                            category_total = 0
                            # new
                            with st.form(key='parts_form', clear_on_submit=True):
                                col1, col2 = st.columns([3, 3])
                                col1.write("New Parts")
                                col2.warning("add new Parts after searching parts above")
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
                                submit_button = col2.form_submit_button(label='Submit')
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
                                        selling_prices = partsPriceDf['SellingPrice'].astype(float)
                                        unit_mask = newParts_df['UNIT Price'].isnull()
                                        newParts_df.loc[unit_mask, 'UNIT Price'] = selling_prices.values
                                        if newParts_df['EXTENDED'].isnull().any():
                                            extended_mask = newParts_df['EXTENDED'].isnull()
                                            newParts_df.loc[extended_mask, 'EXTENDED'] = newParts_df.loc[extended_mask, 'UNIT Price'] * qty_values
                                        st.session_state.parts_df = pd.concat([st.session_state.parts_df, newParts_df], ignore_index=True)
                                        st.experimental_rerun()
                                category_total = category_total + newParts_df['EXTENDED'].sum()
                                category_totals[category] = category_total
                            if not st.session_state.trip_charge_df.empty:
                                st.write("Archived Parts (Delete row when necessary please dont add rows)")
                                st.session_state.parts_df = st.data_editor(
                                    st.session_state.parts_df,
                                    column_config={
                                        "Incurred/Proposed": st.column_config.SelectboxColumn(
                                            "Incurred/Proposed",
                                            help="Incurred",
                                            width=inwidth/6,
                                            options=[],
                                            disabled=True
                                        ),
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
                                            options=[''],
                                            disabled=True
                                        ),
                                        "UNIT Price": st.column_config.NumberColumn(
                                            "UNIT Price",
                                            help="Unit Price",
                                            width=inwidth/4,
                                            min_value=0.00,
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
                                category_total = st.session_state.parts_df['EXTENDED'].sum()
                        elif category == 'Miscellaneous Charges':
                            string_values = [" : "+f'{value:.2f}'.rstrip('0').rstrip('.') for value in st.session_state.misc_ops_df['Fee_Amount']]
                            concatenated_values = [description + value for description, value in zip(st.session_state.misc_ops_df['Fee_Charge_Type'], string_values)]
                            with st.form(key='Misc_form'):
                                st.session_state.miscellaneous_charges_df = st.data_editor(
                                    st.session_state.miscellaneous_charges_df,
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
                                col1, col2 = st.columns([3,1])
                                submit_button = col2.form_submit_button(label='Submit')
                                if not st.session_state.miscellaneous_charges_df.empty:
                                    if submit_button:
                                        qty_values = st.session_state.miscellaneous_charges_df['QTY']
                                        mask = qty_values.notnull() & st.session_state.miscellaneous_charges_df['Description'].notnull()
                                        st.session_state.miscellaneous_charges_df.loc[mask, 'UNIT Price'] = st.session_state.miscellaneous_charges_df.loc[mask,'Description'].apply(lambda x: float(re.search(r'(\d+(\.\d+)?)', x).group()))
                                        unit_price_values = st.session_state.miscellaneous_charges_df.loc[mask,'UNIT Price']
                                        st.session_state.miscellaneous_charges_df.loc[mask, 'EXTENDED'] = np.array(qty_values[mask], dtype=float) * np.array(unit_price_values[mask], dtype=float)
                                        
                                        st.experimental_rerun()
                                    category_total = st.session_state.miscellaneous_charges_df['EXTENDED'].sum()
                                    category_totals[category] = category_total
                        elif category == 'Materials/Non Stock and Rentals':
                            with st.form(key=f'{category}_form'):
                                st.session_state.materials_non_stock_and_rentals_df = st.data_editor(
                                    st.session_state.materials_non_stock_and_rentals_df,
                                    column_config={
                                        "QTY": st.column_config.NumberColumn(
                                            "QTY",
                                            help="Quantity",
                                            width=inwidth/4,
                                            min_value=0,
                                            
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
                                submit_button = col2.form_submit_button(label='Submit')
                                if not st.session_state.materials_non_stock_and_rentals_df.empty:
                                    if submit_button:
                                        qty_values = st.session_state.materials_non_stock_and_rentals_df['QTY']
                                        unit_price_values = st.session_state.materials_non_stock_and_rentals_df['UNIT Price']
                                        extended_mask = qty_values.notnull() & unit_price_values.notnull()
                                        st.session_state.materials_non_stock_and_rentals_df = st.session_state.materials_non_stock_and_rentals_df[extended_mask]
                                        st.session_state.materials_non_stock_and_rentals_df.loc[extended_mask, 'EXTENDED'] = np.array(qty_values[extended_mask]) * np.array(unit_price_values[extended_mask])
                                        st.experimental_rerun()
                                    category_total = st.session_state.materials_non_stock_and_rentals_df['EXTENDED'].sum()
                                    category_totals[category] = category_total
                        elif category == 'Subcontractor':
                            with st.form(key='sub_form', clear_on_submit=True):
                                st.session_state.subcontractor_df = st.data_editor(
                                    st.session_state.subcontractor_df,
                                    column_config={
                                        "QTY": st.column_config.NumberColumn(
                                            "QTY",
                                            help="Quantity",
                                            width=inwidth/4,
                                            min_value=0,
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
                                submit_button = col2.form_submit_button(label='Submit')
                                if not st.session_state.subcontractor_df.empty:
                                    if submit_button:
                                        qty_values = st.session_state.subcontractor_df['QTY']
                                        unit_price_values = st.session_state.subcontractor_df['UNIT Price']
                                        extended_mask = qty_values.notnull() & unit_price_values.notnull()
                                        st.session_state.subcontractor_df.loc[extended_mask, 'EXTENDED'] = np.array(qty_values[extended_mask]) * np.array(unit_price_values[extended_mask])
                                        st.experimental_rerun()
                                    category_total = st.session_state.subcontractor_df['EXTENDED'].sum()
                                    category_totals[category] = category_total
                    col1.write(f"****{category} Total : {round(category_totals[category], 2)}****")
            else:
                with st.expander("Work Description", expanded=False):
                    with st.container():
                        st.text_area('***General description of Incurred:***', value = str(st.session_state.workDesDf["Incurred"].get(0)), disabled=True, height=100)
                        st.text_area('***General description of Proposed work to be performed:***', value = str(st.session_state.workDesDf["Proposed"].get(0)), disabled=True, height=100)
                st.write(f"NTE_Quote is {st.session_state.NTE_Quote}")
                categories = ['Labor', 'Trip Charge', 'Parts', 'Miscellaneous Charges', 'Materials/Non Stock and Rentals', 'Subcontractor']
                
                if st.button("Expand or Collapse all"):
                    st.session_state.expand_collapse_state = not st.session_state.expand_collapse_state
                    st.experimental_rerun()

                category_totals = {}
                expander_css = """
                <style>
                div[data-testid="stExpander"] div[role="button"] p {
                    font-weight: bold;
                }
                </style>
                """
                st.markdown(expander_css, unsafe_allow_html=True)
                desired_width = 130
                for category in categories:
                    table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_').replace('/', '_')}_df")
                    if not table_df.empty and 'EXTENDED' in table_df.columns:
                        category_total = table_df['EXTENDED'].sum()
                        category_totals[category] = category_total
                        current_title = f"{category} Total: ${category_totals[category]}"
                        num_spaces = desired_width - len(current_title)
                        expanderTitle = f"{category}{' &nbsp;' * num_spaces}Total: ${category_totals[category]}"
                    else:
                        current_title = f"{category} Total : $0"
                        num_spaces = desired_width - len(current_title)
                        expanderTitle = f"{category}{' &nbsp;' * num_spaces}Total : $0"
                
                    

                    with st.expander(expanderTitle, expanded=st.session_state.expand_collapse_state):
                        cleaned_category = category.lower().replace(' ', '_').replace('/', '_')
                        table_df = getattr(st.session_state, f"{cleaned_category}_df")
                        st.table(table_df)
                            
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
                    incol1, incol2, incol3 = st.columns([1,1,1])            
            else:
                with col1:
                    if st.button("Save"):        
                        savetime = datetime.now()
                        updateAll(st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df)
                        updateParent(st.session_state.ticketN, st.session_state.editable, st.session_state.NTE_Quote, savetime, "1900-01-01 00:00:00.000",  "1900-01-01 00:00:00.000", st.session_state.ticketDf["BranchName"].get(0), "save")
                        st.success("Successfully updated to database!")      
                    incol1, incol2, incol3 = st.columns([1,1,1])
                    with incol1:
                        if st.button(str(st.session_state.NTE_Quote)+" Approve", key="3"):
                            approvetime = datetime.now()
                            approve = approvetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            st.session_state.editable = 0
                            updateAll(st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df)
                            updateParent(st.session_state.ticketN, st.session_state.editable, st.session_state.NTE_Quote, "1900-01-01 00:00:00.000", approve,  "1900-01-01 00:00:00.000", st.session_state.ticketDf["BranchName"].get(0), "approve")
                            st.success("Successfully updated to Gp!")
                            refresh()
                    with incol2:
                        if st.button(str(st.session_state.NTE_Quote)+"\nDecline", key="4"):
                            declinetime = datetime.now()
                            decline = declinetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            updateAll(st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df)
                            updateParent(st.session_state.ticketN, 1, st.session_state.NTE_Quote, "1900-01-01 00:00:00.000",  "1900-01-01 00:00:00.000", decline, st.session_state.ticketDf["BranchName"].get(0), "decline")
                            st.success("Successfully updated to declined!")
                            refresh()
                    incol1, incol2, incol3 = st.columns([1,1,1])            
            category_table_data = []
            for category in categories:
                table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_').replace('/', '_')}_df")
                if not table_df.empty:
                    category_table_data.append([f"{category} Total", category_totals[category]])
                    total_price += category_totals[category]
                else:
                    category_table_data.append([f"{category} Total", 0])

            total_price_with_tax = total_price * (1 + taxRate / 100.0)

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

            input_pdf = PdfReader(open('input.pdf', 'rb'))
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
                        c.rect(x, y, col_width, row_height)
                        c.setFont("Arial", 9)
                        c.drawString(x + 5, y + 5, str(col_name))
                        x += col_width
                    y -= row_height
                    for row in table_rows:
                        x = 17
                        count = 0
                        next_width = None
                        for col in row:
                            if count == 0:
                                col_width = category_column_width * 3
                            else:
                                col_width = next_width if next_width else category_column_width

                            if col in ['Incurred', 'Proposed', None]:
                                col_width = category_column_width
                                next_width = category_column_width * 3
                            else:
                                next_width = None
                            if col is not None and isinstance(col, str):
                                match = re.match(r'^[^:\d.]+.*', col)
                                if match:
                                    if y - row_height < margin_bottom:
                                        c.showPage()
                                        first_page = False
                                        y = 750
                                    first_string = match.group()
                                    if category == 'Labor' or category == 'Miscellaneous Charges' or category == 'Trip Charge':
                                        first_string = re.sub(r":.*", "", first_string)
                                    if category == 'Labor':
                                        col_width = category_column_width
                                    c.rect(x, y, col_width, row_height)
                                    c.setFont("Arial", 9)
                                    crop = 47
                                    if len(str(first_string)) < crop:
                                        c.drawString(x + 5, y + 5, str(first_string))
                                    else:
                                        c.drawString(x + 5, y + 5, str(first_string)[:crop])
                            else:
                                if category == 'Labor':
                                    col_width = category_column_width
                                c.rect(x, y, col_width, row_height)
                                c.setFont("Arial", 9)
                                c.drawString(x + 5, y + 5, str(col))
                            x += col_width
                            count+=1
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
                        
            total_price_with_tax = total_price * (1 + taxRate / 100.0)
            c.rect(17, y, block_width, row_height)
            c.drawRightString(block_width + 12, y + 5, f"Price (Pre-Tax): ${total_price:.2f}")
            y -= row_height
            c.rect(17, y, block_width, row_height)
            c.drawRightString(block_width + 12, y + 5, f"Estimated Sales Tax: {total_price*taxRate/100:.2f}")
            y -= row_height
            c.rect(17, y, block_width, row_height)
            c.drawRightString(block_width + 12, y + 5, f"Total (including tax): ${total_price_with_tax:.2f}")

            c.save()
            buffer.seek(0)
            output_pdf = PdfWriter()

            input_pdf = PdfReader('input.pdf')
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
            
            if incol2.button("Close PDF"):
                incol2.text("PDF Closed")
            if(incol1.button("Open PDF")):
                with col1:
                    pdf_display = F'<iframe src="data:application/pdf;base64,{pdf_base64}" width="800" height="950" type="application/pdf"></iframe>'
                    st.download_button("Download PDF", merged_buffer, file_name=f'{st.session_state.ticketN}-quote.pdf', mime='application/pdf')
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    
        if len(st.session_state.ticketDf)!=0 and st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "MAJ0001":
            if st.sidebar.button("Submit to FMDash"):
                checkout(st.session_state.ticketDf['Purchase_Order'].values[0])
                submitFmQuotes(pdf_base64, st.session_state.ticketDf['Purchase_Order'].values[0], str(st.session_state.workDesDf["Incurred"].get(0)), str(st.session_state.workDesDf["Proposed"].get(0)), st.session_state.labor_df, st.session_state.trip_charge_df, st.session_state.parts_df, st.session_state.miscellaneous_charges_df, st.session_state.materials_non_stock_and_rentals_df, st.session_state.subcontractor_df, total_price, total_price_with_tax)
                st.experimental_rerun()

        if(len(st.session_state.ticketDf)!=0 and st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "CIR0001"):
            if st.sidebar.button("Submit to CircleK"):
                wo_cost_information(category_totals.get("Labor", 0),
                category_totals.get("Trip Charge", 0),
                category_totals.get("Parts", 0),
                category_totals.get("Miscellaneous Charges", 0),
                category_totals.get("Materials, Non Stock and Rentals", 0),
                category_totals.get("Subcontractor", 0),
                taxRate, st.session_state.ticketDf['Purchase_Order'])
                st.experimental_rerun()
        
        if(len(st.session_state.ticketDf)!=0 and st.session_state.ticketDf['LOC_CUSTNMBR'].get(0) == "MUR0001"):
            if st.sidebar.button("Submit to Verisae"):
                submitQuoteVerisae(st.session_state.ticketDf['CUST_NAME'].get(0), st.session_state.ticketN, str(st.session_state.workDesDf["Incurred"].get(0)) + str(st.session_state.workDesDf["Proposed"].get(0)), 
                                   category_totals.get("Trip Charge", 0),
                                   category_totals.get("Parts", 0),
                                   category_totals.get("Labor", 0),
                                   category_totals.get("Miscellaneous Charges", 0),
                                   taxRate, st.session_state.ticketDf['Purchase_Order'])
                st.experimental_rerun()

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
    st.set_page_config("Universal Quote Template", layout="wide")
    float_init()
    button_container = st.container()

    with button_container:
        if st.session_state.show:
            if st.button("⭳", type="primary"):
                st.session_state.show = False
                st.experimental_rerun()
        else:
            if st.button("⭱", type="secondary"):
                st.session_state.show = True
                st.experimental_rerun()

    if st.session_state.show:
        vid_y_pos = "0px"
        button_css = float_css_helper(width="2.2rem", right="4rem", bottom="400px", transition=0)
    else:
        vid_y_pos = "-412px"
        button_css = float_css_helper(width="2.2rem", right="4rem", bottom="1rem", transition=0)

    button_container.float(button_css)
    float_box(
        '<iframe width="560" height="400" src="http://localhost:8501" title="Streamlit App"></iframe>',
        width="29rem",
        height="400px",
        right="4rem",
        bottom=vid_y_pos,
        css="padding: 0; transition-property: all; transition-duration: .5s; transition-timing-function: cubic-bezier(0, 1, 0.5, 1);",
        shadow=12
    )
    st.markdown(
        """
       <style>
       [data-testid="stSidebar"][aria-expanded="true"]{
           min-width: 300px;
           max-width: 300px;
       },
       <style>
                .stButton button {
                    float: left;
                }
                .stButton button:first-child {
                    background-color: #0099FF;
                    color: #FFFFFF;
                    width: 120px;
                    height: 50px;
                }
                .stButton button:hover {
                    background-color: #FFFF00;
                    color: #000000;
                    width: 120px;
                    height: 50px;
                }
                </style>
       """,
        unsafe_allow_html=True,
    )
    # selection = st.sidebar.radio("Select Page", ["Ticket Detail", "NTE/QuoteQue"], horizontal=True)
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
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        help="Status",
                        options=["open", "close", "pending"],
                        required=True,
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
            params = st.experimental_get_query_params()
            if params and params['TicketID']:
                st.session_state.ticketN = params['TicketID'][0]
            if(st.session_state.ticketN):
                st.experimental_rerun()
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

if __name__ == "__main__":
    main()
