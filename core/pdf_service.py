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
from reportlab.lib import colors
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

    elements.append(Spacer(1, 10))
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
                BP Abidjan - Côte d'Ivoire<br/><br/>
                Tel: +225 07 78 63 74 00<br/><br/>
                Fix: 2722550041 <br/><br/>
                Email: contact@uic.ci
                
            """, SMALL)
        ]],
        colWidths=[2.5 * cm, 7.5 * cm],
        rowHeights=[3.7 * cm]
    )

    cadre_universite.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 effet arrondi
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    # =====================================================
    # CADRE ÉTUDIANT
    # =====================================================
    date_lieu = ""

    if etudiant.date_naissance:
        date_lieu += etudiant.date_naissance.strftime("%d/%m/%Y")

    if getattr(etudiant, "lieu_naissance", ""):
        date_lieu += f" à {etudiant.lieu_naissance}"
       
    cadre_etudiant = Table(
        [
            ["Nom & Prénom", f"{etudiant.nom} {etudiant.prenoms}"],
            ["Matricule", etudiant.matricule],
            ["Date de naissance", date_lieu],
            ["Sexe", getattr(etudiant, "sexe", "")],
            ["Classe", classe.salle.nom],
            ["Filière", etudiant.filiere_bts.nom],
            ["Redoublant", "NON"],
        ],
        colWidths=[3 * cm, 4.5 * cm]
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
            usable_width * 0.58,
            usable_width * 0.42
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

    data = [[
        "MATIÈRE", "MOY", "COEF", "MOY*COEF",
        "MENTION","RANG", "MIN", "MOY", "MAX"
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
             
        # if "technique d'expression" in m.libelle.lower():
        #     ang_points += moy * coef
        #     ang_coef += coef
            
        # categorie = n.matiere.categorie.nom if n.matiere.categorie else ""   
        
 
        
        # if categorie == "COMPTABILITE & DOCS":
        #     pro_points += moy * coef
        #     pro_coef += coef
            
        # moyenne_professionnelle = safe_round( pro_points / pro_coef if pro_coef else 0)
            

        # valeurs = [
        #      float(ligne[1])
        #       for ligne in data[:5]
        #       if isinstance(ligne[1], (int, float))
        #    ]

        # formation_ang_expr = safe_round(
        #   sum(valeurs) / len(valeurs) if valeurs else 0
        #  )
    
        # moyenne_professionnelle_tech = safe_round(tech_points / tech_coef if tech_coef else 0)
        
        # total_points_ang = 0

        # for ligne in data[:4]:
        #      if isinstance(ligne[1], (int, float)) and isinstance(ligne[2], (int, float)):
        #          total_points_ang += ligne[1] * ligne[2]

        # formation_ang_expr_points = safe_round(total_points_ang)
        # formation general
        valeurs_fg = [
          float(ligne[1])
          for ligne in data[:10]
          if isinstance(ligne[1], (int, float))
        ]

        formation_generale = safe_round(
           sum(valeurs_fg) / len(valeurs_fg) if valeurs_fg else 0
          )
         
        total_points_gnrl = 0

        for ligne in data[1:10]:
             if isinstance(ligne[1], (int, float)) and isinstance(ligne[2], (int, float)):
                 total_points_gnrl += ligne[1] * ligne[2]

        formation_generl_points = safe_round(total_points_gnrl)
        
        
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

        for ligne in data[7:]:
             if isinstance(ligne[1], (int, float)) and isinstance(ligne[2], (int, float)):
                  total_points_tech += ligne[1] * ligne[2]

        formation_generl_tech = safe_round(total_points_tech)
        
        # formation_ang_expr = safe_round(ang_points / ang_coef if ang_coef else 0)

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

    

    formation_generale = safe_round(formation_generale)
    safe_round(moyenne_science)  # noqa: F821
    # moyenne_professionnelle = safe_round(moyenne_professionnelle)
    A4[0] - 2.4 * cm
    
   
    # data.insert(4, [
    #      "//////////////////////",
    #       "", "", "", "", "", "", "", ""
    #      ])
    # data.insert(5, [
    #      "ANGLAIS ET TECHNIQUE D'EXPRESSION",
    #       formation_ang_expr, "", formation_ang_expr_points, "", "", "", "", ""
    #      ])
    # data.insert(9, [
    #      "//////////////////////",
    #       "", "", "", "", "", "", "", ""
    #      ])
    data.insert(10, [
         "FORMATION GENERALE",
          formation_generale, "", formation_generl_points, "", "", "", "", ""
       ])
    # data.insert(10, [
    #     "FORMATION PROFESSIONNELLE",
    #     moyenne_professionnelle, "", "", "", "", "", "", ""
    # ])
    data.append([
        "FORMATION TECHNIQUE et PROFESSIONNELLE",
        moyenne_professionnelle_tech, "", formation_generl_tech, "", "", "", "", ""
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

    ("TOPPADDING", (0,0), (-1,-1), 2),
    ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ("LEFTPADDING", (0,0), (-1,-1), 3),
    ("RIGHTPADDING", (0,0), (-1,-1), 3),
    ("FONTSIZE", (0,0), (-1,-1), 7),
    ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 effet arrondi
    ("SPAN", (4,10), (8,10)),
     # Fusion dernière ligne FORMATION TECHNIQUE ET PROFESSIONNELLE
    ("SPAN", (4, len(data)-1), (8, len(data)-1)),

    
   

    
   ]
    
    for ligne in [10,len(data) - 1]:
        if ligne < len(data):
            style.append(
                 ("BACKGROUND", (0,ligne), (-1,ligne), colors.lightgrey) )
            
    table.setStyle(TableStyle(style)) 
          
    elements.append(table)
    elements.append(Spacer(1, 10))

    # =====================================================
    # RECAP
    # =====================================================
    moyenne_generale = calcul_moyenne_etudiant(etudiant)

    recap_data = [
       ["RAPPEL SEMESTRE", "TRAVAIL", "CONDUITE", "CONSEIL DE CLASSE"],

       [
        "",

        # TRAVAIL
        f"Total points : {safe_round(total_points)}\n"
        f"Total coef : {safe_round(total_coef)}\n"
        f"Moyenne : {safe_round(moyenne_generale)} / 20\n"
        f"Rang : {rang_general}",

        # CONDUITE (discipline)
        f"Absences totales : ...\n"
        f"Absences justifiées : ...\n"
        f"Consignes : ...\n"
        f"Exclusions : ...",

        # CONSEIL DE CLASSE
        f"Note conduite : ...\n"
        f"Blâme : ...\n"
        f"Félicitations : ...\n"
        f"Tableau d'honneur : ...\n"
        f"Encouragement : ...\n"
        f"Avertissement : ..."
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
    # observation = Paragraph(
    # """
    # <br/>
    # <b>OBSERVATION DU CONSEIL DE CLASSE :</b><br/><br/>
    # L’étudiant a montré un travail satisfaisant au cours de ce semestre.
    # Le conseil encourage l’étudiant à poursuivre ses efforts pour améliorer ses résultats
    # et maintenir une discipline exemplaire.
    # """,
    # SMALL
    # )

    # elements.append(observation)
    elements.append(Spacer(1, 8))

    visa_table = Table([
    [
        Paragraph("<b>Le Chef d’établissement</b><br/><br/><br/><br/>Signature & Cachet", SMALL),
        Paragraph("<b>OBSERVATION DU CONSEIL DE CLASSE</b><br/><br/><br/><br/>Signature", SMALL),
    ]
   ], colWidths=[6 * cm, 8 * cm])



    visa_table.setStyle(TableStyle([
    # bordure principale plus élégante
    ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#222222")),

    # grille interne discrète (si plusieurs cases)
    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#999999")),

    # fond léger (style administratif)
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F7F7")),

    # alignement propre
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

    # padding équilibré (important pour effet “carte”)
    ("TOPPADDING", (0, 0), (-1, -1), 15),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),

    # typo plus propre
    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
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