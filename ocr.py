import json
import os
import csv
import sys

def load_json_data(file_path):
    """Loads JSON data from the specified file path."""
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

def extract_abilities(data):
  """Extracts the "Abilities" and their values from the JSON data."""

  # Get 'pages' data
  pages = data["pages"]

  # Initialize start and end indices
  start_index = None
  end_index = None

  # Find start and end indices
  for i, line in enumerate(pages[0]["lines"]):
      if line["text"] == "Abilities":
          start_index = i
      # Start searching for end_index only after start_index is found
      elif start_index is not None and line["text"] == "@ Select Prospect":
          end_index = i
          break  # Stop searching once found

  extracted_matches = {}

  # Slice the lines if both indices are found
  if start_index is not None and end_index is not None:
      sliced_lines = pages[0]["lines"][start_index:end_index]

      # Initialize left_boundary and right_boundary with the x-coordinates of the "Abilities" line
      left_boundary = sliced_lines[0]["boundingPolygon"]["normalizedVertices"][0]["x"]
      right_boundary = sliced_lines[0]["boundingPolygon"]["normalizedVertices"][1]["x"]

      # Find the line with "Attributes" to potentially update the left boundary
      for line in sliced_lines:
          if line["text"] == "Attributes":
              left_boundary = min(left_boundary, line["boundingPolygon"]["normalizedVertices"][0]["x"])
              break  # Stop searching once found

      # Get the center y coordinate of the line containing "Abilities"
      abilities_center_y = (sliced_lines[0]["boundingPolygon"]["normalizedVertices"][0]["y"] + 
                            sliced_lines[0]["boundingPolygon"]["normalizedVertices"][2]["y"]) / 2

      # Get the center y coordinate of the line containing "@ Select Prospect"
      select_prospect_center_y = (sliced_lines[-1]["boundingPolygon"]["normalizedVertices"][0]["y"] + 
                                  sliced_lines[-1]["boundingPolygon"]["normalizedVertices"][2]["y"]) / 2

      # Define vertical tolerance
      vertical_tolerance = 0.05  # Increased tolerance

      # Filter lines based on conditions
      filtered_lines = [
          line
          for line in sliced_lines
          if (
              # Check if the line's x-coordinates fall within the range of "Abilities" with some tolerance
              left_boundary - 0.05 <= line["boundingPolygon"]["normalizedVertices"][0]["x"]
              and line["boundingPolygon"]["normalizedVertices"][1]["x"] <= right_boundary + 0.05
              # Check if line is below or equal to "Abilities" and above "@ Select Prospect"
              and (line["boundingPolygon"]["normalizedVertices"][0]["y"] + 
                   line["boundingPolygon"]["normalizedVertices"][2]["y"]) / 2 >= abilities_center_y
              and (line["boundingPolygon"]["normalizedVertices"][0]["y"] + 
                   line["boundingPolygon"]["normalizedVertices"][2]["y"]) / 2 < select_prospect_center_y
              # Exclude "Abilities" and "Mentals"
              and line["text"] not in ["Abilities", "Mentals"]
          )
      ]

      # Extract abilities as a single string
      extracted_matches["Abilities"] = ", ".join([line["text"] for line in filtered_lines])

  return extracted_matches

def extract_attributes(data):
    """Extracts key-value pairs from the JSON data based on specific criteria."""
    # Extract 'pages'
    pages = data["pages"]

    # Initialize start and end indices
    start_index = None
    end_index = None

    # Find start and end indices
    for i, line in enumerate(pages[0]["lines"]):
        if line["text"] == "Attributes":
            start_index = i
        elif line["text"] == "@ Select Prospect":
            end_index = i

    # Slice the lines if both indices are found
    if start_index is not None and end_index is not None:
        sliced_lines = pages[0]["lines"][start_index:end_index]

        # Get the left boundary
        left_boundary = sliced_lines[0]["boundingPolygon"]["normalizedVertices"][0]["x"]

        # Filter lines based on conditions
        filtered_lines = [
            line
            for line in sliced_lines
            if line["boundingPolygon"]["normalizedVertices"][0]["x"] >= left_boundary
            and line["text"] != "Attributes"
        ]

    #key value matching and output for attributes
        # Initialize a dictionary to store the extracted matches
        attribute_data = {}

        # Iterate through the filtered lines
        for i, line in enumerate(filtered_lines):
            # Check if the current line is a potential key and it has not been matched yet
            if (line["text"].isupper() or line["text"].endswith(":")) and line["text"] not in attribute_data:
                # Calculate the center of the current line
                current_center_x = (
                    line["boundingPolygon"]["normalizedVertices"][0]["x"]
                    + line["boundingPolygon"]["normalizedVertices"][1]["x"]
                ) / 2

                # Scan a few lines below for potential values
                for j in range(i + 1, min(i + 4, len(filtered_lines))):
                    next_line = filtered_lines[j]

                    # Calculate the center of the next line
                    next_center_x = (
                        next_line["boundingPolygon"]["normalizedVertices"][0]["x"]
                        + next_line["boundingPolygon"]["normalizedVertices"][1]["x"]
                    ) / 2

                    # Check if the next line is reasonably centered below the current line
                    if abs(current_center_x - next_center_x) < 0.1:  # Relaxed threshold
                        attribute_data[line["text"]] = next_line["text"]
                        break  # Stop searching for values once a match is found
        return attribute_data

