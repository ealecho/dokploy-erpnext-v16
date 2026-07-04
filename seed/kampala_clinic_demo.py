#!/usr/bin/env python3
"""Seed realistic demo data for a Kampala clinic into a Frappe Health (Marley) site.

Creates practitioners, patients, appointment types, lab test templates,
medications, appointments, vitals, and encounters with Ugandan-realistic
names, conditions, and UGX pricing. Idempotent: safe to run more than once.

Usage (on the Dokploy server):

    docker cp seed/kampala_clinic_demo.py <backend-container>:/tmp/
    docker exec <backend-container> bash -c \
        "cd /home/frappe/frappe-bench/sites && ../env/bin/python /tmp/kampala_clinic_demo.py <site-name>"

Requires: setup wizard completed and the healthcare app installed on the site.
"""

import sys
from datetime import date, datetime, timedelta

import frappe

created = {"count": 0}


def upsert(doctype, filters, extra=None, submit=False):
    """Return existing doc name or create the doc. Never raises: logs and returns None on failure."""
    name = frappe.db.exists(doctype, filters)
    if name:
        return name
    try:
        doc = frappe.get_doc({"doctype": doctype, **filters, **(extra or {})})
        doc.flags.ignore_mandatory = False
        doc.insert(ignore_permissions=True)
        if submit:
            doc.submit()
        created["count"] += 1
        print(f"  + {doctype}: {doc.name}")
        return doc.name
    except Exception as e:
        print(f"  ! {doctype} {filters}: {e}")
        return None


# ---------------------------------------------------------------- masters

DEPARTMENTS = ["General Medicine", "Paediatrics", "Dental", "Laboratory", "Pharmacy"]

PRACTITIONERS = [
    # (first, last, gender, department, consultation fee UGX)
    ("Sarah", "Nakato", "Female", "General Medicine", 50000),
    ("David", "Okello", "Male", "Paediatrics", 50000),
    ("Grace", "Namubiru", "Female", "Gynaecology", 60000),
    ("Peter", "Ssemakula", "Male", "Dental", 40000),
    ("Agnes", "Atim", "Female", "General Medicine", 50000),
    ("Josephine", "Nabirye", "Female", "Maternity", 30000),
]

APPOINTMENT_TYPES = [
    ("New Patient Consultation", 30),
    ("Follow Up", 15),
    ("Antenatal Visit", 30),
    ("Immunisation", 15),
    ("Dental Checkup", 30),
]

LAB_TESTS = [
    # (name, code, rate UGX, sample)
    ("Malaria Rapid Diagnostic Test", "MRDT", 15000, "Blood"),
    ("Blood Smear for Malaria Parasites", "B/S", 10000, "Blood"),
    ("Complete Blood Count", "CBC", 35000, "Blood"),
    ("Widal Test", "WIDAL", 20000, "Blood"),
    ("HIV Rapid Test", "HIV-R", 10000, "Blood"),
    ("Random Blood Sugar", "RBS", 10000, "Blood"),
    ("Urinalysis", "URINE", 15000, "Urine"),
    ("Stool Microscopy", "STOOL", 15000, "Stool"),
    ("Hepatitis B Surface Antigen", "HBsAg", 25000, "Blood"),
    ("Pregnancy Test (hCG)", "HCG", 10000, "Urine"),
    ("Blood Grouping & Rhesus", "BG-RH", 15000, "Blood"),
    ("Syphilis (RPR)", "RPR", 15000, "Blood"),
]

COMPLAINTS = [
    "Fever", "Headache", "Cough", "Abdominal pain", "Joint pain",
    "General body weakness", "Vomiting", "Diarrhoea", "Skin rash",
    "Painful urination", "Toothache", "Loss of appetite",
]

DIAGNOSES = [
    "Malaria", "Typhoid Fever", "Upper Respiratory Tract Infection",
    "Urinary Tract Infection", "Hypertension", "Type 2 Diabetes Mellitus",
    "Peptic Ulcer Disease", "Gastroenteritis", "Dental Caries",
    "Intestinal Worms", "Anaemia", "Normal Pregnancy",
]

MEDICATION_CLASSES = [
    "Antimalarial", "Antibiotic", "Analgesic", "Antihypertensive",
    "Antidiabetic", "Proton Pump Inhibitor", "Anthelmintic", "Supplement",
]

