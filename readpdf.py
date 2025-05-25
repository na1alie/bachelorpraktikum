import fitz  
import re
import json

#quatsch, nur versuch aus pdf infos zu entnehmen
doc = fitz.open("Modulhandbuch-Inf-IC.pdf")
courses = []

for page in doc:
    text = page.get_text()
    if "Modulbezeichnung:" in text:
        blocks = re.split(r"(?=Modulbezeichnung:)", text)
        for block in blocks:
            modul = re.search(r"Modulbezeichnung:\s*(.*)", block)
            inhalt = re.search(r"Inhalt:\s*(.*?)(Studien-/Prüfungsleistungen:|Literatur:)", block, re.DOTALL)
            if modul and inhalt:
                courses.append({
                    "modul": modul.group(1).strip(),
                    "inhalt": inhalt.group(1).strip()
                })

print(json.dumps(courses, indent=2, ensure_ascii=False))