def extract_dev_trait(data):
  """Extracts the "Development Trait" and its value from the JSON data."""

  # Get 'pages' data
  pages = data["pages"]

  # Initialize start and end indices
  start_index = None
  end_index = None

  # Find start and end indices
  for i, line in enumerate(pages[0]["lines"]):
      if line["text"] == "Development Trait":
          start_index = i
      elif line["text"] == "@ Select Prospect":
          end_index = i

  dev_trait = {}

  # Slice the lines if both indices are found
  if start_index is not None and end_index is not None:
      sliced_lines = pages[0]["lines"][start_index:end_index]

      # Get the left boundary
      left_boundary = sliced_lines[0]["boundingPolygon"]["normalizedVertices"][0]["x"]

      # Filter lines based on conditions
      filtered_lines = [
          line
          for line in sliced_lines
          if line["boundingPolygon"]["normalizedVertices"][0]["x"] >= left_boundary
          #and line["text"] != "Development Trait"
      ]

      # Iterate through the filtered lines
      for i, line in enumerate(filtered_lines):
          # Check if the current line contains "Development Trait"
          if line["text"] == "Development Trait":
              # Calculate the center of the current line
              current_center_x = (
                  line["boundingPolygon"]["normalizedVertices"][0]["x"]
                  + line["boundingPolygon"]["normalizedVertices"][1]["x"]
              ) / 2

              # Scan a few lines below for potential values
              for j in range(i + 1, min(i + 4, len(filtered_lines))):
                  next_line = filtered_lines[j]

                  # Calculate the center of the next line
                  next_center_x = (
                      next_line["boundingPolygon"]["normalizedVertices"][0]["x"]
                      + next_line["boundingPolygon"]["normalizedVertices"][1]["x"]
                  ) / 2

                  # Check if the next line is reasonably centered below the current line
                  if abs(current_center_x - next_center_x) < 0.1:  # Relaxed threshold
                      dev_trait["Development Trait"] = next_line["text"]
                      break  # Stop searching for values once a match is found
  return dev_trait

def extract_mentals(data):
  """Extracts the "Mentals" and their values from the JSON data."""

  # Get 'pages' data
  pages = data["pages"]

  # Initialize start and end indices
  start_index = None
  end_index = None

  # Find start and end indices
  for i, line in enumerate(pages[0]["lines"]):
      if line["text"] == "Mentals":
          start_index = i
      # Start searching for end_index only after start_index is found
      elif start_index is not None and line["text"] == "Development Trait":
          end_index = i
          break  # Stop searching once found

  extracted_matches = {}

  # Slice the lines if both indices are found
  if start_index is not None and end_index is not None:
      sliced_lines = pages[0]["lines"][start_index:end_index]

      # Get the center y coordinate of the line containing "Mentals"
      mentals_center_y = (sliced_lines[0]["boundingPolygon"]["normalizedVertices"][0]["y"] + 
                          sliced_lines[0]["boundingPolygon"]["normalizedVertices"][2]["y"]) / 2

      # Get the center y coordinate of the line containing "Development Trait"
      development_trait_center_y = (sliced_lines[-1]["boundingPolygon"]["normalizedVertices"][0]["y"] + 
                                    sliced_lines[-1]["boundingPolygon"]["normalizedVertices"][2]["y"]) / 2

      # Get the left and right boundaries from the line containing "Mentals"
      left_boundary = sliced_lines[0]["boundingPolygon"]["normalizedVertices"][0]["x"] - 0.02  # Add tolerance
      right_boundary = sliced_lines[0]["boundingPolygon"]["normalizedVertices"][1]["x"] + 0.02  # Add tolerance

      # Filter lines based on conditions
      filtered_lines = [
          line
          for line in sliced_lines
          if (
              # Check if line is below "Mentals" and above "Development Trait"
              mentals_center_y <= (line["boundingPolygon"]["normalizedVertices"][0]["y"] + 
                                   line["boundingPolygon"]["normalizedVertices"][2]["y"]) / 2 < development_trait_center_y
              # Check if at least one x-coordinate is within the boundaries
              and any(left_boundary <= v["x"] <= right_boundary for v in line["boundingPolygon"]["normalizedVertices"])
              # Exclude "Mentals"
              and line["text"] != "Mentals"
          )
      ]

      # Extract mentals as a single string
      extracted_matches["Mentals"] = ", ".join([line["text"] for line in filtered_lines])

  return extracted_matches