MEDICATIONS = [
    # (generic name, class, strength, form)
    ("Artemether + Lumefantrine", "Antimalarial", 20, "Tablet"),
    ("Artesunate", "Antimalarial", 60, "Injection"),
    ("Amoxicillin", "Antibiotic", 500, "Capsule"),
    ("Amoxicillin Suspension", "Antibiotic", 125, "Syrup"),
    ("Ciprofloxacin", "Antibiotic", 500, "Tablet"),
    ("Paracetamol", "Analgesic", 500, "Tablet"),
    ("Ibuprofen", "Analgesic", 400, "Tablet"),
    ("Omeprazole", "Proton Pump Inhibitor", 20, "Capsule"),
    ("Amlodipine", "Antihypertensive", 5, "Tablet"),
    ("Metformin", "Antidiabetic", 500, "Tablet"),
    ("Mebendazole", "Anthelmintic", 500, "Tablet"),
    ("Ferrous Sulphate + Folic Acid", "Supplement", 200, "Tablet"),
]

PATIENTS = [
    # (first, last, sex, yob, mobile, area, occupation, blood group)
    ("Immaculate", "Nakimuli", "Female", 1992, "+256 772 481 133", "Ntinda", "Teacher", "O+"),
    ("Ronald", "Mukasa", "Male", 1985, "+256 701 224 890", "Bukoto", "Driver", "A+"),
    ("Betty", "Namutebi", "Female", 1978, "+256 782 337 415", "Kawempe", "Market Vendor", "B+"),
    ("Brian", "Okello", "Male", 2019, "+256 759 668 202", "Naguru", "", ""),
    ("Susan", "Achola", "Female", 1990, "+256 704 519 776", "Nakawa", "Accountant", "O-"),
    ("Moses", "Ssentongo", "Male", 1969, "+256 772 903 348", "Rubaga", "Retired Civil Servant", "A+"),
    ("Diana", "Ainembabazi", "Female", 1995, "+256 787 254 611", "Kololo", "Bank Officer", "AB+"),
    ("Kenneth", "Tumwine", "Male", 1988, "+256 703 481 927", "Bugolobi", "Engineer", "O+"),
    ("Aisha", "Nabukenya", "Female", 2001, "+256 758 112 340", "Kisenyi", "Student", "B+"),
    ("Ivan", "Kizza", "Male", 1993, "+256 771 645 208", "Makindye", "Graphic Designer", "O+"),
    ("Prossy", "Nansubuga", "Female", 1983, "+256 782 990 137", "Nansana", "Hairdresser", "A-"),
    ("Emmanuel", "Odongo", "Male", 1975, "+256 750 823 464", "Ntinda", "Security Guard", "O+"),
    ("Winnie", "Apio", "Female", 1998, "+256 706 337 851", "Kireka", "Waitress", "B-"),
    ("Godfrey", "Lubega", "Male", 1958, "+256 772 445 620", "Mengo", "Farmer", "A+"),
    ("Stella", "Mbabazi", "Female", 1987, "+256 788 210 973", "Naalya", "Shopkeeper", "O+"),
    ("Hassan", "Ssekandi", "Male", 2015, "+256 701 559 384", "Kibuli", "", ""),
    ("Rebecca", "Auma", "Female", 1991, "+256 784 672 015", "Banda", "Teacher", "O+"),
    ("Joan", "Nakalembe", "Female", 2024, "+256 759 301 288", "Kyaliwajjala", "", ""),
]

