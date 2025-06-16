import json
from fpdf import FPDF

def json_to_pdf(json_path, pdf_path):
    # Load JSON data
    with open(json_path, "r") as f:
        data = json.load(f)

    sample_data = data[:1]
    
    for s in sample_data:
        s["job_description_formatted"] = ""
    # Pretty print JSON string
    pretty_text = json.dumps(sample_data, indent=4)

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Courier", size=10)

    # Split pretty text into lines that fit the page width
    max_width = 190  # approx page width in mm
    line_height = 5

    # Since Courier is monospaced, approx char width ~2.5 mm, max chars per line ~ max_width / 2.5 = 76
    max_chars = 76
    lines = []
    for paragraph in pretty_text.splitlines():
        while len(paragraph) > max_chars:
            lines.append(paragraph[:max_chars])
            paragraph = paragraph[max_chars:]
        lines.append(paragraph)

    # Add lines to PDF
    for line in lines:
        pdf.cell(0, line_height, line, ln=1)

    # Save PDF
    pdf.output(pdf_path)
    print(f"Saved PDF: {pdf_path}")

# Example usage:
#json_to_pdf("courses_cs_bsc/cs_bsc_courses_info.json", "courses_cs_bsc/cs_bsc_courses_info.pdf")
json_to_pdf("job_offer_collection/job_results_bright_data.json", "job_offer_collection/job_results_bright_data.pdf")
