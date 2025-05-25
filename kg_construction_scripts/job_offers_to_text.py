from bs4 import BeautifulSoup
import os

# Script to turn html code of job offers into text files

# Set the directory containing your HTML files
directory = "job_offers"  # e.g., "data/jobs/"

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".html"):
        txt_filename = filename.rsplit('.', 1)[0] + ".txt"
        txt_file_path = os.path.join(directory, txt_filename)
        
        # Proceed only if .txt file does NOT exist
        if not os.path.exists(txt_file_path):
            file_path = os.path.join(directory, filename)

            # Read the HTML content
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Parse with BeautifulSoup and extract text
            soup = BeautifulSoup(html_content, "lxml")
            plain_text = soup.get_text(separator="\n", strip=True)

            # Create new filename with .txt extension
            txt_filename = filename.rsplit('.', 1)[0] + ".txt"
            txt_file_path = os.path.join(directory, txt_filename)

            # Write the extracted plain text to the new .txt file
            with open(txt_file_path, "w", encoding="utf-8") as f:
                f.write(plain_text)

            print(f"Processed and saved: {txt_filename}")