def extract_bio(data):
    """Extracts the name (first and last), tendency, and position from the JSON data."""

    # Get 'pages' data
    pages = data["pages"]

    # Initialize a dictionary to store the extracted values
    extracted_data = {}

    # Define approximate coordinate ranges with tolerance
    first_name_x_min, first_name_x_max = 0.45, 0.53  # Adjusted for 'AUSTIN' example
    first_name_y_min, first_name_y_max = 0.15, 0.22  # Adjusted for 'AUSTIN' example

    last_name_x_min, last_name_x_max = 0.45, 0.67  # Adjusted for 'CANTWELL' example
    last_name_y_min, last_name_y_max = 0.20, 0.26  # Adjusted for 'CANTWELL' example

    tendency_x_min, tendency_x_max = 0.65, 0.78  # Adjusted for 'Improviser' example
    tendency_y_min, tendency_y_max = 0.22, 0.30  # Adjusted for 'Improviser' example

    # position_x_min, position_x_max = 0.05, 0.12  # Adjusted for 'QB' example
    # position_y_min, position_y_max = 0.15, 0.23  # Adjusted for 'QB' example
    # Update the coordinate ranges for 'Position' based on the new "ATH" location
    position_x_min, position_x_max = 0.67, 0.73  # Adjusted for 'ATH' example
    position_y_min, position_y_max = 0.17, 0.24  # Adjusted for 'ATH' example

    class_x_min, class_x_max = 0.75, 0.85  # Keep the same
    class_y_min, class_y_max = 0.18, 0.23  # Reduce the upper bound to minimize overlap, shift downwards

    hometown_x_min, hometown_x_max = 0.75, 0.87  # Keep the same
    hometown_y_min, hometown_y_max = 0.24, 0.30  # Increase the lower bound to minimize overlap was .24 and .3

    height_weight_x_min, height_weight_x_max = 0.85, 0.96  # Adjusted for '6' 3" . 200 lbs' example
    height_weight_y_min, height_weight_y_max = 0.18, 0.24  # Adjusted for '6' 3" . 200 lbs' example


    # Iterate through the lines in the first page
    for line in pages[0]["lines"]:
        vertices = line["boundingPolygon"]["normalizedVertices"]
        x1, y1 = vertices[0]["x"], vertices[0]["y"]
        x2, y2 = vertices[2]["x"], vertices[2]["y"]

        # Check if coordinates fall within the approximate ranges for 'First Name'
        if (first_name_x_min <= x1 <= first_name_x_max and first_name_y_min <= y1 <= first_name_y_max and
                first_name_x_min <= x2 <= first_name_x_max and first_name_y_min <= y2 <= first_name_y_max):
            extracted_data["First Name"] = line["text"]

        # Check if coordinates fall within the approximate ranges for 'Last Name'
        if (last_name_x_min <= x1 <= last_name_x_max and last_name_y_min <= y1 <= last_name_y_max and
                last_name_x_min <= x2 <= last_name_x_max and last_name_y_min <= y2 <= last_name_y_max):
            extracted_data["Last Name"] = line["text"]

        # Check if coordinates fall within the approximate ranges for 'Tendency'
        if (tendency_x_min <= x1 <= tendency_x_max and tendency_y_min <= y1 <= tendency_y_max and
                tendency_x_min <= x2 <= tendency_x_max and tendency_y_min <= y2 <= tendency_y_max):
            extracted_data["Tendency"] = line["text"]

        # Check if coordinates fall within the approximate ranges for 'Position'
        if (position_x_min <= x1 <= position_x_max and position_y_min <= y1 <= position_y_max and
                position_x_min <= x2 <= position_x_max and position_y_min <= y2 <= position_y_max):
            extracted_data["Position"] = line["text"]
        # Check if coordinates fall within the approximate ranges for 'Class'
        if (class_x_min <= x1 <= class_x_max and class_y_min <= y1 <= class_y_max and
                class_x_min <= x2 <= class_x_max and class_y_min <= y2 <= class_y_max):
            extracted_data["Class"] = line["text"]

        # Check if coordinates fall within the approximate ranges for 'Hometown'
        if (hometown_x_min <= x1 <= hometown_x_max and hometown_y_min <= y1 <= hometown_y_max and
                hometown_x_min <= x2 <= hometown_x_max and hometown_y_min <= y2 <= hometown_y_max):
            extracted_data["Hometown"] = line["text"]

        # Check if coordinates fall within the approximate ranges for 'Height & Weight'
        if (height_weight_x_min <= x1 <= height_weight_x_max and height_weight_y_min <= y1 <= height_weight_y_max and
                height_weight_x_min <= x2 <= height_weight_x_max and height_weight_y_min <= y2 <= height_weight_y_max):
            extracted_data["Height & Weight"] = line["text"]

    # Combine first and last name if both are found
    if "First Name" in extracted_data and "Last Name" in extracted_data:
        extracted_data["Name"] = extracted_data["First Name"] + " " + extracted_data["Last Name"]
        del extracted_data["First Name"]
        del extracted_data["Last Name"]

    # Reorder the dictionary to put 'Name' first (if it exists)
    if "Name" in extracted_data:
        extracted_data = {"Name": extracted_data["Name"]} | extracted_data  # Python 3.9+ syntax

    return extracted_data

