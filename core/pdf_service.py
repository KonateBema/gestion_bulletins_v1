import os
import io
from datetime import datetime
from itertools import groupby

from django.conf import settings
from django.db.models import Min, Max, Avg
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image as RLImage
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import Note
from .services import calcul_moyenne_etudiant, mention
from reportlab.platypus import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class RoundedBackground(Flowable):
    def __init__(self, width, height, radius=8, fillColor=colors.whitesmoke, strokeColor=colors.black):
        super().__init__()
        self.width = width
        self.height = height
        self.radius = radius
        self.fillColor = fillColor
        self.strokeColor = strokeColor

    def draw(self):
        self.canv.setFillColor(self.fillColor)
        self.canv.setStrokeColor(self.strokeColor)

        self.canv.roundRect(
            0, 0,
            self.width,
            self.height,
            self.radius,
            stroke=1,
            fill=1
        )

# =====================================================
# STYLES
# =====================================================
styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "TITLE",
    parent=styles["Heading1"],
    alignment=1,
    fontSize=15,
    fontName="Courier-Bold",
    textColor=colors.HexColor("#b30000"),
)

SMALL = ParagraphStyle(
    "SMALL",
    parent=styles["Normal"],
    fontSize=9,
    leading=11,
    fontName="Courier",
)

# =====================================================
# UTILS
# =====================================================
def get_image(path, width, height, fallback):
    if os.path.exists(path):
        return RLImage(path, width=width, height=height)
    return Paragraph(fallback, SMALL)

def safe_round(value):
    try:
        return round(float(value), 2)
    except:
        return 0

def format_rang(r):
    if r == 1:
        return "1er"
    if r == 2:
        return "2e"
    if r == 3:
        return "3e"
    return f"{r}e" if r != "-" else "-"


def generate_qr_image(etudiant, size=2.2 * cm):
    """
    Génère un QR code contenant les informations de l'étudiant
    et retourne un Flowable RLImage prêt à être inséré dans le PDF.
    """
    date_naissance = (
        etudiant.date_naissance.strftime("%d/%m/%Y")
        if getattr(etudiant, "date_naissance", None)
        else ""
    )

    buffer = io.BytesIO()
    
    buffer.seek(0)

    return RLImage(buffer, width=size, height=size)


