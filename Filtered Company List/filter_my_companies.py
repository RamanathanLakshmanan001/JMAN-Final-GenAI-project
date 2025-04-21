import pandas as pd

def extract_row_range(input_file, output_file, start_row, end_row):
    try:
        dataframe = pd.read_excel(input_file)
        
        max_index = len(dataframe) - 1
        
        start_row = max(0, min(start_row, max_index))
        end_row = max(start_row, min(end_row, max_index))
        
        extracted_dataframe = dataframe.iloc[start_row:end_row]
        
        extracted_dataframe.to_excel(output_file, index=False)
        
        print(f"Successfully extracted rows {start_row} to {end_row} to {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")



if __name__ == "__main__":

    input_file = "C:\\JMAN Final Project\\company_list.xlsx"
    output_file = "C:\\JMAN Final Project\\Filtered Company List\\filtered_company_list.xlsx"
    
    start_row = 551
    end_row = 735
    
    extract_row_range(input_file, output_file, start_row, end_row)