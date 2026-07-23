import os
from datetime import datetime

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

from .models import Note,Filierebts
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
    total_fg_points = 0
    total_fg_coef = 0
    rows = []
    output_dir = os.path.join(settings.BASE_DIR, "media", "bulletins")
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"bulletin_{etudiant.matricule}.pdf")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm
    )

    elements = []

    # =====================================================
    # EN-TÊTE ÉTAT
    # =====================================================
    header_table = Table([
    [
        Paragraph("""
            <para align="left">
            <b>MINISTÈRE DE L’ENSEIGNEMENT <br/>
            SUPÉRIEUR ET DE LA <br/>
            RECHERCHE SCIENTIFIQUE</b>
            </para>
        """, SMALL),

        Paragraph("""
            <para align="right">
            <b>RÉPUBLIQUE DE CÔTE D'IVOIRE</b><br/>
            Union - Discipline - Travail
            </para>
        """, SMALL)
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
    """, SMALL))

    # elements.append(Spacer(1, 10))
    # =====================================================
    # LOGO
    # =====================================================
    logo = get_image(
        os.path.join(settings.BASE_DIR, "core/static/logo.jpeg"),
        1.6 * cm,
        1.6 * cm,
        "LOGO"
    )

    cachet = get_image(
        os.path.join(settings.BASE_DIR, "core/static/cachet.png"),
        2.5 * cm,
        2.5 * cm,
        "CACHET"
    )

    # =====================================================
    # CADRE UNIVERSITÉ
    # =====================================================
    cadre_universite = Table(
        [[
            logo,
            Paragraph("""
                <b>UNIVERSITÉ INTERNATIONALE DE COCODY</b><br/><br/>
                 &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;BP Abidjan - Côte d'Ivoire<br/><br/>
                 &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;Tel: +225 07 78 63 74 00<br/><br/>
                 &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;site: www.uci-ci.com<br/><br/>
                 &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;Email: uicinfos@gmail.com
           """, SMALL)
        ]],
        colWidths=[0.5 * cm, 7.5 * cm],
        rowHeights=[3.7 * cm]

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
    ]))

    # =====================================================
    # CADRE ÉTUDIANT
    # =====================================================
    nom_classe = classe.nom

    if classe.filiere_bts:
         nom_classe = nom_classe.replace(f"{classe.filiere_bts.nom} ", "")

    date_lieu = (
    f"{etudiant.date_naissance.strftime('%d/%m/%Y')} à {etudiant.lieu_naissance}"
    if etudiant.date_naissance and etudiant.lieu_naissance
    else etudiant.date_naissance.strftime("%d/%m/%Y")
    if etudiant.date_naissance
    else ""
    )
       
    # cadre_etudiant = Table(
    #     [
    #         ["Nom & Prénom", f"{etudiant.nom} {etudiant.prenoms}"],
    #         ["Matricule", etudiant.matricule],
    #         ["Date et lieu de naiss", date_lieu],
    #         ["Sexe", getattr(etudiant, "sexe", "")],
    #         ["Classe", nom_classe],
    #         ["Filière", etudiant.filiere_bts.nom],
    #         ["Redoublant", "NON"],
    #     ],
    #     colWidths=[4.5 * cm, 5.5 * cm], etudiant.filiere_bts.nom.replace(" ", "<br/>", 1),
    # )
    cadre_etudiant = Table(
       [
        ["Nom & Prénom", f"{etudiant.nom} {etudiant.prenoms}"],
        ["Matricule", etudiant.matricule],
        ["Date et lieu de naiss", date_lieu],
        ["Sexe", getattr(etudiant, "sexe", "")],
        ["Classe", nom_classe],
        # ["Filière", etudiant.filiere_bts.nom],
        ["Filière", Paragraph(etudiant.filiere_bts.nom.replace(" ", "<br/>", 1),
        SMALL
       )],
        ["Redoublant", "NON"],
      ],
    colWidths=[3.5 * cm, 6.5 * cm],
)

    cadre_etudiant.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        # ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f7f7f7")),
    ]))

    # =====================================================
    # HEADER GLOBAL
    # =====================================================
    page_width = A4[0]
    usable_width = page_width - doc.leftMargin - doc.rightMargin

    header = Table(
        [[cadre_universite, cadre_etudiant]],
        colWidths=[
            usable_width * 0.45,
            usable_width * 0.55
        ]
    )

    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elements.append(header)
    elements.append(Spacer(1, 12))

    # =====================================================
    # TITRE
    # =====================================================
    # elements.append(Paragraph("BULLETIN DE NOTES - 1er SEMESTRE", TITLE))
    elements.append(
    Paragraph(f"BULLETIN DE NOTES - {semestre}er SEMESTRE", TITLE))
    elements.append(Spacer(1, 10))

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
      .select_related("matiere")
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
    formation_generale = 0
    rangs = {item["etudiant"]: i + 1 for i, item in enumerate(classement)}
    rang_general = format_rang(rangs.get(etudiant.id, "-"))

    # data = [[
    #     "MATIÈRE", "MOY", "COEF", "MOY*COEF",
    #     "MENTION","RANG", "MIN", "MOY", "MAX"
    # ]]
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

    fg_points = 0
    fg_coef = 0

    pro_points = 0
    pro_coef = 0

    tech_points = 0
    tech_coef = 0

    ang_points = 0
    ang_coef = 0

    fg_row = [
    "FORMATION GÉNÉRALE",
    formation_generale,
    "",
    "",
    "",
    "",
    "",
    "",
    ""
   ]

    rows.insert(6, fg_row)  # index 6 = 7ème ligne
    total_points = 0
    total_coef = 0
    notes_list = list(notes[:6])
    total_points_gnrl = 0
    total_coef_gnrl = 0
    total_points_tech = 0
    total_coef_tech = 0
    formation_generl_tech = 0
    moyenne_professionnelle_tech = 0
    formation_generl_points = 0
    formation_ang_expr = 0
    formation_ang_expr_points = 0
    formation_generale = 0
    formation_generl_points = 0
    moyenne_professionnelle_tech = 0
    formation_generl_tech = 0
  
    for n in notes_list:
        moy = safe_round(n.moyenne)
        coef = safe_round(n.matiere.coefficient)
        total_fg_points += moy * coef
        total_fg_coef += coef
    # formation_generale = (
    #     total_fg_points / total_fg_coef
    #     if total_fg_coef > 0
    #     else 0)

    # formation_generale = safe_round(formation_generale)

    for n in notes:
        m = n.matiere
        stats = stats_map.get(m.id, {})
        moy = safe_round(n.moyenne)
        coef = safe_round(m.coefficient)
        total_points += moy * coef
        total_coef += coef
        fg_points += moy * coef
        fg_coef += coef
        
        if getattr(m, "categorie", None) == "SCIENCE":
             tech_points += moy * coef
             tech_coef += coef
        elif getattr(m, "categorie", None) == "PRO":
             pro_points += moy * coef
             pro_coef += coef

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
            safe_round(stats.get("min_note")),
            safe_round(stats.get("avg_note")),
            safe_round(stats.get("max_note")),
        ])
    # formation general
    valeurs_fg = [
          float(ligne[1])
          for ligne in data[1:8]
          if isinstance(ligne[1], (int, float))
        ]

    formation_generale = safe_round(
           sum(valeurs_fg) / len(valeurs_fg) if valeurs_fg else 0
          )
         
    total_points_gnrl = 0
    for ligne in data[1:8]:
          if isinstance(ligne[1], (int, float)) and isinstance(ligne[2], (int, float)):
                 total_points_gnrl += ligne[1] * ligne[2]

    formation_generl_points = safe_round(total_points_gnrl)
        
        # Total des coefficients
    total_coef_gnrl = sum(
           ligne[2]
           for ligne in data[1:8]
           if isinstance(ligne[2], (int, float))
          )

    total_coef_gnrl = safe_round(total_coef_gnrl)
        #  "FORMATION TECHNIQUE et PROFESSIONNELLE",
    valeurs_prof = [
          float(ligne[1])
          for ligne in data[9:]
          if isinstance(ligne[1], (int, float))
        ]

    moyenne_professionnelle_tech = safe_round(
            sum(valeurs_prof) / len(valeurs_prof) if valeurs_prof else 0
          ) 
        
    total_points_tech = 0

    for ligne in data[8:]:
       if isinstance(ligne[1], (int, float)) and isinstance(ligne[2], (int, float)):
                  total_points_tech += ligne[1] * ligne[2]

    formation_generl_tech = safe_round(total_points_tech)
        # Total des coefficients
    total_coef_tech = sum(
            ligne[2]
            for ligne in data[8:]
            if isinstance(ligne[2], (int, float))
        )

    total_coef_tech = safe_round(total_coef_tech)

    formation_generale = safe_round(formation_generale)
    safe_round(moyenne_science)  # noqa: F821
    # moyenne_professionnelle = safe_round(moyenne_professionnelle)
    A4[0] - 2.4 * cm
    

    data.insert(8, [
         "FORMATION GENERALE",
          formation_generale, total_coef_gnrl, formation_generl_points, "", "", "", "", ""
       ])
 
    data.append([
        "FORMATION TECHNIQUE et PROFESSIONNELLE",
        moyenne_professionnelle_tech, total_coef_tech, formation_generl_tech, "", "", "", "", ""
        ])

    
    
    # table = Table(data)
    table = Table(data, colWidths=[
    6 * cm,   # MATIÈRE (plus large)
    1.5 * cm,
    1.5 * cm,
    2 * cm,
    2.5 * cm,
    1.5 * cm,
    1.5 * cm,
    1.5 * cm,
    1.2 * cm,   # MAX
  ])

    style = [
    ("GRID", (0,0), (-1,-1), 0.4, colors.black),
    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
    # ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
    ("ALIGN", (1,1), (-1,-1), "CENTER"),
    ("BACKGROUND", (0, 0), (-1, 1), colors.lightgrey),

    ("TOPPADDING", (0,0), (-1,-1), 2),
    ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ("LEFTPADDING", (0,0), (-1,-1), 3),
    ("RIGHTPADDING", (0,0), (-1,-1), 3),
    ("FONTSIZE", (0,0), (-1,-1), 7),
    ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 effet arrondi
    
    ("SPAN", (4, 8), (8, 8)),
     # Fusion dernière ligne FORMATION TECHNIQUE ET PROFESSIONNELLE
    ("SPAN", (4, len(data)-1), (8, len(data)-1)),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),

    # Fusion du titre MOYENNE DE LA CLASSE
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

    # Centrage
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
   
   ]

    for ligne in [8,len(data) - 1]:
        if ligne < len(data):
            style.append(
                 ("BACKGROUND", (0,ligne), (-1,ligne), colors.lightgrey) )
            
    table.setStyle(TableStyle(style)) 
    elements.append(table)
    elements.append(Spacer(1, 10))
    # =====================================================
    # RECAP
    # =====================================================
    # moyenne_generale = calcul_moyenne_etudiant(etudiant)
    # Moyennes des deux semestres
    # moyenne_s1 = calcul_moyenne_etudiant(etudiant, 1)
    # moyenne_s2 = calcul_moyenne_etudiant(etudiant, 2)
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
        f"Avertissement "
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
    # ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("ALIGN", (0, 0), (-1, 0), "CENTER"),

    # CONTENU
    # ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
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
    # elements.append(observation)
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

#     visa_table = Table([
#     [
#         Paragraph("<b>Le Chef d’établissement</b><br/><br/><br/><br/>", SMALL),
#         Paragraph("<b>OBSERVATION DU CONSEIL DE CLASSE</b><br/><br/><br/><br/>", SMALL),
#     ]
#    ], colWidths=[6 * cm, 8 * cm])
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
        5 * cm,
        5 * cm,
        4 * cm,
        5 * cm,
    ],
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

    elements.append(visa_table)
    # =====================================================
    # FOOTER
    # =====================================================
    elements.append(Spacer(1, 8))
    # elements.append(Paragraph(
    #     f"Edité le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    #     SMALL
    # ))

    doc.build(elements)

    return file_path