# encounters: (patient idx, practitioner idx, days ago, complaints, diagnosis,
#              [(medication, period, note)], [lab tests],
#              vitals (temp, pulse, rr, sys, dia, height m, weight kg))
ENCOUNTERS = [
    (1, 0, 2, ["Fever", "Headache", "General body weakness"], "Malaria",
     [("Artemether + Lumefantrine", "3 Day", "4 tablets twice daily with food"),
      ("Paracetamol", "3 Day", "2 tablets three times daily")],
     ["Malaria Rapid Diagnostic Test"], ("38.9", "96", "20", "118", "76", 1.74, 72)),
    (2, 0, 3, ["Fever", "Abdominal pain", "Loss of appetite"], "Typhoid Fever",
     [("Ciprofloxacin", "7 Day", "1 tablet twice daily")],
     ["Widal Test", "Complete Blood Count"], ("38.2", "88", "18", "112", "74", 1.61, 65)),
    (5, 4, 1, ["Headache"], "Hypertension",
     [("Amlodipine", "1 Month", "1 tablet once daily, review in 30 days")],
     ["Random Blood Sugar"], ("36.8", "78", "16", "158", "98", 1.70, 81)),
    (3, 1, 1, ["Cough", "Fever"], "Upper Respiratory Tract Infection",
     [("Amoxicillin Suspension", "5 Day", "5 ml three times daily"),
      ("Paracetamol", "3 Day", "Half tablet when temperature is above 38C")],
     [], ("37.9", "110", "26", "", "", 1.05, 16)),
    (6, 0, 2, ["Painful urination"], "Urinary Tract Infection",
     [("Ciprofloxacin", "5 Day", "1 tablet twice daily")],
     ["Urinalysis"], ("37.1", "82", "16", "121", "79", 1.66, 60)),
    (16, 2, 4, [], "Normal Pregnancy",
     [("Ferrous Sulphate + Folic Acid", "1 Month", "1 tablet daily")],
     ["Blood Grouping & Rhesus", "HIV Rapid Test", "Hepatitis B Surface Antigen"],
     ("36.9", "84", "17", "110", "70", 1.63, 68)),
]

# appointments: (patient idx, practitioner idx, day offset, time, type, status)
APPOINTMENTS = [
    (0, 0, 0, "09:00:00", "New Patient Consultation", "Open"),
    (7, 0, 0, "09:30:00", "New Patient Consultation", "Open"),
    (9, 4, 0, "10:00:00", "New Patient Consultation", "Open"),
    (13, 4, 0, "10:30:00", "Follow Up", "Open"),
    (16, 2, 0, "11:00:00", "Antenatal Visit", "Open"),
    (17, 1, 0, "11:30:00", "Immunisation", "Open"),
    (4, 3, 0, "14:00:00", "Dental Checkup", "Open"),
    (8, 0, 1, "09:00:00", "New Patient Consultation", "Scheduled"),
    (10, 4, 1, "09:30:00", "New Patient Consultation", "Scheduled"),
    (12, 0, 1, "10:00:00", "Follow Up", "Scheduled"),
    (14, 3, 1, "11:00:00", "Dental Checkup", "Scheduled"),
    (11, 4, 2, "09:00:00", "Follow Up", "Scheduled"),
    (15, 1, 2, "10:00:00", "New Patient Consultation", "Scheduled"),
    (5, 4, 3, "09:30:00", "Follow Up", "Scheduled"),
]


