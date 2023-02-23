import csv
import os
import requests

# Replace this with the path to your CSV file
csv_path = 'discord.csv'

# Get the directory name of the CSV file
csv_dir = os.path.dirname(csv_path)

# Create the output folder if it doesn't exist
output_folder = os.path.join(csv_dir, 'downloads')
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Open the CSV file and read the first column
with open(csv_path, 'r') as csvfile:
    csv_reader = csv.reader(csvfile)
    for row in csv_reader:
        url = row[0]
        # Get the filename from the URL
        filename = url.split('/')[-1]
        # Check if the file already exists in the output folder
        if os.path.exists(os.path.join(output_folder, filename)):
            print(f"Skipping {filename} (already downloaded)")
            continue
        # Download the file and save it in the output folder
        with open(os.path.join(output_folder, filename), 'wb') as f:
            response = requests.get(url)
            f.write(response.content)
            print(f"Downloaded {filename}")
