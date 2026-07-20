import pandas as pd
import sys

def main():
    # Default values for input/output paths
    input_file = 'data/flights.csv'
    output_file = 'data/airports.csv'

    # Allow path override via command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        # Read the cleaned flights CSV
        flights_df = pd.read_csv(input_file)

        # Extract Origin and Destination airport information with standardized names
        origin_airports = flights_df[['OriginAirportID', 'OriginAirportName']].rename(columns={
            'OriginAirportID': 'AirportID',
            'OriginAirportName': 'AirportName'
        }).drop_duplicates().reset_index(drop=True)
        dest_airports = flights_df[['DestAirportID', 'DestAirportName']].rename(columns={
            'DestAirportID': 'AirportID',
            'DestAirportName': 'AirportName'
        }).drop_duplicates().reset_index(drop=True)

        # Combine all airports (union of origin and destination)
        all_airports = pd.concat([origin_airports, dest_airports]).drop_duplicates().reset_index(drop=True)

        # Sort by AirportID for consistent output
        all_airports = all_airports.sort_values(by='AirportID')

        # Save to CSV
        all_airports.to_csv(output_file, index=False)

        print(f"Successfully extracted {len(all_airports)} unique airports.")
        print(f"Output saved to {output_file}")

    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
    except pd.errors.EmptyDataError:
        print("Error: The file is empty.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return 0

if __name__ == '__main__':
    exit(main())