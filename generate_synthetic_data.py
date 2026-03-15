# generate_synthetic_data.py
# Generates realistic fake German insurance claim PDFs
# matching the structure of duden Wakanda claims data.
# Use this for public portfolio — never commit real customer data.

import os
import random
from datetime import datetime, timedelta
from fpdf import FPDF

os.makedirs("data/synthetic_pdfs", exist_ok=True)

# --- Fake but realistic German names and data ---
FIRST_NAMES = [
    "Thomas", "Maria", "Klaus", "Andrea", "Michael",
    "Sabine", "Wolfgang", "Elisabeth", "Stefan", "Monika",
    "Peter", "Ingrid", "Christian", "Ursula", "Markus"
]

LAST_NAMES = [
    "Müller", "Schmidt", "Weber", "Wagner", "Becker",
    "Hoffmann", "Gruber", "Huber", "Steiner", "Bauer",
    "Maier", "Leitner", "Berger", "Fischer", "Schwarz"
]

DAMAGE_TYPES = [
    "Leitungswasser",      # pipe water damage
    "Elementarschaden",    # natural disaster
    "Einbruchdiebstahl",   # burglary
    "Sturmschaden",        # storm damage
    "Brandschaden",        # fire damage
    "Glasbruch",           # glass breakage
]

DAMAGE_DESCRIPTIONS = {
    "Leitungswasser": [
        "Durch austretendes Leitungswasser wurden Decke und Wände beschädigt.",
        "Ein geplatztes Rohr hat den Keller überflutet und den Bodenbelag beschädigt.",
        "Wasserrohrbruch im Badezimmer hat zu erheblichen Schäden an der Bausubstanz geführt.",
    ],
    "Elementarschaden": [
        "Starkregen hat zu Überflutung des Kellers geführt.",
        "Hagel hat das Dach und die Fassade beschädigt.",
        "Hochwasser hat Erdgeschoss und Keller beschädigt.",
    ],
    "Einbruchdiebstahl": [
        "Unbekannte Täter haben die Eingangstür aufgebrochen und Wertgegenstände entwendet.",
        "Einbruch durch Kellerfenster, mehrere Elektrogeräte gestohlen.",
        "Aufgebrochene Terrassentür, Bargeld und Schmuck entwendet.",
    ],
    "Sturmschaden": [
        "Sturm hat Dachziegel abgedeckt und zu Wassereintritt geführt.",
        "Umgestürzter Baum hat das Carport beschädigt.",
        "Sturmböen haben die Terrassenüberdachung zerstört.",
    ],
    "Brandschaden": [
        "Küchenbrand durch defektes Elektrogerät, erhebliche Rußschäden.",
        "Kaminbrand hat auf Dachstuhl übergegriffen.",
        "Elektrischer Kurzschluss hat zu Brand im Verteilerkasten geführt.",
    ],
    "Glasbruch": [
        "Fensterscheibe durch Steinwurf beschädigt.",
        "Glastür durch Sturm eingedrückt.",
        "Terrassenfenster durch herabfallenden Ast gebrochen.",
    ],
}

REQUIRED_DOCUMENTS = {
    "Leitungswasser": [
        "Leckortungsprotokoll",
        "Fotos des Schadens",
        "Kostenvoranschlag der Reparatur",
        "Rechnung des Installateurs",
    ],
    "Elementarschaden": [
        "Fotos des Schadens",
        "Niederschlagsnachweis",
        "Kostenvoranschlag",
        "Behördliche Bestätigung",
    ],
    "Einbruchdiebstahl": [
        "Polizeianzeige",
        "Inventarliste der gestohlenen Gegenstände",
        "Fotos der Einbruchspuren",
        "Kaufbelege der entwendeten Gegenstände",
    ],
    "Sturmschaden": [
        "Fotos des Schadens",
        "Wetterbericht",
        "Kostenvoranschlag",
        "Dachdecker-Rechnung",
    ],
    "Brandschaden": [
        "Feuerwehrprotokoll",
        "Fotos des Schadens",
        "Kostenvoranschlag",
        "Liste der beschädigten Gegenstände",
    ],
    "Glasbruch": [
        "Fotos des Schadens",
        "Kostenvoranschlag des Glasers",
        "Rechnung",
    ],
}