def process_json_files_in_folder(folder_path):
    """Processes all JSON files in the specified folder and writes the extracted data to a CSV file."""

    # Print the folder path being used
    print(f"Searching for JSON files in: {folder_path}")

    all_attribute_keys = set()

    # Collect all unique attribute keys before processing files
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            try:
                data = load_json_data(file_path)
                attributes_data = extract_attributes(data)
                all_attribute_keys.update(attributes_data.keys())
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON format in file {filename}")

    # Check if any JSON files were found
    if not all_attribute_keys:
        print("No JSON files found in the specified folder.")
        return

    # Open the CSV file for writing after collecting all attribute keys
    with open("player_data.csv", "w", newline="") as csvfile:
        # Updated fieldnames to include 'State'
        fieldnames = ['Name', 'Position', 'Class', 'Hometown', 'State', 'Height & Weight', 'Tendency', 'star_rating', 'overall_rating', 'development_trait', 'abilities', 'mentals'] + list(all_attribute_keys) 
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row immediately
        writer.writeheader()

        # Now process each file and write data to CSV
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)

                # Print the filename being processed
                print(f"Processing file: {filename}")

                try:
                    data = load_json_data(file_path)

                    # Extract bio_data before printing it
                    bio_data = extract_bio(data)

                    # Print the extracted bio_data
                    print(f"Extracted bio_data: {bio_data}")

                    # Check if name_data is valid
                    if bio_data is None or bio_data.get("Name") is None:
                        print(f"Error processing file {filename}: Unable to extract player name.")
                        continue  # Skip to the next file

                    # Extract State from Hometown if available
                    if "Hometown" in bio_data:
                        hometown = bio_data["Hometown"]
                        if ", " in hometown:
                            city, state = hometown.split(", ")
                            bio_data["State"] = state.strip()  # Remove any extra spaces

                    dev_trait_data = extract_dev_trait(data) or {}
                    abilities_data = extract_abilities(data) or {}
                    mentals_data = extract_mentals(data) or {}
                    attributes_data = extract_attributes(data) or {}

                    # Prepare the row data as a dictionary, including new bio fields
                    row_data = {
                        'Name': bio_data.get("Name"),
                        'Position': bio_data.get("Position"),
                        'Class': bio_data.get("Class"),
                        'Hometown': bio_data.get("Hometown"),
                        'State': bio_data.get("State"),  # Include State in the row
                        'Height & Weight': bio_data.get("Height & Weight"),
                        'Tendency': bio_data.get("Tendency"),
                        'star_rating': 4,  # Replace with actual extraction logic if available
                        'overall_rating': 69,  # Replace with actual extraction logic if available
                        'development_trait': dev_trait_data.get("Development Trait"),
                        'abilities': abilities_data.get("Abilities"),
                        'mentals': mentals_data.get("Mentals")
                    }
                    row_data.update(attributes_data)  # Add attributes to the row

                    # Write the row to the CSV file
                    writer.writerow(row_data)

                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON format in file {filename}")
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")

if __name__ == "__main__":
    folder_path = os.getcwd()  # Replace with the actual folder path
    process_json_files_in_folder(folder_path)
   
#     file_path = "cantwell.json"  # Replace with your actual file path
#     data = load_json_data(file_path)

# #extract name
# name = extract_bio(data)
# print(f"***Player Info:***")
# for key, value in name.items():
#     print(f"{key}: {value}")
# print(f"Star Rating: 4")
# print(f"Overall Rating: 69")

# # Extract the development trait
# extracted_data = extract_dev_trait(data)
# for key, value in extracted_data.items():
#     print(f"{key}: {value}")

# # Extract the abilities
# abilities = extract_abilities(data)
# for key, value in abilities.items():
#     print(f"{key}: {value}")

# # Extract the mentals
# mentals = extract_mentals(data)
# for key, value in mentals.items():
#     print(f"{key}: {value}")

# ## call and print key value pairs for attributes
# attributes = extract_attributes(data)
# for key, value in attributes.items():
#     print(f"{key}: {value}")
