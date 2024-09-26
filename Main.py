import os
import time
import pandas as pd
import streamlit as st
from googletrans import Translator

# Custom CSS for background and text color
st.markdown("""
    <style>
    .stApp {
        background-color: #ADD8E6;  /* Light blue background */
    }
    .title {
        color: #003366;  /* Dark blue color for the title */
        font-family: 'Arial Black', sans-serif;
        text-align: center;
        margin-bottom: 20px;
    }
    .selectbox, .text_input, .button {
        margin-bottom: 20px;
    }
    .warning {
        color: #FF4500; /* Orange color for warnings */
    }
    </style>
    """, unsafe_allow_html=True)

# Retry-safe Marathi to English translation function
def safe_translate(translator, text, retries=3):
    for i in range(retries):
        try:
            return translator.translate(text, src='mr', dest='en').text
        except Exception as e:  # Catch any exception, including network errors
            print(f"Error occurred: {e}. Retrying ({i+1}/{retries})...")
            time.sleep(2)
    return text  # Fallback to the original text if retries fail

# Function to translate Marathi to English
def translate_marathi_to_english(df):
    translator = Translator()
    for col in df.columns:
        df[col] = df[col].astype(str).apply(lambda x: safe_translate(translator, x))
    return df

# Step 1: Upload Marathi Excel files, translate, and ask for property description
def upload_translate_and_search():
    st.markdown("<h1 class='title'>STR Document Search Interface</h1>", unsafe_allow_html=True)

    # Step to upload Marathi files
    uploaded_files = st.file_uploader("Upload Marathi Excel files", accept_multiple_files=True, type=['xls', 'xlsx'])

    # Store translated DataFrames in session state
    if 'translated_dfs' not in st.session_state:
        st.session_state.translated_dfs = []

    # Dictionary to hold file names for downloading
    file_download_links = {}

    if uploaded_files and st.button('Translate'):
        st.session_state.translated_dfs = []  # Clear previous translations
        for uploaded_file in uploaded_files:
            df = pd.read_excel(uploaded_file)
            translated_df = translate_marathi_to_english(df)
            st.session_state.translated_dfs.append(translated_df)

            # Provide an option to download each translated file
            output = f"translated_{uploaded_file.name}"
            translated_df.to_excel(output, index=False)
            file_download_links[uploaded_file.name] = output  # Store for download links
            st.success(f"File {uploaded_file.name} has been translated.")

    # Display download buttons for each translated file
    for original_filename, translated_filename in file_download_links.items():
        with open(translated_filename, 'rb') as file:
            st.download_button("Download Translated: " + original_filename, file, file_name=translated_filename)

    # Display property description input
    property_description = st.text_input("Enter Property Description to Search:")

    # Search button below the property description block
    if property_description and st.button('Search Property Description'):
        results = []
        for translated_df in st.session_state.translated_dfs:
            translated_df.columns = translated_df.columns.str.lower()
            search_result = translated_df[translated_df['propertydescription'].astype(str).str.contains(property_description, case=False, na=False, regex=False)]
            if not search_result.empty:
                results.append(search_result)

        if results:
            final_result = pd.concat(results).reset_index(drop=True)
            st.write(f"Results for Property Description containing '{property_description}':")
            st.dataframe(final_result)
        else:
            st.write(f"No results found for Property Description containing '{property_description}'.")

    # Added Search Document Details button that operates on the translated Excel file
    if st.button('Search Document Details in Translated Files'):
        results = []
        for translated_df in st.session_state.translated_dfs:
            translated_df.columns = translated_df.columns.str.lower()
            # Proceed with searching through the translated dataframe
            search_result = translated_df[translated_df['propertydescription'].astype(str).str.contains(property_description, case=False, na=False, regex=False)]
            if not search_result.empty:
                results.append(search_result)

        if results:
            final_result = pd.concat(results).reset_index(drop=True)
            st.write(f"Search Results for '{property_description}':")
            st.dataframe(final_result)
        else:
            st.write(f"No results found for '{property_description}' in translated documents.")

# Step 2: Search through uploaded English Excel files
def search_document_details():
    st.markdown("<h1 class='title'>Document Details Search Interface</h1>", unsafe_allow_html=True)

    uploaded_files = st.file_uploader("Upload Converted English Excel files", accept_multiple_files=True, type=['xls', 'xlsx'])

    selected_column = st.selectbox(
        'Select Column to Search:',
        ['DocNo', 'RegistrationDate', 'SellerParty',
         'PurchaserParty', 'PropertyDescription', 'DateOfExecution'],
        index=4  # Default to 'PropertyDescription'
    )

    search_value = st.text_input('Enter Search Value:', '')

    if st.button('Submit') and uploaded_files:
        expected_columns_set_1 = [
            'srocode', 'internaldocumentnumber', 'docno', 'docname', 'registrationdate',
            'sroname', 'micrno', 'bank_type', 'party_code', 'sellerparty',
            'purchaserparty', 'propertydescription', 'areaname', 'consideration_amt',
            'marketvalue', 'dateofexecution', 'stampdutypaid', 'registrationfees', 'status'
        ]

        expected_columns_set_2 = [
            'SROCode', 'InternalDocumentNumber', 'DocNo', 'DocName', 'RegistrationDate',
            'SROName', 'SellerParty', 'PurchaserParty', 'PropertyDescription', 'AreaName',
            'consideration_amt', 'MarketValue', 'DateOfExecution', 'StampDutyPaid',
            'RegistrationFees', 'status', 'micrno', 'party_code', 'bank_type'
        ]

        dataframes = []

        for uploaded_file in uploaded_files:
            try:
                df = pd.read_excel(uploaded_file)

                if all(col in df.columns for col in expected_columns_set_1):
                    dataframes.append(df[expected_columns_set_1])
                elif all(col in df.columns for col in expected_columns_set_2):
                    dataframes.append(df[expected_columns_set_2])
                else:
                    st.warning(f"File {uploaded_file.name} does not match the expected column sets and will be skipped.", icon="⚠️")
            except PermissionError:
                st.warning(f"Permission denied for file {uploaded_file.name}. Ensure it is not open in another application.", icon="⚠️")
            except Exception as e:
                st.warning(f"An error occurred with file {uploaded_file.name}: {e}", icon="⚠️")

        results = []

        for df in dataframes:
            df.columns = df.columns.str.lower()
            selected_column_lower = selected_column.lower()

            if selected_column_lower in df.columns:
                result = df[df[selected_column_lower].astype(str).str.contains(search_value, case=False, na=False, regex=False)]
                if not result.empty:
                    results.append(result)
            else:
                st.warning(f"Selected column '{selected_column}' not found in one or more files.", icon="⚠️")

        if results:
            final_result = pd.concat(results).reset_index(drop=True)
            st.write(f"Results for {selected_column} containing '{search_value}':")
            st.dataframe(final_result)
        else:
            st.write(f"No results found for {selected_column} containing '{search_value}'.")

# Main Application Interface
def main():
    st.sidebar.title("Navigation")
    option = st.sidebar.radio("Choose an option", ["Translate Marathi Excel Files", "Search Document Details"])

    if option == "Translate Marathi Excel Files":
        upload_translate_and_search()  # Updated function call
    else:
        search_document_details()

if __name__ == "__main__":
    main()


