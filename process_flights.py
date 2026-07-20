import csv

input_file = 'data/flights.csv'
output_file = 'data/flights_cleaned.csv'

def process_csv(in_path, out_path):
    try:
        with open(in_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader)
            
            cleaned_rows = []
            for row in reader:
                # Replace empty strings (null segments) with '0'
                new_row = [col if col.strip() != '' else '0' for col in row]
                cleaned_rows.append(new_row)
        
        with open(out_path, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(cleaned_rows)
            
        print(f"Successfully processed {len(cleaned_rows)} rows.")
        print(f"Output saved to {out_path}")

    except FileNotFoundError:
        print(f"Error: The file {in_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    process_csv(input_file, output_file)
