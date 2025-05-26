import fitz  
import re
import json


pdf_path = "course_offers/Modulhandbuch_BSc_Mathematik.pdf"
doc = fitz.open(pdf_path)

all_text = "\n".join(page.get_text() for page in doc)

clean_text = re.sub(r"Modulhandbuch\s+Generiert am \d{2}\.\d{2}\.\d{4}\s+Seite \d+ von \d+\s*", '', all_text)

# Pattern für 'Modulbeschreibung' + Zeile danach 
modul_iter = re.finditer(r"Modulbeschreibung\n(.*)\n(?:.|\n)*?Voraussetzungen:\n((?:.|\n)*?)Inhalt:\n((?:.|\n)*?)Lernergebnisse:", clean_text)

courses_from_pdf = []
for modul in modul_iter:
    title = modul.group(1).strip()
    requirement = modul.group(2).strip()
    content = modul.group(3).strip()
    if requirement and content:
        description = f"Voraussetzungen:\n{requirement}\n\nInhalt:\n{content}"
        courses_from_pdf.append({
            "title": title,
            "description": description
        })

with open("courses_from_pdf.json", "w", encoding="utf-8") as f:
    json.dump(courses_from_pdf, f, ensure_ascii=False, indent=2)