URGENCY_LEVELS = ["normal", "normal", "normal", "high", "low"]  # weighted toward normal

EMAIL_TEMPLATES = [
    # Template 1: Customer reporting damage
    """Email received on: {date} CEST
Subject: {claim_number}
From: {sender_email}
To: Schaden (duden)
Cc:
Attachments: {attachment}

Sehr geehrte Damen und Herren,

anbei übermittle ich Ihnen die Schadenmeldung bezüglich meiner Polizze {policy_number}.

Schadenart: {damage_type}
Schadendatum: {damage_date}

{damage_description}

Ich bitte um rasche Bearbeitung meines Anliegens.

Mit freundlichen Grüßen,
{full_name}
Tel: {phone}""",

    # Template 2: duden requesting documents
    """Email received on: {date} CEST
Subject: {claim_number}
From: {duden_email}
To: {sender_email}
Cc:
Attachments:

Sehr geehrte/r {full_name},

vielen Dank für Ihre Schadenmeldung zur Schadennummer {claim_number}.

Um Ihren Schaden bearbeiten zu können, benötigen wir folgende Unterlagen:

{required_docs}

Bitte senden Sie uns diese Dokumente so bald wie möglich zu.

Mit freundlichen Grüßen,
Schadenabteilung duden Österreich
{duden_email}""",

    # Template 3: Follow-up from customer
    """Email received on: {date} CEST
Subject: AW: {claim_number}
From: {sender_email}
To: Schaden (duden)
Cc:
Attachments: {attachment}

Sehr geehrte Damen und Herren,

bezugnehmend auf Ihre Anfrage zur Schadennummer {claim_number} übersende ich Ihnen anbei die angeforderten Unterlagen.

{damage_description}

Bitte bestätigen Sie den Eingang der Dokumente.

Mit freundlichen Grüßen,
{full_name}""",

    # Template 4: Invoice submission
    """Email received on: {date} CEST
Subject: Rechnung {claim_number}
From: {sender_email}
To: Schaden (duden)
Cc:
Attachments: Rechnung_{claim_number}.pdf

Sehr geehrte Damen und Herren,

anbei erhalten Sie die Rechnung für die Schadenbehebung zur Schadennummer {claim_number}.

Rechnungsbetrag: {invoice_amount} EUR
Schadendatum: {damage_date}
Polizzennummer: {policy_number}

Ich bitte um Überweisung des Betrages auf mein Konto.

Mit freundlichen Grüßen,
{full_name}
IBAN: AT{iban}""",
]

duden_EMAILS = [
    "schaden@duden.at",
    "schadenmeldung@duden.at",
    "kfz-schaden@duden.at",
    "haushaltsschaden@duden.at",
]


def random_date(start_year=2024, end_year=2025) -> datetime:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_claim_number() -> str:
    year = random.choice([2024, 2025])
    num1 = random.randint(1000000, 9999999)
    num2 = random.randint(10000000, 99999999)
    return f"SYN-{year}-{num1}-{num2}"


def generate_policy_number() -> str:
    prefix = random.choice(["A", "B", "C", "D"])
    return f"FAKE-{prefix}{random.randint(10000, 99999)}-{random.randint(1000, 9999)}"


def generate_fake_email(first, last) -> str:
    formats = [
        f"{first.lower()}.{last.lower()}@gmail.com",
        f"{first.lower()}{last.lower()}@outlook.com",
        f"{first.lower()}.{last.lower()}@gmx.at",
        f"{first[0].lower()}{last.lower()}@icloud.com",
    ]
    return random.choice(formats)


def generate_phone() -> str:
    return f"+43 {random.randint(600, 699)} {random.randint(1000000, 9999999)}"


def generate_iban() -> str:
    return f"00 0000 0000 {random.randint(1000, 9999)} {random.randint(1000, 9999)}"


def generate_invoice_amount() -> str:
    amount = random.randint(150, 15000)
    return f"{amount:,}".replace(",", ".")