science_points = 0
science_coef = 0
moyenne_professionnelle=0
professionnel_points = 0
professionnel_coef = 0
moyenne_science =0
# =====================================================
# GENERATION PDF
# =====================================================
def generate_bulletin_pdf(etudiant, classe,semestre):
    output_dir = os.path.join(settings.BASE_DIR, "media", "bulletins")
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"bulletin_{etudiant.matricule}.pdf")

    doc = SimpleDocTemplate(
       file_path,
       pagesize=A4,
       leftMargin=0.8 * cm,
       rightMargin=0.8 * cm,
       topMargin=0.7 * cm,
       # Marge basse agrandie pour réserver la place du pied de page fixe
       # (dessiné directement sur le canvas, hors du flux des "elements")
       bottomMargin=2.6 * cm
    )

    elements = []

    # =====================================================
    # EN-TÊTE ÉTAT
    # =====================================================
    from reportlab.lib.enums import TA_LEFT
    style_ministere = ParagraphStyle(
    "style_ministere",
    parent=SMALL,
    fontName="Helvetica-Bold",
    fontSize=6,
    leading=7,
    alignment=TA_LEFT,
    spaceAfter=0,
    spaceBefore=0,
   )
    
    header_table = Table([
    [
        Paragraph("""
            MINISTÈRE DE L’ENSEIGNEMENT<br/>
             SUPÉRIEUR ET DE LA<br/>
            RECHERCHE SCIENTIFIQUE
        """, style_ministere),

        Paragraph("""
            <para align="right">
            <b>RÉPUBLIQUE DE CÔTE D'IVOIRE</b><br/>
            Union - Discipline - Travail<br/>
           
            </para>
        """, style_ministere)
    ]
    ], colWidths=[9*cm, 9*cm])

    header_table.setStyle(TableStyle([
         ("VALIGN", (0, 0), (-1, -1), "TOP"),
         ("LEFTPADDING", (0, 0), (-1, -1), 0),
         ("RIGHTPADDING", (0, 0), (-1, -1), 0),
         ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
         ("TOPPADDING", (0, 0), (-1, -1), 0),
       ]))

    header_table.setStyle(TableStyle([
       ('VALIGN', (0, 0), (-1, -1), 'TOP'),
       ('LEFTPADDING', (0, 0), (-1, -1), 0),
       ('TOPPADDING', (0, 0), (-1, -1), 0),
   ]))

    elements.append(header_table)

    elements.append(Paragraph("""
        <para align="right">
         <b>ANNÉE ACADÉMIQUE : 2025 - 2026</b>
        </para>
    """, style_ministere))

    elements.append(Spacer(1, 8))
    # =====================================================
    # LOGO
    # =====================================================
    logo = get_image(
        os.path.join(settings.BASE_DIR, "core/static/logo.jpeg"),
        1.6 * cm,
        2.5 * cm,
        "LOGO"
    )

    cachet = get_image(
        os.path.join(settings.BASE_DIR, "core/static/cachet.png"),
        2.5 * cm,
        2.5 * cm,
        "CACHET"
    )
    style_universite = ParagraphStyle(
    "style_universite",
    parent=SMALL,
    fontSize=9,
    leading=11,
   )
   

    # =====================================================
    # CADRE UNIVERSITÉ 
    # =====================================================
    cadre_universite = Table(
        [[
            logo,
            Paragraph("""
                <b>UNIVERSITÉ INTER. DE COCODY</b><br/>
                BP Abidjan - Côte d'Ivoire<br/>
                Tel: +225 07 78 63 74 00<br/>
                Tél. fixe : 27 XX XX XX<br/>
                site: www.uci-ci.com<br/>
                Email: uicinfos@gmail.com
           """, style_universite)
        ]],
        # colWidths=[0.5 * cm, 7.5 * cm],
        colWidths=[1.7 * cm, 6.5 * cm],
        rowHeights=[3.2 * cm]   # hauteur fixe  # hauteur alignée avec le cadre étudiant (8 lignes x 0.45cm)
    )
    

    cadre_universite.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 effet arrondi
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        # ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),

          # Décaler uniquement le texte vers la droite
        ("LEFTPADDING", (1, 0), (1, 0), 15),

         # Padding du logo
        ("LEFTPADDING", (0, 0), (0, 0), 5),
        ("RIGHTPADDING", (0, 0), (0, 0), 5),
        
         # réduire les marges internes
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),

        ("LEFTPADDING", (1,0), (1,0), 8),

        ("LEFTPADDING", (0,0), (0,0), 3),
        ("RIGHTPADDING", (0,0), (0,0), 3),
    ]))

    # =====================================================
    # CADRE ÉTUDIANT
    # =====================================================
  
    
    nom_classe = classe.nom.strip()
    if classe.filiere_bts:
        nom_filiere = classe.filiere_bts.nom.strip()
    # Supprimer le nom de la filière uniquement au début
        if nom_classe.startswith(nom_filiere):
             nom_classe = nom_classe[len(nom_filiere):].strip()

    date_lieu = (
    f"{etudiant.date_naissance.strftime('%d/%m/%Y')} à {etudiant.lieu_naissance}"
    if etudiant.date_naissance and etudiant.lieu_naissance
    else etudiant.date_naissance.strftime("%d/%m/%Y")
    if etudiant.date_naissance
    else ""
    )
       
    cadre_etudiant = Table(
       [
        ["Nom & Prénom", f"{etudiant.nom} {etudiant.prenoms}"],
        ["Matricule", etudiant.matricule],
        ["Date et lieu de naiss", date_lieu],
        ["Sexe", getattr(etudiant, "sexe", "")],
        ["Classe", nom_classe],
        ["Filière",  etudiant.filiere_bts.nom[:23]],
        ["Redoublant", "NON"],
      ],
    colWidths=[3.2 * cm, 7 * cm],
    rowHeights=[0.45*cm]*7   # hauteur de chaque ligne
)

    cadre_etudiant.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        # ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f7f7f7")),
         # réduire hauteur interne
       ("TOPPADDING", (0,0), (-1,-1), 1),
       ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))

    # =====================================================

    # =====================================================
    # HEADER GLOBAL
    # =====================================================
    page_width = A4[0]
    usable_width = page_width - doc.leftMargin - doc.rightMargin

    # Pas de colWidths imposé ici : chaque cadre (université / étudiant / QR)
    # a déjà sa propre largeur fixe. Les imposer une 2e fois au niveau du
    # tableau parent provoquait un dépassement de la largeur de page (donc
    # un chevauchement visuel) car la somme des largeurs internes dépassait
    # la largeur utile de la page. On laisse ReportLab dimensionner les
    # colonnes d'après le contenu, et on espace juste un peu les cadres.
    # Les 3 cadres ont maintenant tous une hauteur totale de 3.6cm, ce qui
    # aligne parfaitement leurs bords supérieur et inférieur.
    
    header = Table(
        [[cadre_universite, cadre_etudiant]]
    )

    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
        ("RIGHTPADDING", (2, 0), (2, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    elements.append(header)
    # elements.append(Spacer(1, 12))

    # =====================================================
    # TITRE
    # =====================================================
    if semestre == 1:
       titre_semestre = "1er"
    else:
       titre_semestre = "2ème"
    
    elements.append(
    Paragraph(f"BULLETIN DE NOTES - {titre_semestre} SEMESTRE", TITLE))
    # elements.append(Spacer(1, 10))

    # =====================================================
    # NOTES
    # =====================================================

    if str(semestre).startswith("S"):
          semestre_value = str(semestre)
    else:
          semestre_value = f"S{semestre}"

    notes = (
        Note.objects.filter(
        etudiant=etudiant,
        semestre=semestre_value
      )
      .select_related("matiere", "matiere__grande_unite")
      .order_by("matiere__grande_unite__ordre", "matiere__code")
      )

    stats_map = {
        s["matiere"]: s
        for s in Note.objects.filter(etudiant__classe=classe, semestre=semestre_value)
        .values("matiere")
        .annotate(
            min_note=Min("moyenne"),
            max_note=Max("moyenne"),
            avg_note=Avg("moyenne"),
        )
    }

    classement = (
        Note.objects.filter(etudiant__classe=classe, semestre=semestre_value)
        .values("etudiant")
        .annotate(moy=Avg("moyenne"))
        .order_by("-moy")
    )
    rangs = {item["etudiant"]: i + 1 for i, item in enumerate(classement)}
    rang_general = format_rang(rangs.get(etudiant.id, "-"))

    data = [
    [
        "MATIÈRE",
        "MOY",
        "COEF",
        "MOY*COEF",
        "MENTION",
        "RANG",
        "MOYENNE DE LA CLASSE",
        "",
        ""
    ],
    [
        "",
        "",
        "",
        "",
        "",
        "",
        "MIN",
        "MOY",
        "MAX"
    ]]

    total_points = 0
    total_coef = 0

    # =====================================================
    # LIGNES DE NOTES + SOUS-TOTAL PAR GRANDE UNITÉ
    # (les notes sont déjà triées par matiere__grande_unite__ordre)
    # =====================================================
    subtotal_rows = []

    for grande_unite, groupe in groupby(notes, key=lambda n: n.matiere.grande_unite):
        groupe = list(groupe)
        gu_points = 0
        gu_coef = 0

        for n in groupe:
            m = n.matiere
            stats = stats_map.get(m.id, {})
            moy = safe_round(n.moyenne)
            coef = safe_round(m.coefficient)

            total_points += moy * coef
            total_coef += coef
            gu_points += moy * coef
            gu_coef += coef

            rang_matiere = (
                Note.objects.filter(
                    etudiant__classe=classe,
                    matiere=m,
                    moyenne__gt=n.moyenne
                )
                .count() + 1
            )

            data.append([
                m.libelle,
                moy,
                coef,
                safe_round(moy * coef),
                mention(moy),
                format_rang(rang_matiere),
                # getattr(m, "professeur", "") or "-",
                safe_round(stats.get("min_note")),
                safe_round(stats.get("avg_note")),
                safe_round(stats.get("max_note")),
            ])

        gu_moyenne = safe_round(gu_points / gu_coef) if gu_coef else 0
        gu_libelle = grande_unite.libelle.upper() if grande_unite else "AUTRES MATIERES"

        subtotal_rows.append(len(data))
        data.append([
            gu_libelle,
            gu_moyenne, gu_coef, safe_round(gu_points), "", "", "","", ""
        ])

    # table = Table(data)
    table = Table(data, colWidths=[
    6.3 * cm,   # MATIÈRE (plus large)
    1.5 * cm,
    2 * cm,
    1.7 * cm,
    2 * cm,
    1.3 * cm,
    1.3 * cm,
    1.3 * cm,
    1.3 * cm,   # MAX
  ])

    style = [
    ("GRID", (0,0), (-1,-1), 0.4, colors.black),
    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
    ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
    ("ALIGN", (1,1), (-1,-1), "CENTER"),
    ("BACKGROUND", (0, 0), (-1, 1), colors.lightgrey),

    ("TOPPADDING", (0,0), (-1,-1), 2),
    ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ("LEFTPADDING", (0,0), (-1,-1), 3),
    ("RIGHTPADDING", (0,0), (-1,-1), 3),
    ("FONTSIZE", (0,0), (-1,-1), 7),
    ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 effet arrondi

    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),

    # Fusion du titre MOYENNE DE LA CLASSE
    # ("SPAN", (7, 0), (9, 0)),
    ("SPAN", (6, 0), (8, 0)),

    # Fusion MATIÈRE sur les deux lignes
    ("SPAN", (0, 0), (0, 1)),

    # Fusion MOY sur les deux lignes
    ("SPAN", (1, 0), (1, 1)),

    # Fusion COEF sur les deux lignes
    ("SPAN", (2, 0), (2, 1)),

    # Fusion MOY*COEF sur les deux lignes
    ("SPAN", (3, 0), (3, 1)),

    # Fusion MENTION sur les deux lignes
    ("SPAN", (4, 0), (4, 1)),

    # Fusion RANG sur les deux lignes
    ("SPAN", (5, 0), (5, 1)),

    # Fusion PROFESSEUR sur les deux lignes
    # ("SPAN", (6, 0), (6, 1)),

    # Centrage
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

    # Matière alignée à gauche (hors en-tête)
    ("ALIGN", (0, 2), (0, -1), "LEFT"),

     # Réduction hauteur des lignes
    ("TOPPADDING", (0,0), (-1,-1), 0.5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 0.5),
     # Réduction espace horizontal
    ("LEFTPADDING", (0,0), (-1,-1), 1),
    ("RIGHTPADDING", (0,0), (-1,-1), 1),

   ]

    # Fusion + fond grisé pour chaque ligne de sous-total (une par grande unité)
    for ligne in subtotal_rows:
        # style.append(("SPAN", (4, ligne), (9, ligne)))
        style.append(("SPAN", (4, ligne), (8, ligne)))
        style.append(("BACKGROUND", (0, ligne), (-1, ligne), colors.lightgrey))
         # Texte noir
        style.append(( "TEXTCOLOR",(0, ligne),(0, ligne), colors.black))
        # Texte en gras
        style.append(("FONTNAME", (0, ligne),(0, ligne),"Courier-Bold"))

    table.setStyle(TableStyle(style)) 
    elements.append(table)
    elements.append(Spacer(1, 10))
    # =====================================================
    # RECAP
    # =====================================================
    moyenne_s1 = calcul_moyenne_etudiant(etudiant, "S1")
    moyenne_s2 = calcul_moyenne_etudiant(etudiant, "S2")
    
    classement_s1 = (
    Note.objects.filter(
        etudiant__classe=classe,
        semestre="S1"
    )
    .values("etudiant")
    .annotate(moy=Avg("moyenne"))
    .order_by("-moy")
   )

    rangs_s1 = {
       item["etudiant"]: i + 1
       for i, item in enumerate(classement_s1)
       }

    rang_s1 = format_rang(
             rangs_s1.get(etudiant.id, "-")
      )
    
    classement_s2 = (
    Note.objects.filter(
        etudiant__classe=classe,
        semestre="S2"
    )
    .values("etudiant")
    .annotate(moy=Avg("moyenne"))
    .order_by("-moy")
    )

    rangs_s2 = {
        item["etudiant"]: i + 1
        for i, item in enumerate(classement_s2)
      }

    rang_s2 = format_rang(
      rangs_s2.get(etudiant.id, "-")
    )
    
    if str(semestre) in ["1", "S1"]:

        rappel_semestre = Paragraph(
        f"""
        <b>1er Semestre</b><br/>
        Moyenne : {safe_round(moyenne_s1)}/20<br/>
        Rang : {rang_s1}
        """,
         SMALL
       )

    else:

       rappel_semestre = Paragraph(
         f"""
         <b>1er Semestre</b><br/>
         Moyenne : {safe_round(moyenne_s1)}/20<br/>
         Rang : {rang_s1}<br/><br/>

         <b>2ème Semestre</b><br/>
         Moyenne : {safe_round(moyenne_s2)}/20<br/>
         Rang : {rang_s2}
         """,
         SMALL
    )
    
    moyenne_generale = calcul_moyenne_etudiant(etudiant,semestre)

    recap_data = [
       ["RAPPEL SEMESTRE", "TRAVAIL", "CONDUITE", "CONSEIL DE CLASSE"],

       [
        rappel_semestre ,

        # TRAVAIL
        f"Total points : {safe_round(total_points)}\n"
        f"Total coef : {safe_round(total_coef)}\n"
        f"Moyenne : {safe_round(moyenne_generale)} / 20\n"
        f"Rang : {rang_general}",

        # CONDUITE (discipline)
        f"Absences totales : 0.0\n"
        f"Absences justifiées : 0.0\n"
        f"Consignes : 0.0\n"
        f"Exclusions : 0.0",

        # CONSEIL DE CLASSE
        f"Note conduite \n"
        f"Blâme conduite\n"
        f"Félicitations\n"
        f"Tableau d'honneur\n"
        f"Encouragement \n"
        # f"Avertissement "
     ],
   ]

    recap = Table(
     recap_data,
      colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 5 * cm]
    )
    
    recap.setStyle(TableStyle([
    # Bordures globales
    ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),

    # HEADER
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("ALIGN", (0, 0), (-1, 0), "CENTER"),

    # CONTENU
    ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
    ("FONTSIZE", (0, 1), (-1, -1), 8),
    ("VALIGN", (0, 1), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 1), (-1, -1), 6),
    ("RIGHTPADDING", (0, 1), (-1, -1), 6),
    ("TOPPADDING", (0, 1), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
    ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 effet arrondi
  ]))

    elements.append(recap)
    elements.append(Spacer(1, 8))
    moyenne_annuelle = calcul_moyenne_etudiant(etudiant)

    classement_annuel = (
      Note.objects.filter(etudiant__classe=classe)
       .values("etudiant")
       .annotate(moy=Avg("moyenne"))
      .order_by("-moy")
    )

    rangs_annuels = {
      item["etudiant"]: i + 1
      for i, item in enumerate(classement_annuel)
     }

    rang_annuel = format_rang(rangs_annuels.get(etudiant.id, "-"))

    HEADER = ParagraphStyle(
      "HEADER",
        parent=SMALL,
        alignment=1,               # Centré
        fontName="Courier-Bold",
        textColor=colors.white,
        fontSize=9,
      )
    
    visa_table = Table(
    [
        [
            Paragraph("<b>ANNUEL</b>", HEADER),
            Paragraph("<b>OBSERVATION DU CONSEIL DE CLASSE</b>", HEADER),
            Paragraph("<b>DÉCISION FINALE</b>", HEADER),
            Paragraph("<b>VISA DU CHEF D'ÉTABLISSEMENT</b>", HEADER),
        ],
        [
            Paragraph(
                f"""
                 <b>Moy annuelle :</b> {moyenne_annuelle}/20<br/>
                 <b>Rang annuel :</b> {rang_annuel}<br/>
                """,
                SMALL,
            ),
            Paragraph(
                """
                """,
                SMALL,
            ),
            Paragraph(
                """
                ☐ Passe<br/>
                ☐ Redouble<br/>
                ☐ Exclu(e)<br/>
                """,
                SMALL,
            ),
            Paragraph(
                """
                """,
                SMALL,
            ),
        ],
    ],
    colWidths=[
        4.5 * cm,
        5 * cm,
        3.5 * cm,
        6 * cm,
    ],
    rowHeights=[
        1 * cm,   # hauteur de l'en-tête
        3 * cm,   # hauteur du contenu
    ]
  )

    visa_table.setStyle(TableStyle([
    # bordure principale plus élégante
    ("BOX", (0, 0), (-1, -1), 1, colors.black),
    # grille interne discrète (si plusieurs cases)
    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("FONTNAME", (0, 1), (-1, -1), "Courier"),
    ("FONTSIZE", (0, 1), (-1, -1), 8),

    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),

    ("TOPPADDING", (0, 1), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 5),

    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),

   ]))
    
    FOOTER = ParagraphStyle(
    "FOOTER",
    parent=SMALL,
    fontSize=6,
    leading=7.5,
    alignment=1,
    textColor=colors.grey,
    fontName="Helvetica"
)

    elements.append(visa_table)
    elements.append(Spacer(1, 10))

    # =====================================================
    # FOOTER PROFESSIONNEL — FIXÉ EN BAS DE CHAQUE PAGE
    # =====================================================
    # On ne met plus le footer dans "elements" (il suivrait le flux du
    # contenu et sa position varierait selon la longueur du bulletin).
    # On le dessine directement sur le canvas via onFirstPage/onLaterPages,
    # à une position fixe proche du bas de la page. La "bottomMargin" du
    # doc a été agrandie ci-dessus pour lui laisser la place nécessaire.

    footer_text = (
        """
       <b>UNIVERSITÉ INTERNATIONALE DE COCODY</b><br/>
        Arrêté n°487/MESRS/DGSE du 29/12/2015<br/>
        Siège Social : Cocody 2 Plateaux, 7ème Tranche, non loin du Café de Versailles<br/>
        édité le %s
        """
        % datetime.now().strftime("%d/%m/%Y à %H:%M")
    )

    footer_width = 18 * cm
    footer_x = (page_width - footer_width) / 2

    def draw_footer(canvas, pdf_doc):
        canvas.saveState()

        footer_paragraph = Paragraph(footer_text, FOOTER)
        # largeur dispo, hauteur "infinie" pour laisser le paragraphe
        # calculer sa propre hauteur réelle
        w, h = footer_paragraph.wrap(footer_width, 10 * cm)

        # position fixe : collé au bas de la page (dans la bottomMargin
        # réservée), quel que soit le contenu qui précède sur la page
        # footer_y = 0.4 * cm
        footer_y = 0.5 * cm

        # ligne de séparation au-dessus du texte
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(0.5)
        canvas.line(
            footer_x, footer_y + h + 4,
            footer_x + footer_width, footer_y + h + 4
        )

        footer_paragraph.drawOn(canvas, footer_x, footer_y)
        canvas.restoreState()

    doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)

    return file_path