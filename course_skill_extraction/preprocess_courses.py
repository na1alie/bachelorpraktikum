import json


with open("../course_offer_collection/content.json", "r", encoding="utf-8") as f:
    courses = json.load(f)


#only take courses from Department Computer Science
filtered_content = []
for course in courses:
    inhalt = course.get("inhalt", "").strip()
    lernergebnisse = course.get("lernergebnisse", "").strip()
    name = course.get("name", "").strip()
    kennung = course.get("kennung", "").strip()
    anmerkung = course.get("anmerkung", "").strip()
    organisation = course.get("organisation", "").strip()

    exclude_due_to_anmerkung = (
        name == "" or
        kennung == "" or
        anmerkung == "Die Lehrveranstaltungen werden nicht mehr angeboten." or
        anmerkung == "Dieses Modul wird nicht mehr angeboten!" or
        anmerkung == "Wird nicht mehr angeboten." or
        anmerkung.startswith("Das Modul wird nicht mehr angeboten.") or
        organisation != "Department Computer Science"
    )

    if (inhalt or lernergebnisse) and not exclude_due_to_anmerkung:
        filtered_content.append(course)



with open("filtered_content.json", "w") as outfile:
    json.dump(filtered_content, outfile, indent=4, ensure_ascii=False)

print(f"{len(filtered_content)} courses written to 'filtered_content.json'")
print(f"{len(courses)} courses in content.json'")