def generate_attachment(damage_type: str) -> str:
    attachments = {
        "Leitungswasser": ["Foto_Schaden.jpg", "Leckortung.pdf", "Kostenvoranschlag.pdf"],
        "Elementarschaden": ["Schadenfotos.jpg", "Niederschlagsnachweis.pdf"],
        "Einbruchdiebstahl": ["Polizeianzeige.pdf", "Inventarliste.pdf", "Fotos.jpg"],
        "Sturmschaden": ["Schadenfotos.jpg", "Kostenvoranschlag.pdf"],
        "Brandschaden": ["Feuerwehrprotokoll.pdf", "Schadenfotos.jpg"],
        "Glasbruch": ["Foto_Glasbruch.jpg", "Kostenvoranschlag.pdf"],
    }
    return random.choice(attachments.get(damage_type, ["Dokument.pdf"]))


def generate_required_docs_text(damage_type: str) -> str:
    docs = REQUIRED_DOCUMENTS.get(damage_type, ["Schadendokumentation"])
    return "\n".join(f"• {doc}" for doc in docs)


def generate_email_content() -> str:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    full_name = f"{first} {last}"
    damage_type = random.choice(DAMAGE_TYPES)
    email_date = random_date()
    damage_date = email_date - timedelta(days=random.randint(1, 30))
    claim_number = generate_claim_number()
    template = random.choice(EMAIL_TEMPLATES)

    content = template.format(
        date=email_date.strftime("%d-%b-%Y %H:%M:%S.%S"),
        claim_number=claim_number,
        sender_email=generate_fake_email(first, last),
        duden_email=random.choice(duden_EMAILS),
        full_name=full_name,
        policy_number=generate_policy_number(),
        damage_type=damage_type,
        damage_date=damage_date.strftime("%d.%m.%Y"),
        damage_description=random.choice(DAMAGE_DESCRIPTIONS[damage_type]),
        required_docs=generate_required_docs_text(damage_type),
        attachment=generate_attachment(damage_type),
        invoice_amount=generate_invoice_amount(),
        phone=generate_phone(),
        iban=generate_iban(),
    )
    return content, claim_number, damage_type


def create_pdf(content: str, output_path: str, num_pages: int = 1):
    """Creates a PDF with the email content, optionally multi-page."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for page in range(num_pages):
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)

        if page == 0:
            # First page has the actual content
            # Handle German characters by encoding safely
            safe_content = content.encode(
                'latin-1', errors='replace').decode('latin-1')
            width = pdf.w - pdf.l_margin - pdf.r_margin
            for line in safe_content.split('\n'):
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(width, 5, line)
        else:
            # Additional pages simulate attachments/scans
            pdf.set_font("Helvetica", style="I", size=12)
            pdf.cell(0, 10, f"[Anlage {page} - Scan/Foto]", ln=True)
            pdf.set_font("Helvetica", size=9)
            pdf.cell(
                0, 8, "Dieses Dokument ist ein Anhang zur Schadenmeldung.", ln=True)

    pdf.output(output_path)


def generate_dataset(num_documents: int = 90):
    """Generates a complete synthetic dataset."""
    print(f"Generating {num_documents} synthetic insurance claim PDFs...")

    for i in range(num_documents):
        content, claim_number, damage_type = generate_email_content()

        # Vary document length — some short, some multi-page
        num_pages = random.choices(
            [1, 2, 3, 5, 8],
            weights=[30, 30, 20, 15, 5]
        )[0]

        # Create filename matching real data structure
        year = random.choice([2024, 2025])
        id1 = random.randint(1000000, 9999999)
        id2 = random.randint(10000000, 99999999)
        filename = f"claim_{year}{id1}_{id2}.pdf"
        output_path = os.path.join("data/pdfs", filename)

        create_pdf(content, output_path, num_pages)

        if (i + 1) % 10 == 0:
            print(f"  Generated {i+1}/{num_documents} documents...")

    print(f"\nDone. {num_documents} synthetic PDFs in data/synthetic_pdfs/")
    print("Update config.py PDF_FOLDER to 'data/synthetic_pdfs' to use them.")


if __name__ == "__main__":
    generate_dataset(90)