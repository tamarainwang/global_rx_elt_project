import os
from sqlalchemy import create_engine
import pandas as pd # data analysis and manipulation library
from dotenv import load_dotenv
import psycopg2 # database adapter library that enables Python applications interact with PostgreSQL databases
import openpyxl # Python library used for reading from and writing to Excel 2010+ files
from datetime import datetime

# Load environment

load_dotenv(override=True) #this means that if we change the values of our .env file. it picks the new value and we dont have to reload it.

pg_url = os.getenv('POSTGRES_URL')

file_path = 'global-superstore-data.xlsx'

df = pd.read_excel(file_path)

def load_excel_data(data_source:str,
                    sheet_name:str):
    """Function to load excel data"""
    print(f'Loading data from {data_source}......')
    raw_data = pd.read_excel(data_source, sheet_name=sheet_name)
    return raw_data

def transform_column_names(df:pd.DataFrame)-> pd.DataFrame: # the --> pd.Daframe isnt compulsory its just to tell us that a dataframe is going to be returned
    """transforms column names of a dataframe to lowercase and repaces spaces with underscores"""
    df.columns = [column.strip().lower().replace(' ','_').replace('-','_') for column in df.columns]
    return df




# Normalization ----> Breaking it all apart., Breaking the table into the 4 subsets below and then removing duplicates based on the primary key

# Products
# customers
# location
# orders

# we also moved all these into a function
def normalize_data(df):
    """Function to normalize data into 4 dataframes ie 4 tables"""
    print(f"Normalization in progress.....current length = {len(df)}")

    products_df = df[['product_id', 'category', 'sub_category', 'product_name']]
    products_df_clean = products_df.drop_duplicates()
    print(f"Done transforming Products ---> current length = {len(products_df_clean)}")

    customers_df = df[['customer_id', 'customer_name']]
    customers_df_clean = customers_df.drop_duplicates()
    print(f"Done transforming customers ---> current length = {len(customers_df_clean)}")

    locations_df = df[['city', 'state', 'country','market']]
    locations_df_clean = locations_df.drop_duplicates()
    print(f"Done transforming locations ---> current length = {len(locations_df_clean)}")
   
    # validate order duplications

    orders_df = df.drop(columns = ['category', 'sub_category', 'product_name','customer_name','state', 'city'])

    return[products_df_clean,customers_df_clean,locations_df_clean,orders_df]

def write_to_csv(list_of_dfs:list):
    """Function to write a list of dataframes to a csv file."""

    #write dfs to csv files

    output_dir = "outputs/models/"
    list_of_dfs[0].to_csv(f"{output_dir}products.csv", index=False)
    list_of_dfs[1].to_csv(f"{output_dir}customers.csv", index=False)
    list_of_dfs[2].to_csv(f"{output_dir}locations.csv", index=False)
    list_of_dfs[3].to_csv(f"{output_dir}orders.csv", index=False)

    print(f"{len(list_of_dfs)} Files written to intermediate storage.")

    print("Files written to intermediate storage")

def update_dataframe(original_data)-> pd.DataFrame:
    """Takes in a dataframe and returns another dataframe with timestamp column"""
    current_time = datetime.now().strftime('%Y-%d-%m %H:%M:%S')
    original_data['_elt_loaded_at'] = current_time
    return original_data

def load_data_to_db(table:str):
    
    # reads the csv to a dataframe
    data = pd.read_csv(f"outputs/models/{table}.csv")
    # adds a timestamp column
    timestamped_dataframe = update_dataframe(original_data = data)
    # connects to the database
    engine = create_engine(pg_url)
    connection = engine.connect()
    # writes table with timestamp column to database
    timestamped_dataframe.to_sql(table, con=connection, if_exists='replace', index=False)
    connection.close()
    print(f"Data loaded to {table} table.")


# Run our function

if __name__ =="__main__":

    #load data
    raw_data = load_excel_data(data_source=file_path,sheet_name="Orders")

    #transform data
    raw_data_transformed = transform_column_names(raw_data)

    #normalize data
    normalized_datasets_list = normalize_data(df=raw_data_transformed)

    #write_to_intermediate_storage_in_csv_format
    write_to_csv(normalized_datasets_list)

    #iterates over normalized tables in intermediate storage and loads to database
    files_to_load = ["products","customers","locations","orders"]
    for file in files_to_load:
        load_data_to_db(table=file)
    