def main(site):
    frappe.init(site=site)
    frappe.connect()
    frappe.set_user("Administrator")
    frappe.flags.mute_emails = True

    if not frappe.db.get_single_value("System Settings", "setup_complete"):
        print("ERROR: complete the setup wizard (login as Administrator in the browser) before seeding.")
        sys.exit(1)
    if "healthcare" not in frappe.get_installed_apps():
        print("ERROR: the healthcare app is not installed on this site.")
        sys.exit(1)

    company = frappe.defaults.get_global_default("company")
    print(f"Seeding demo data into site '{site}' (company: {company})\n")

    print("Medical departments:")
    for d in DEPARTMENTS:
        upsert("Medical Department", {"department": d})

    print("Practitioners:")
    practitioner_names = []
    for first, last, gender, dept, fee in PRACTITIONERS:
        upsert("Medical Department", {"department": dept})
        name = upsert(
            "Healthcare Practitioner",
            {"first_name": f"Dr {first}", "last_name": last},
            {"gender": gender, "department": dept, "status": "Active",
             "op_consulting_charge": fee},
        )
        practitioner_names.append(name)

    print("Appointment types:")
    for atype, duration in APPOINTMENT_TYPES:
        upsert("Appointment Type", {"appointment_type": atype},
               {"default_duration": duration, "allow_booking_for": "Practitioner"})

    print("Lab test templates:")
    upsert("Item Group", {"item_group_name": "Laboratory"},
           {"parent_item_group": "All Item Groups", "is_group": 0})
    for test, code, rate, sample in LAB_TESTS:
        upsert("Lab Test Sample", {"sample": sample})
        upsert("Lab Test Template", {"lab_test_name": test},
               {"lab_test_code": code, "lab_test_group": "Laboratory",
                "department": "Laboratory", "lab_test_template_type": "Single",
                "is_billable": 1, "lab_test_rate": rate, "sample": sample})

    print("Complaints and diagnoses:")
    for c in COMPLAINTS:
        upsert("Complaint", {"complaints": c})
    for d in DIAGNOSES:
        upsert("Diagnosis", {"diagnosis": d})

    print("Medications:")
    upsert("UOM", {"uom_name": "mg"})
    for mc in MEDICATION_CLASSES:
        upsert("Medication Class", {"medication_class": mc})
    for generic, mclass, strength, form in MEDICATIONS:
        upsert("Dosage Form", {"dosage_form": form})
        upsert("Medication", {"generic_name": generic},
               {"medication_class": mclass, "strength": strength,
                "strength_uom": "mg", "dosage_form": form})

    print("Prescription durations:")
    for number, period in [(3, "Day"), (5, "Day"), (7, "Day"), (14, "Day"), (1, "Month")]:
        upsert("Prescription Duration", {"number": number, "period": period})

    print("Patients:")
    patient_names = []
    for first, last, sex, yob, mobile, area, occupation, blood in PATIENTS:
        extra = {
            "sex": sex,
            "dob": date(yob, ((yob * 7) % 12) + 1, ((yob * 3) % 27) + 1),
            "mobile": mobile,
        }
        if occupation:
            extra["occupation"] = occupation
        if blood:
            extra["blood_group"] = blood
        name = upsert("Patient", {"first_name": first, "last_name": last}, extra)
        patient_names.append(name)

    print("Appointments:")
    today = date.today()
    for p_idx, pr_idx, offset, time_, atype, status in APPOINTMENTS:
        patient, practitioner = patient_names[p_idx], practitioner_names[pr_idx]
        if not (patient and practitioner):
            continue
        appt_date = today + timedelta(days=offset)
        dept = frappe.db.get_value("Healthcare Practitioner", practitioner, "department")
        upsert("Patient Appointment",
               {"patient": patient, "practitioner": practitioner,
                "appointment_date": appt_date, "appointment_time": time_},
               {"appointment_for": "Practitioner", "appointment_type": atype,
                "department": dept, "company": company, "status": status,
                "duration": frappe.db.get_value("Appointment Type", atype, "default_duration") or 15})

    print("Encounters and vitals:")
    for (p_idx, pr_idx, days_ago, complaints, diagnosis,
         drugs, labs, vitals) in ENCOUNTERS:
        patient, practitioner = patient_names[p_idx], practitioner_names[pr_idx]
        if not (patient and practitioner):
            continue
        enc_date = today - timedelta(days=days_ago)

        temp, pulse, rr, sys_bp, dia_bp, height, weight = vitals
        upsert("Vital Signs", {"patient": patient, "signs_date": enc_date},
               {"signs_time": "09:15:00", "temperature": temp, "pulse": pulse,
                "respiratory_rate": rr, "bp_systolic": sys_bp, "bp_diastolic": dia_bp,
                "height": height, "weight": weight, "company": company})

        if frappe.db.exists("Patient Encounter",
                            {"patient": patient, "encounter_date": enc_date}):
            continue
        try:
            enc = frappe.get_doc({
                "doctype": "Patient Encounter",
                "patient": patient,
                "practitioner": practitioner,
                "appointment_type": "New Patient Consultation",
                "encounter_date": enc_date,
                "encounter_time": "09:30:00",
                "company": company,
                "symptoms": [{"complaint": c} for c in complaints],
                "diagnosis": [{"diagnosis": diagnosis}],
                "drug_prescription": [
                    {"medication": med, "drug_name": med, "period": period,
                     "dosage_form": frappe.db.get_value("Medication", {"generic_name": med}, "dosage_form") or "Tablet",
                     "comment": note}
                    for med, period, note in drugs
                ],
                "lab_test_prescription": [
                    {"lab_test_code": frappe.db.get_value("Lab Test Template", {"lab_test_name": t}, "name"),
                     "lab_test_name": t}
                    for t in labs
                ],
            })
            enc.insert(ignore_permissions=True)
            created["count"] += 1
            print(f"  + Patient Encounter: {enc.name} ({diagnosis})")
        except Exception as e:
            print(f"  ! Patient Encounter for {patient}: {e}")

    frappe.db.commit()
    print(f"\nDone. {created['count']} documents created (existing ones were kept).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
