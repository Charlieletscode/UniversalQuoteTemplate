import streamlit as st
import pandas as pd
import requests
from PIL import Image
import io
from io import BytesIO
from reportlab.lib.pagesizes import letter
from servertest import getPricing
from servertest import getTicketInfo
from servertest import getLRates
from servertest import getTRates
from servertest import getMisc
from datetime import datetime
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from servertest import getTicketInfo
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Paragraph
import numpy as np
import re
from reportlab.pdfgen import canvas

current_date = datetime.now()
formatted_date = current_date.strftime("%m/%d/%Y")
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
    st.session_state.workDescription = None

if "labor_df" not in st.session_state:
    st.session_state.labor_df = pd.DataFrame()
    st.session_state.trip_charge_df = pd.DataFrame()
    st.session_state.parts_df = pd.DataFrame()
    st.session_state.miscellaneous_charges_df = pd.DataFrame()
    st.session_state.materials_and_rentals_df = pd.DataFrame()
    st.session_state.subcontractor_df = pd.DataFrame()

def mainPage():
    header_image_url = "https://github.com/Charlieletscode/UniversalQuoteTemplate/blob/main/Header.jpg?raw=true"
    response = requests.get(header_image_url)
    image = Image.open(io.BytesIO(response.content))
    image_height = 200
    resized_image = image.resize((int(image_height * image.width / image.height), image_height))

    st.subheader("Main Page")
    st.write("Welcome to the main page of the Fee Charge Types application.")
    st.markdown(
        """
       <style>
       [data-testid="stSidebar"][aria-expanded="true"]{
           min-width: 300px;
           max-width: 300px;
       }
       """,
        unsafe_allow_html=True,
    )   
    st.session_state.ticketN = st.sidebar.text_input("Enter ticket number:")

    # try:
    if 'ticketN' in st.session_state and st.session_state.ticketN:
        st.markdown(
                """
                <style>
                .stButton button {
                    float: right;
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
                unsafe_allow_html=True
            )
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Edit", key="1"):
                st.session_state.edit = True
        with col2:
            if st.button("View", key="2"):
                st.session_state.edit = False
        
        col1, col2 = st.columns((2,1))
        st.session_state.ticketDf = getTicketInfo(st.session_state.ticketN)
        st.session_state.pricingDf = getPricing(st.session_state.ticketN)
        st.session_state.LRatesDf = getLRates(st.session_state.ticketN)
        st.session_state.TRatesDf = getTRates(st.session_state.ticketN)
        st.session_state.misc_ops_df = getMisc(st.session_state.ticketN)

        left_data = {
            'To': st.session_state.ticketDf['CUST_NAME'] + " " + st.session_state.ticketDf['CUST_ADDRESS1'] + " " +
                st.session_state.ticketDf['CUST_ADDRESS2'] + " " + st.session_state.ticketDf['CUST_ADDRESS3'] + " " +
                st.session_state.ticketDf['CUST_CITY'] + " " + st.session_state.ticketDf['CUST_Zip'],
            'ATTN': ['ATTN']
        }

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
            'BranchEmail': st.session_state.ticketDf['MailDispatch']
        }

        df_info1 = pd.DataFrame(data)
        df_info2 = pd.DataFrame(data1)

        st.subheader("Ticket Info")
        st.dataframe(df_info1, hide_index=True)
        st.dataframe(df_info2, hide_index=True)
        
        if st.session_state.edit:
            if st.session_state.get("labor_df", None) is None or st.session_state.labor_df.empty:
                labor_data = {
                    'Description': [None],
                    'Nums of Techs': [None],
                    'Hours per Tech': [None],
                    'QTY': [None],
                    'Hourly Rate': [None],
                    'EXTENDED': [None]
                }
                st.session_state.labor_df = pd.DataFrame(labor_data)

            if st.session_state.get("trip_charge_df", None) is None or st.session_state.trip_charge_df.empty:
                trip_charge_data = {
                    'Description': [None],
                    'QTY': [None],
                    'UNIT Price': [None],
                    'EXTENDED': [None]
                }
                st.session_state.trip_charge_df = pd.DataFrame(trip_charge_data)

            if st.session_state.get("parts_df", None) is None or st.session_state.parts_df.empty:
                parts_data = {
                    'Description': [None],
                    'QTY': [None],
                    'UNIT Price': [None],
                    'EXTENDED': [None]
                }
                st.session_state.parts_df = pd.DataFrame(parts_data)

            if st.session_state.get("miscellaneous_charges_df", None) is None or st.session_state.miscellaneous_charges_df.empty:
                misc_charges_data = {
                    'Description': [None],
                    'QTY': [None],
                    'UNIT Price': [None],
                    'EXTENDED': [None]
                }
                st.session_state.miscellaneous_charges_df = pd.DataFrame(misc_charges_data)

            if st.session_state.get("materials_and_rentals_df", None) is None or st.session_state.materials_and_rentals_df.empty:
                materials_rentals_data = {
                    'Description': [None],
                    'QTY': [None],
                    'UNIT Price': [None],
                    'EXTENDED': [None]
                }
                st.session_state.materials_and_rentals_df = pd.DataFrame(materials_rentals_data)

            if st.session_state.get("subcontractor_df", None) is None or st.session_state.subcontractor_df.empty:
                subcontractor_data = {
                    'Description': [None],
                    'QTY': [None],
                    'UNIT Price': [None],
                    'EXTENDED': [None]
                }
                st.session_state.subcontractor_df = pd.DataFrame(subcontractor_data)
            st.write("**UNLESS SPECIFICALLY NOTED, THIS PROPOSAL IS VALID FOR 30 DAYS FROM THE DATE ABOVE**")
            
            with st.container():
                work_description = st.text_area('***General description of work to be performed:***', value=st.session_state.workDescription, height=200, key='work_description')
                if st.button("Save Work Description"):
                    st.session_state.workDescription = work_description
            col1, col2 = st.columns([1, 3])

            categories = ['Labor', 'Trip Charge', 'Parts', 'Miscellaneous Charges', 'Materials and Rentals', 'Subcontractor']
            category_totals = {category: 0 for category in categories}

            for category in categories:
                with st.expander(f"******{category}******", expanded=True):
                    st.title(category)
                    if category == 'Parts':
                        input_letters = st.text_input("Please enter Part#/short Description of Part:", max_chars=15).upper()
                    width = 800
                    inwidth = 650
                    with st.form(key=f'{category}_form'):
                        if category == 'Labor':
                            string_values = [" : "+str(value).rstrip('0').rstrip('.') for value in st.session_state.LRatesDf['Billing_Amount']]
                            concatenated_values = [description + value for description, value in zip(st.session_state.LRatesDf['Pay_Code_Description'], string_values)]
                            st.session_state.labor_df = st.data_editor(
                                st.session_state.labor_df,
                                column_config={
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
                                        min_value=0.0,
                                        step=0.5
                                    ),
                                    "QTY": st.column_config.NumberColumn(
                                        "QTY",
                                        help="Quantity",
                                        width=inwidth/6,
                                        disabled=True,
                                    ),
                                    "Hourly Rate": st.column_config.NumberColumn(
                                        "Hourly Rate",
                                        help="Hourly Rate",
                                        width=inwidth/6,
                                        disabled=True,
                                    ),
                                    "EXTENDED": st.column_config.NumberColumn(
                                        "EXTENDED",
                                        help="Extended Amount",
                                        width=inwidth/6,
                                        disabled=True,
                                        min_value=0.0
                                    )
                                },
                                hide_index=True,
                                width=width,
                                num_rows="dynamic",
                                key=category
                            )
                            col1, col2 = st.columns([3,1])
                            submit_button = col2.form_submit_button(label='Submit')
                            if not st.session_state.labor_df.empty:
                                if submit_button:
                                    qty_values = st.session_state.labor_df["Nums of Techs"]
                                    hours_values = st.session_state.labor_df["Hours per Tech"]
                                    qty_mask = qty_values.notnull() & hours_values.notnull()
                                    st.session_state.labor_df.loc[qty_mask, 'QTY'] = np.array(qty_values[qty_mask]) * np.array(hours_values[qty_mask])
                                    description_values = st.session_state.labor_df['Description']
                                    rate_mask = description_values.notnull()
                                    st.session_state.labor_df.loc[rate_mask, 'Hourly Rate'] = description_values[rate_mask].apply(lambda x: float(re.search(r'\d+', x).group()))
                                    extended_mask = qty_mask & rate_mask
                                    st.session_state.labor_df.loc[extended_mask, 'EXTENDED'] = np.array(st.session_state.labor_df.loc[extended_mask, 'QTY']) * np.array(st.session_state.labor_df.loc[extended_mask, 'Hourly Rate'])
                                    st.experimental_rerun()
                                category_total = st.session_state.labor_df['EXTENDED'].sum()
                                category_totals[category] = category_total
                        elif category == 'Trip Charge':
                            string_values = [" : "+str(value).rstrip('0').rstrip('.') for value in st.session_state.TRatesDf['Billing_Amount']]
                            concatenated_values = [description + value for description, value in zip(st.session_state.TRatesDf['Pay_Code_Description'], string_values)]
                            st.session_state.trip_charge_df = st.data_editor(
                                st.session_state.trip_charge_df,
                                column_config={
                                    "QTY": st.column_config.NumberColumn(
                                        "QTY",
                                        help="Quantity",
                                        width=inwidth/4,
                                        min_value=0,
                                        step=1
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
                                        min_value=0.0,
                                        disabled=False
                                    ),
                                    "EXTENDED": st.column_config.NumberColumn(
                                        "EXTENDED",
                                        help="Extended Amount",
                                        width=inwidth/4,
                                        min_value=0.0,
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
                            if not st.session_state.trip_charge_df.empty:
                                if submit_button:
                                    if pd.isnull(st.session_state.trip_charge_df['UNIT Price']).any() and not pd.isnull(st.session_state.trip_charge_df['Description']).any():
                                        st.session_state.trip_charge_df['UNIT Price'] = st.session_state.trip_charge_df['Description'].apply(lambda x: float(re.search(r'\d+', x).group()))
                                    qty_values = st.session_state.trip_charge_df['QTY']
                                    unit_price_values = st.session_state.trip_charge_df['UNIT Price']
                                    extended_mask = qty_values.notnull() & unit_price_values.notnull()
                                    st.session_state.trip_charge_df.loc[extended_mask, 'EXTENDED'] = np.array(qty_values[extended_mask]) * np.array(unit_price_values[extended_mask])
                                    st.experimental_rerun()
                                category_total = st.session_state.trip_charge_df['EXTENDED'].sum()
                                category_totals[category] = category_total
                            col1.write("<small>Please enter Unit Price if 0</small>", unsafe_allow_html=True)
                        elif category == 'Parts':
                            filtered_descriptions = st.session_state.pricingDf[
                                (st.session_state.pricingDf['ITEMNMBR'] + " " + st.session_state.pricingDf['ITEMDESC']).str.contains(input_letters)]
                            filtered_descriptions['bindDes'] = filtered_descriptions['ITEMNMBR'] + " " + filtered_descriptions['ITEMDESC']
                            st.session_state.parts_df = st.data_editor(
                                st.session_state.parts_df,
                                column_config={
                                    "QTY": st.column_config.NumberColumn(
                                        "QTY",
                                        help="Quantity",
                                        width=inwidth/4,
                                        min_value=0,
                                        step=1
                                    ),
                                    "Description": st.column_config.SelectboxColumn(
                                        "Description",
                                        help="Description",
                                        width=inwidth/4,
                                        options=filtered_descriptions['bindDes'],
                                    ),
                                    "UNIT Price": st.column_config.NumberColumn(
                                        "UNIT Price",
                                        help="Unit Price",
                                        width=inwidth/4,
                                        min_value=0.0,
                                        disabled=True
                                    ),
                                    "EXTENDED": st.column_config.NumberColumn(
                                        "EXTENDED",
                                        help="Extended Amount",
                                        width=inwidth/4,
                                        min_value=0.0,
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
                            if not st.session_state.parts_df.empty:
                                if submit_button:
                                    qty_values = st.session_state.parts_df['QTY']
                                    descriptions = st.session_state.parts_df['Description']
                                    merged_table = st.session_state.parts_df.merge(filtered_descriptions, left_on='Description', right_on='bindDes', how='left')
                                    selling_prices = merged_table['SellingPrice'].astype(float)

                                    extended_mask = qty_values.notnull() & descriptions.notnull()
                                    st.session_state.parts_df.loc[extended_mask, 'UNIT Price'] = selling_prices[extended_mask]
                                    st.session_state.parts_df.loc[extended_mask, 'EXTENDED'] = np.array(qty_values[extended_mask]) * np.array(selling_prices[extended_mask])
                                    st.experimental_rerun()
                                category_total = st.session_state.parts_df['EXTENDED'].sum()
                                category_totals[category] = category_total
                        elif category == 'Miscellaneous Charges':
                            string_values = [" : "+str(value).rstrip('0').rstrip('.') for value in st.session_state.misc_ops_df['Fee_Amount']]
                            concatenated_values = [description + value for description, value in zip(st.session_state.misc_ops_df['Fee_Charge_Type'], string_values)]
                            st.session_state.miscellaneous_charges_df = st.data_editor(
                                st.session_state.miscellaneous_charges_df,
                                column_config={
                                    "QTY": st.column_config.NumberColumn(
                                        "QTY",
                                        help="Quantity",
                                        width=inwidth/4,
                                        min_value=0,
                                        step=1
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
                                        min_value=0.0,
                                        disabled=True
                                    ),
                                    "EXTENDED": st.column_config.NumberColumn(
                                        "EXTENDED",
                                        help="Extended Amount",
                                        width=inwidth/4,
                                        min_value=0.0,
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
                                    st.session_state.miscellaneous_charges_df['UNIT Price'] = st.session_state.miscellaneous_charges_df['Description'].apply(lambda x: float(re.search(r'\d+', x).group()))
                                    qty_values = st.session_state.miscellaneous_charges_df['QTY']
                                    unit_price_values = st.session_state.miscellaneous_charges_df['UNIT Price']
                                    extended_mask = qty_values.notnull() & unit_price_values.notnull()                                        
                                    st.session_state.miscellaneous_charges_df.loc[extended_mask, 'EXTENDED'] = np.array(qty_values[extended_mask]) * np.array(unit_price_values[extended_mask])
                                    st.experimental_rerun()
                                category_total = st.session_state.miscellaneous_charges_df['EXTENDED'].sum()
                                category_totals[category] = category_total
                        elif category == 'Materials and Rentals':
                            st.session_state.materials_and_rentals_df = st.data_editor(
                                st.session_state.materials_and_rentals_df,
                                column_config={
                                    "QTY": st.column_config.NumberColumn(
                                        "QTY",
                                        help="Quantity",
                                        width=inwidth/4,
                                        min_value=0,
                                        step=1
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
                                        min_value=0.0
                                    ),
                                    "EXTENDED": st.column_config.NumberColumn(
                                        "EXTENDED",
                                        help="Extended Amount",
                                        width=inwidth/4,
                                        min_value=0.0,
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
                            if not st.session_state.materials_and_rentals_df.empty:
                                if submit_button:
                                    qty_values = st.session_state.materials_and_rentals_df['QTY']
                                    unit_price_values = st.session_state.materials_and_rentals_df['UNIT Price']
                                    extended_mask = qty_values.notnull() & unit_price_values.notnull()
                                    st.session_state.materials_and_rentals_df.loc[extended_mask, 'EXTENDED'] = np.array(qty_values[extended_mask]) * np.array(unit_price_values[extended_mask])
                                    st.experimental_rerun()
                                category_total = st.session_state.materials_and_rentals_df['EXTENDED'].sum()
                                category_totals[category] = category_total
                        elif category == 'Subcontractor':
                            st.session_state.subcontractor_df = st.data_editor(
                                st.session_state.subcontractor_df,
                                column_config={
                                    "QTY": st.column_config.NumberColumn(
                                        "QTY",
                                        help="Quantity",
                                        width=inwidth/4,
                                        min_value=0,
                                        step=1
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
                                        min_value=0.0
                                    ),
                                    "EXTENDED": st.column_config.NumberColumn(
                                        "EXTENDED",
                                        help="Extended Amount",
                                        width=inwidth/4,
                                        min_value=0.0,
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
                        col1.write(f"****{category} Total : {category_totals[category]}****")
                    
            # if st.button(label='toCsv'):
            #     data = {
            #         'workdescription': [workDescription],
            #         # 'incurredInfo': [add_incurred], 
            #         'TicketID':[st.session_state.ticketN]
            #         }
            #     df = pd.DataFrame(data)
            #     df.to_csv(f'{st.session_state.ticketN}workdescription.csv', index=False)
            #     st.session_state.labor_df['TicketID'] = st.session_state.ticketN
            #     st.session_state.trip_charge_df['TicketID'] = st.session_state.ticketN
            #     st.session_state.parts_df['TicketID'] = st.session_state.ticketN
            #     st.session_state.miscellaneous_charges_df['TicketID'] = st.session_state.ticketN
            #     st.session_state.materials_and_rentals_df['TicketID'] = st.session_state.ticketN
            #     st.session_state.subcontractor_df['TicketID'] = st.session_state.ticketN
            #     st.session_state.labor_df.to_csv(f'{st.session_state.ticketN}labor.csv', index=False)
            #     st.session_state.trip_charge_df.to_csv(f'{st.session_state.ticketN}trip_charge.csv', index=False)
            #     st.session_state.parts_df.to_csv(f'{st.session_state.ticketN}parts.csv', index=False)
            #     st.session_state.miscellaneous_charges_df.to_csv(f'{st.session_state.ticketN}misc_charges.csv', index=False)
            #     st.session_state.materials_and_rentals_df.to_csv(f'{st.session_state.ticketN}materials_rentals.csv', index=False)
            #     st.session_state.subcontractor_df.to_csv(f'{st.session_state.ticketN}subcontractor.csv', index=False)
                
            #     data = {
            #         'TicketID':[st.session_state.ticketN],
            #         'workdescription': [workDescription],
            #         'Labor': [st.session_state.labor_df]
            #         }
            #     df = pd.DataFrame(data)
            #     df.to_csv(f'{st.session_state.ticketN}workdescription.csv', index=False)
            
        else:
            st.success("everything is saved")
            with st.container():
                st.text_area('***General description of work to be performed:***', value = st.session_state.workDescription, disabled=True, height=200)
            categories = ['Labor', 'Trip Charge', 'Parts', 'Miscellaneous Charges', 'Materials and Rentals', 'Subcontractor']
            
            expand_button_title = "Expand All"
            collapse_button_title = "Collapse All"
            expand_collapse_state = True
            expand_collapse_button = st.button(collapse_button_title if expand_collapse_state else expand_button_title)

            if expand_collapse_button:
                expand_collapse_state = not expand_collapse_state
                if expand_collapse_state:
                    expand_collapse_button = st.button(collapse_button_title)
                    st.markdown(
                        """
                        <style>
                        .streamlit-expanderContent {
                            display: block;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    expand_collapse_button = st.button(expand_button_title)
                    st.markdown(
                        """
                        <style>
                        .streamlit-expanderContent {
                            display: none;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )

            category_totals = {}
            for category in categories:
                with st.expander(category, expanded=expand_collapse_state):
                    table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_')}_df")
                    st.table(table_df)
                    if not table_df.empty and 'EXTENDED' in table_df.columns:
                        category_total = table_df['EXTENDED'].sum()
                        category_totals[category] = category_total
                        st.write(f"{category} Total : {category_totals[category]}")
                    else:
                        st.write(f"{category} Total : 0")
        left_column_content = """
        *THE TOTAL PRICE IS AS FOLLOWS:*
        *NOTE: TOTAL PRICE INCLUDES ESTIMATED SALES* \n*/ USE TAX*
        """

        col1, col2 = st.columns([1, 1])
        col1.write(left_column_content)
        total_price = 0
        if st.session_state.edit:
            taxRate = col1.number_input("Please input a tax rate in % (by 2 decimal)",
                                        value=float(st.session_state.ticketDf['Tax_Rate']),
                                        format="%.2f",
                                        key="tax_rate_input")
        else:
            taxRate = col1.number_input("Please input a tax rate in % (by 2 decimal)",
                                    value=float(st.session_state.ticketDf['Tax_Rate']),
                                    disabled=True,
                                    format="%.2f",
                                    key="tax_rate_input")
        category_table_data = []
        for category in categories:
            table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_')}_df")
            if not table_df.empty:
                category_table_data.append([f"{category} Total", category_totals[category]])
                total_price += category_totals[category]
            else:
                category_table_data.append([f"{category} Total", 0])

        total_price_with_tax = total_price * (1 + taxRate / 100)

        right_column_content = f"""
        **Total**
        ${total_price:.2f}

        *Estimated Sales Tax*
        ${taxRate:.1f}%

        *Total (including tax)*
        ${total_price_with_tax:.2f}
        """
        col2.dataframe(pd.DataFrame(category_table_data, columns=["Category", "Total"]), hide_index=True)
        col2.write(right_column_content)
    
        input_pdf = PdfReader(open('input.pdf', 'rb'))
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica", 7)
        c.drawString(25, 675.55, str(st.session_state.ticketDf['CUST_NAME'].values[0]) + " " + str(st.session_state.ticketDf['CUST_ADDRESS1'].values[0]))
        c.drawString(25, 665.55, str(st.session_state.ticketDf['CUST_ADDRESS2'].values[0]) + " " + str(st.session_state.ticketDf['CUST_ADDRESS3'].values[0]) + " " +
                    str(st.session_state.ticketDf['CUST_CITY'].values[0]) + " " + str(st.session_state.ticketDf['CUST_Zip'].values[0]))
        
        c.drawString(50, 582, str(st.session_state.ticketDf['LOC_LOCATNNM'].values[0]))
        c.drawString(50, 572, st.session_state.ticketDf['LOC_Address'].values[0] + " " + st.session_state.ticketDf['CITY'].values[0] + " " + 
            st.session_state.ticketDf['STATE'].values[0]+ " " + st.session_state.ticketDf['ZIP'].values[0])
        c.drawString(70, 542, str(st.session_state.ticketDf['MailDispatch'].values[0]))
        c.drawString(310, 582, str(st.session_state.ticketN))
        c.drawString(310, 562, str(st.session_state.ticketDf['Purchase_Order'].values[0]))
        c.drawString(510, 552, str(formatted_date))
        c.setFont("Helvetica", 10)

        text_box_width = 480
        text_box_height = 100
        general_description = st.session_state.workDescription
        
        styles = getSampleStyleSheet()
        paragraph_style = styles["Normal"]
        if general_description is not None:
            paragraph = Paragraph(general_description, paragraph_style)
        else:
            paragraph = Paragraph("Nothing has been entered", paragraph_style)
        paragraph.wrapOn(c, text_box_width, text_box_height)
        paragraph.drawOn(c, 25, 460.55)
        block_x = 7
        block_y = 386.55
        block_width = 577
        block_height = 100
        border_width = 1.5
        right_block_x = block_x + 10
        right_block_y = block_y
        right_block_width = block_width
        right_block_height = block_height
        c.rect(right_block_x, right_block_y, right_block_width, right_block_height, fill=0)
        c.rect(right_block_x + border_width, right_block_y + border_width, right_block_width - 2 * border_width, right_block_height - 2 * border_width, fill=0)  # Inner border
        c.setFont("Helvetica", 12)
        # after
        y = 386.55 - 50
        margin_bottom = 20
        first_page = True
        new_page_needed = False

        for category in categories:
            if new_page_needed:
                c.showPage()
                first_page = False
                new_page_needed = False
                y = 750

            table_df = getattr(st.session_state, f"{category.lower().replace(' ', '_')}_df")
            row_height = 20
            category_column_width = 577 / 6

            if not table_df.empty:
                table_rows = table_df.to_records(index=False)
                column_names = table_df.columns
                row_height = 20
                category_column_width = 577 / 6

                if category == 'Labor':
                    category_column_width = category_column_width
                else:
                    category_column_width = category_column_width * 6 / 4

                if not first_page and y - (len(table_rows) + 4) * row_height < margin_bottom:
                    c.showPage()
                    first_page = False
                    y = 750

                x = 17
                for col_name in column_names:
                    c.rect(x, y, category_column_width, row_height)
                    c.drawString(x + 5, y + 5, str(col_name))
                    x += category_column_width
                y -= row_height
                for row in table_rows:
                    x = 17
                    for col in row:
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
                                if len(first_string) > 23:
                                    first_string = first_string[:23]
                                c.rect(x, y, category_column_width, row_height)
                                c.drawString(x + 5, y + 5, first_string)
                        else:
                            c.rect(x, y, category_column_width, row_height)
                            c.drawString(x + 5, y + 5, str(col))
                        x += category_column_width
                    y -= row_height
                    if new_page_needed:
                        c.showPage()
                        first_page = False
                        new_page_needed = False
                        y = 750


                category_total = table_df['EXTENDED'].sum()
                if category == 'Labor':
                    c.rect(17, y, category_column_width * 6, row_height)
                    c.drawRightString(category_column_width * 6 + 12, y + 5, f"{category} Total: {category_total}")
                else:
                    c.rect(17, y, category_column_width * 4, row_height)
                    c.drawRightString(category_column_width * 4 + 12, y + 5, f"{category} Total: {category_total}")
                y -= row_height

                if y < margin_bottom:
                    c.showPage()
                    first_page = False
                    y = 750


        total_price_with_tax = total_price * (1 + taxRate / 100)
        c.rect(17, y, category_column_width * 4, row_height)
        c.drawRightString(category_column_width * 4 + 12, y + 5, f"Total Price: ${total_price:.2f}")
        y -= row_height
        c.rect(17, y, category_column_width * 4, row_height)
        c.drawRightString(category_column_width * 4 + 12, y + 5, f"Estimated Sales Tax: {taxRate:.1f}%")
        y -= row_height
        c.rect(17, y, category_column_width * 4, row_height)
        c.drawRightString(category_column_width * 4 + 12, y + 5, f"Total (including tax): ${total_price_with_tax:.2f}")

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
        st.download_button("Download PDF", merged_buffer, file_name=f'{st.session_state.ticketN}-quote.pdf', mime='application/pdf')
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
    fee_charge_types = [
        ("Street Saw", "$125.00"),
        ("Environmental Fee", "$10.00"),
        ("Filter Disposal", "$1.50"),
        ("PCW Disposal", "$2.50"),
        ("PCW Pump Fee", "$25.00"),
        ("PCW Truck Fee", "$75.00"),
        ("Truck Crane Fee", "$75.00"),
        ("Trailer Fee", "$150.00"),
        ("Calibration Prover", "$5.00"),
        ("Forklift", "$300.00"),
        ("Bobcat", "$300.00"),
        ("Breaker", "$225.00"),
        ("PP&E Fee", "$15.00"),
        ("Confined Space", "$15.00"),
        ("Blower", "$125.00"),
        ("Laptop Fee", "$30.00"),
        ("P-1 Fee", "$50.00"),
        ("Project Management Fee", "$70.00"),
        ("Stand By Fee Per Hr.", "$115.00")
    ]

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

def main():
    st.set_page_config(layout="wide")
    mainPage()
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
