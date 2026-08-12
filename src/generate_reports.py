"""
Génère 2 rapports financiers PDF réalistes (ACME Corp 2023 & 2024).
Synthétiques mais crédibles : permet une évaluation RIGOUREUSE du RAG (vérité
terrain connue). Le pipeline fonctionne à l'identique sur de vrais PDF publics
qu'on déposerait dans data/.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

DATA = Path(__file__).resolve().parent.parent / "data"
PETROL = colors.HexColor("#137A8B")

# Données financières (M€) — vérité terrain
FIN = {
    2023: dict(ca=120.0, cout=72.0, marge_brute=48.0, charges=30.0, rex=18.0,
               net=12.5, effectifs=720, treso=21.0, dette=45.0, dividende=4.0,
               rd=9.0, eu=60, am=30, asie=10),
    2024: dict(ca=145.0, cout=82.0, marge_brute=63.0, charges=36.0, rex=27.0,
               net=19.0, effectifs=850, treso=34.0, dette=40.0, dividende=6.0,
               rd=12.0, eu=58, am=31, asie=11),
}


def build(year: int) -> None:
    f = FIN[year]
    marge_nette = 100 * f["net"] / f["ca"]
    marge_brute_pct = 100 * f["marge_brute"] / f["ca"]
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=PETROL)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=PETROL)
    body = styles["BodyText"]

    doc = SimpleDocTemplate(str(DATA / f"ACME_rapport_annuel_{year}.pdf"),
                            pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    e = []
    e.append(Paragraph(f"ACME Corp — Rapport annuel {year}", h1))
    e.append(Paragraph(f"Document de référence financier · exercice clos le 31 décembre {year}", body))
    e.append(Spacer(1, 0.5 * cm))

    e.append(Paragraph("Faits marquants", h2))
    e.append(Paragraph(
        f"En {year}, ACME Corp a réalisé un chiffre d'affaires de {f['ca']:.1f} millions d'euros, "
        f"pour un résultat net de {f['net']:.1f} millions d'euros, soit une marge nette de "
        f"{marge_nette:.1f} %. La société a compté {f['effectifs']} employés en fin d'exercice. "
        f"Le conseil d'administration propose un dividende de {f['dividende']:.1f} millions d'euros.", body))
    e.append(Spacer(1, 0.3 * cm))

    e.append(Paragraph("Compte de résultat (en millions d'euros)", h2))
    rows = [["Poste", f"{year}"],
            ["Chiffre d'affaires", f"{f['ca']:.1f}"],
            ["Coût des ventes", f"{f['cout']:.1f}"],
            ["Marge brute", f"{f['marge_brute']:.1f}"],
            ["Charges d'exploitation", f"{f['charges']:.1f}"],
            ["Résultat d'exploitation", f"{f['rex']:.1f}"],
            ["Résultat net", f"{f['net']:.1f}"]]
    t = Table(rows, colWidths=[9 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PETROL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT")]))
    e.append(t)
    e.append(Spacer(1, 0.4 * cm))

    e.append(Paragraph("Situation financière", h2))
    e.append(Paragraph(
        f"La trésorerie disponible s'élève à {f['treso']:.1f} millions d'euros au 31 décembre {year}, "
        f"tandis que l'endettement financier net atteint {f['dette']:.1f} millions d'euros. "
        f"La marge brute ressort à {marge_brute_pct:.1f} % du chiffre d'affaires. "
        f"Les dépenses de recherche et développement représentent {f['rd']:.1f} millions d'euros.", body))
    e.append(Spacer(1, 0.3 * cm))

    e.append(Paragraph("Répartition géographique du chiffre d'affaires", h2))
    e.append(Paragraph(
        f"Europe : {f['eu']} % · Amériques : {f['am']} % · Asie-Pacifique : {f['asie']} %. "
        f"L'Europe demeure le premier marché du groupe.", body))

    doc.build(e)
    print(f"  ACME_rapport_annuel_{year}.pdf — CA {f['ca']:.0f} M€, marge nette {marge_nette:.1f} %")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    for y in (2023, 2024):
        build(y)
    print("2 rapports PDF générés dans data/")


if __name__ == "__main__":
    main()
