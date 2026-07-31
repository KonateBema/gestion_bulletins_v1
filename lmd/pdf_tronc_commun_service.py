from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os
from lmd.models import EtudiantLMD
from .models import  UE, NoteLMD
from reportlab.platypus import HRFlowable
from reportlab.pdfgen import canvas
from .models import SaisieNoteLMD
from .services import (
    calcul_moyenne_etudiant,
)
# =========================================================
# STYLES
# =========================================================
def safe_date(date):
    return date.strftime("%d/%m/%Y") if date else "Non renseignée"
styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "TITLE",
    parent=styles["Normal"],
    fontSize=14,
    leading=16,
    alignment=1,
    spaceAfter=10,
    textColor=colors.HexColor("#1a1a1a"),
    fontName="Courier-Bold",
)

SMALL = ParagraphStyle(
    "SMALL",
    parent=styles["Normal"],
    fontSize=9,
    leading=11,
    fontName="Courier-Bold",
)


# =========================================================
# HELPERS
# =========================================================

def get_image(path, width, height, fallback):
    if path and os.path.exists(path):
        return Image(path, width=width, height=height)
    return Paragraph(fallback, SMALL)

def add_footer(canvas, doc):
    canvas.saveState()

    width, height = A4

    footer_text = [
        "UNIVERSITÉ INTERNATIONALE DE COCODY",
        "Arrêté n°487/MESRS/DGSE du 29/12/2015",
        "Siège Social : Cocody 2 Plateaux, Teme Tranche non loin du café de Versailles",
        "04 B.P ABJ 04, Côte d'Ivoire",
        "Email : uicinfos@gmail.com | Tel : (+225) 27 22 52 28 84 - 07 78 63 74 00"
    ]

    y = 2.2 * cm  # position du footer

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)

    for line in footer_text:
        canvas.drawCentredString(width / 2, y, line)
        y -= 0.35 * cm

    canvas.restoreState()

# =========================================================
# GENERATION PDF
# =========================================================

def generer_bulletin_tronc_commun_pdf(etudiant, semestre,file_path):

    ues = UE.objects.filter(
        filiere__libelle="Gestion et Droit"
    ).prefetch_related(
         "ecues"
    )


    print("=" * 50)
    print("ETUDIANT :", etudiant.nom)
    print("FILIERE :", etudiant.filiere)
    print("NB UE :", ues.count())

    # doc = SimpleDocTemplate(file_path, pagesize=A4)
    doc = SimpleDocTemplate(
    file_path,
    pagesize=A4,
    leftMargin=0.6 * cm,
    rightMargin=0.6 * cm,
    topMargin=0.6 * cm,
    bottomMargin=2.8 * cm,   # laisser la place au footer
    )
    
    from reportlab.platypus import PageTemplate, Frame

    frame = Frame(
         doc.leftMargin,
         doc.bottomMargin,
         doc.width,
         doc.height,
         id='normal'
     )

    # doc = SimpleDocTemplate(file_path, pagesize=A4)

    doc.addPageTemplates([
          PageTemplate(id='main', frames=frame, onPage=add_footer)
        ])
    elements = []

    style_universite = ParagraphStyle(
    "style_universite",
    parent=SMALL,
    fontSize=9,
    leading=11,
   )
    # =========================================================
    # HEADER REPUBLIQUE
    # =========================================================
    # logo_header_path = os.path.join(settings.BASE_DIR, "core/static/logo.jpeg")
    logo_path = os.path.join(settings.BASE_DIR, "core/static/logo.jpeg")
    logo = get_image(logo_path, 1.8* cm, 1.8 * cm, "LOGO")

    header_table = Table([
    [
        Paragraph("""
        <para align="center">
       <b>
       <font color="#002147">
        MINISTÈRE DE L'ENSEIGNEMENT <br/>SUPÉRIEUR
        ET DE LA <br/>RECHERCHE SCIENTIFIQUE
        </font>
        </b>
        </para>
        """, style_universite),
         logo,
        
        Paragraph("""
        <para align="center">
        <b>RÉPUBLIQUE DE CÔTE D'IVOIRE</b><br/>
        Union - Discipline - Travail
        </para>
        """, style_universite)
      ]], colWidths=[7 * cm,2.5 * cm,  7 * cm])
    
    header_table.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ('ALIGN', (2, 0), (2, 0), 'CENTER'),

    ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ('TOPPADDING', (0, 0), (-1, -1), 0),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    

    elements.append(header_table)

    elements.append(Spacer(1, 14))

# Le semestre vient directement de l'URL
    semestre_saisie = semestre

# Récupérer la session correspondant au semestre
    saisie = SaisieNoteLMD.objects.filter(
        filiere=etudiant.filiere,
         niveau=etudiant.niveau,
        semestre=semestre
     ).first()

    session = saisie.session if saisie else "1"

    annee = etudiant.annee_academique

    elements.append(Paragraph(f"""
        <para align="center">
        <b>
        <font color="#B30000">RELEVE DE NOTES</font>
        &nbsp;&nbsp;&nbsp;&nbsp;
        SEMESTRE {semestre_saisie} - SESSION {session}
        &nbsp;&nbsp;&nbsp;&nbsp;
        ANNÉE SCOLAIRE : {annee}
        </b>
       </para>
       """, style_universite))

    elements.append(HRFlowable(
         width="40%",
         thickness=2,
         color=colors.HexColor("#B30000"),
         lineCap='round',
         spaceBefore=3,
         spaceAfter=10,
         hAlign='CENTER'
        ))

    # =========================================================
    # LOGO
    # =========================================================

    # logo_path = os.path.join(settings.BASE_DIR, "core/static/logo.jpeg")
    # logo = get_image(logo_path, 2 * cm, 2 * cm, "LOGO")


    # =========================================================
    # CADRE UNIVERSITE DOMAINE : SCIENCES ECONOMIQUE 
    # =========================================================
    # specialite = etudiant.filiere.nom if etudiant.filiere else "TRONC COMMUN"
    HAUTEUR_HEADER = 3.3 * cm
    specialite = etudiant.filiere.libelle if etudiant.filiere else "TRONC COMMUN"
    
    cadre_universite = Table(
    [[
        logo,
        Paragraph("""
            <b>UNIVERSITÉ INTER. DE COCODY</b><br/><br/>
            <b>DOMAINE :  TROMS COMMUN </b><br/>
            <b>SPECIALITE :</b> TROMS COMMUN<br/>
            Site: www.uci-ci.com<br/>
            Email: uicinfos@gmail.com
        """, style_universite)
    ]],
    colWidths=[1.7 * cm, 6.5 * cm],
    rowHeights=[3.2 * cm]   # hauteur fixe
    )

    cadre_universite.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
        ("TOPPADDING", (0, 2), (-1, 2), 12),  # espace avant SPÉCIALITÉ
         # réduire les marges internes
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LEFTPADDING", (1,0), (1,0), 8),

        ("LEFTPADDING", (0,0), (0,0), 3),
        ("RIGHTPADDING", (0,0), (0,0), 3),

        
        
    ]))

    elements.append(Spacer(1, 10))
    # =========================================================
    # LOGO CENTER
    # =========================================================
    date_lieu = (
    f"{etudiant.date_naissance.strftime('%d/%m/%Y')} à {etudiant.lieu_naissance}"
    if etudiant.date_naissance and etudiant.lieu_naissance
    else etudiant.date_naissance.strftime("%d/%m/%Y")
    if etudiant.date_naissance
    else ""
    )

    # =========================================================
    # ETUDIANT
    # =========================================================
    etudiant_data = [
    # ["Nom & Prénom", f"{etudiant.nom} {etudiant.prenoms}"],
    ["Nom & Prénom", f"{etudiant.nom} {etudiant.prenoms}"[:21]],
    ["Matricule", etudiant.matricule],
    # ["Né(e) le / à", date_lieu],
    ["Date/lieu de naissance", date_lieu],
    ["Sexe", getattr(etudiant, "sexe", "")],
    ["Niveau", etudiant.get_niveau_display()],
    ["Filière", etudiant.filiere],
   ]
    
    HAUTEUR_HEADER = 3.3 * cm
    NB_LIGNES = len(etudiant_data)

    cadre_etudiant = Table(
    etudiant_data,
    # colWidths=[3*cm, 5.8*cm],
    colWidths=[4*cm, 6.8*cm],   # avant : [3*cm, 5.8*cm]
    rowHeights=[HAUTEUR_HEADER / NB_LIGNES] * NB_LIGNES
    )
    cadre_etudiant.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        # ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
         # Police
        ("FONTNAME", (0, 0), (0, -1), "Courier-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
         # Alignement
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
         # Marges internes
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
         # Coins arrondis
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
          # réduire hauteur interne
        #  ("TOPPADDING", (0,0), (-1,-1), 1),
        #  ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ]))
    
    page_width = A4[0]
    usable_width = page_width - doc.leftMargin - doc.rightMargin

    header_global = Table(
    [[cadre_universite, cadre_etudiant]],
    colWidths=[
        usable_width * 0.45,
        usable_width * 0.55,
      ]
    )

    header_global.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    header_global.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    
    

    elements.append(header_global)
    elements.append(Spacer(1, 10))

    TITLE_GREEN = ParagraphStyle(
    "TITLE_GREEN",
    parent=styles["Normal"],
    fontSize=14,
    leading=16,
    alignment=1,
    spaceAfter=10,
    textColor=colors.green,
    fontName="Helvetica-Bold"
    )
    elements.append(Spacer(1, 10))
    # elements.append(
    # Paragraph("BULLETIN DE NOTES - 1er SEMESTRE", TITLE_GREEN)
    # )
    # =========================================================
    # TABLE BULLETIN
    # =========================================================

    data = [["CODE","UE:UNITES D'ENSEIGNEMENTS","ECUE","CRÉDIT\nECUE","CRÉDIT\nUE","MOY\nECUE","MOY\nUE","DÉCISION"]]

    somme_generale = 0
    total_ue = 0
    ue_validees = 0
    ue_non_validees = 0
    credits_total = 0
    credits_obtenus = 0
    somme_ponderee_ue = 0
    total_credit_ue = 0
    ecues_total = 0
    ecues_validees = 0
    row_index = 1  # 0 = header
    table_style = []
    row_index_control = 0
    index = 1  # juste après header du tableau
    ecues_non_validees = 0
    credits_ecue_total = 0
    credits_ecue_acquis = 0
     
    def add_section(title, data, table_style):
        row_index = len(data)
        # row_index = len(data)
        data.append([
           Paragraph(f'<para align="LEFT" color="red"><b>{title}</b></para>', SMALL),
        "", "",total_credit_ecue, total_credit_ue, total_moy_ecue, total_moy_ue , ""
        ])

        table_style.append(("SPAN", (0, row_index), (2, row_index)))
        table_style.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#D9D9D9")))
        table_style.append(("ALIGN", (0, row_index), (-1, row_index), "CENTER"))
        table_style.append(("VALIGN", (0, row_index), (-1, row_index), "MIDDLE"))
        table_style.append(("FONTNAME", (0, row_index), (-1, row_index), "Courier-Bold"))
        table_style.append(("FONTSIZE", (0, row_index), (-1, row_index), 10))
        table_style.append(("TOPPADDING", (0, row_index), (-1, row_index), 6))
        table_style.append(("BOTTOMPADDING", (0, row_index), (-1, row_index), 6))
        table_style.append(("TEXTCOLOR", (0, row_index), (-1, row_index), colors.green))

    compteur_ue = 0
    for ue in ues: 
        compteur_ue += 1  
        if compteur_ue == 4:
            # ues_fondamentales = ues[:compteur_ue-1]  # les 4 premières UE
            # ues_fondamentales = ues[:4]  # les 5 premières UE
            ues_fondamentales = ues[:5]
            total_credit_ecue = sum(
                ecue.credit
                for ue_temp in ues[:3]
                for ecue in ue_temp.ecues.all()
                 )
                 
            total_credit_ue = sum(
                getattr(ue_temp, "credit", 0)
                for ue_temp in ues[:2]
                ) 
              # TOTAL MOYENNES ECUE

            total_moy_ecue = 0
            total_moy_ue = 0
            for ue_temp in ues_fondamentales:
                somme_ecue = 0
                nombre_ecue = 0

                for ecue in ue_temp.ecues.all():
                    note = NoteLMD.objects.filter(
                      etudiant=etudiant,
                      ecue=ecue,
                      semestre=semestre,
                      session="1"

                    ).first()
                    moy_ecue = float(note.moyenne) if note and note.moyenne else 0
                    total_moy_ecue = moy_ecue
                    somme_ecue += moy_ecue
                    nombre_ecue += 1
                # Moyenne de l'UE
                    moy_ue = (
                       round(somme_ecue / nombre_ecue, 2)
                       if nombre_ecue else 0
                      )
                    total_moy_ue = moy_ue

            # total_credit_ue = sum(
            #      ue_temp.credit or 0
            #     for ue_temp in ues_fondamentales total_moy_ecue
            #    )  
                 # Somme des crédits UE des 5 premières UE
            add_section(f"UE : UNITÉS FONDAMENTALES ",data,table_style)
          
            # add_section(f"{ue.code} - UE : UNITÉS FONDAMENTALES (ECUE={total_credit_ecue} | UE={total_credit_ue})",data,table_style)

        if compteur_ue == 6:
            ues_culture = ues[6:9]  # 6ème à la 19ème UE
            total_credit_ecue = sum(
                ecue.credit
                 for ue_temp in ues[2:4]
                #  for ue_temp in ues_culture
                  for ecue in ue_temp.ecues.all() )

            total_credit_ue = sum(
                getattr(ue_temp, "credit", 0)
                for ue_temp in ues[2:4]
                # for ue_temp in ues_culture
                )
            
            total_moy_ecue_culture = 0
            nb_ecue_culture = 0
            total_moy_ue_culture = 0
            nb_ue_culture = 0
            
            for ue_temp in ues_culture:
                somme_ecue = 0
                nombre_ecue = 0
                for ecue in ue_temp.ecues.all():
                    note = NoteLMD.objects.filter(
                        etudiant=etudiant,
                        ecue=ecue,
                        semestre=semestre,
                        session="1"
                         ).first()
                    moy_ecue = (
                        float(note.moyenne)
                        if note and note.moyenne is not None 
                         else 0 )
                    # total_moy_ecue_culture += moy_ecue
                    total_credit_ecue += moy_ecue
                    nb_ecue_culture += 1
                    somme_ecue += moy_ecue
                    nombre_ecue += 1
                if nombre_ecue:
                    moy_ue = round(somme_ecue / nombre_ecue, 2)
                    total_moy_ue += moy_ue
                    nb_ue_culture += 1
            total_moy_ecue = (
                 round(total_moy_ecue / nb_ecue_culture, 2)
                 if nb_ecue_culture else 0   )
            total_moy_ue = (
                round(total_moy_ue / nb_ue_culture, 2)
                if nb_ue_culture else 0  )
            
            add_section("UE: UNITES DE CULTURE GENERALES", data, table_style)
            # add_section(f"UE : UNITES DE CULTURE GENERALES "f"(ECUE={total_credit_ecue} | "f"UE={total_credit_ue_culture} | "f"MOY={moyenne_ue_culture})",data,table_style,)
        if compteur_ue == 15:
            add_section("UE: UNITES DE SPECIALITES", data, table_style)

        # ecues = ue.ecues.all()
        # ecues = ECUE.objects.filter(ue=ue)  # SAFE à 100%
        ecues = ue.ecues.all()
        print(len(data))
        print(data[:3])
        somme_ue = 0
        count = 0
        lignes = []
        credit_ue = getattr(ue, "credit", 6)
        somme_ponderee = 0
        credit_total_ue = 0

        premiere_ligne = True
        
        for ecue in ecues:
            ecues_total += 1
            note = NoteLMD.objects.filter(
                etudiant=etudiant,
                ecue=ecue,
                semestre="S1",
                session="1"
            ).first()
            row_index = len(data)
            moy_ecue = float(note.moyenne) if note and note.moyenne is not None else 0.0
            # ✔ ECUE validéeCODE
            credits_ecue_total += ecue.credit
            ecues_total += 1
            
            if moy_ecue >= 10:
                 ecues_validees += 1
                 credits_ecue_acquis += ecue.credit
            else:
                  ecues_non_validees += 1  
                 
            credit_ecue = ecue.credit
             # ✔ pondération correcte
            somme_ponderee += credit_ecue * moy_ecue
            credit_total_ue += credit_ecue
            moy_ue = round(somme_ponderee / credit_total_ue, 2) if credit_total_ue else 0
            # moy_ue = round(somme_ecue / nombre_ecue,2)
            

            somme_ue += moy_ecue
            count += 1

            lignes.append([
                ue.code if premiere_ligne else "",
                ue.libelle if premiere_ligne else "",
                ecue.libelle,
                # getattr(ecue, "credit", 0),
                ecue.credit,
                credit_ue,
                round(moy_ecue, 2),
                "",
                "",
                
            ])

            premiere_ligne = False
            # insert_index += 1   # 🔥 chaque ECUE ajoute une ligne

        if count == 0:
             continue
            
        moy_ue = round(somme_ue / count, 2)
        # decision = "VALIDÉE" if moy_ue >= 10 else "NON VALIDÉE"
        decision = (
            '<para align="center"><font color="green"><b>VALIDÉE</b></font></para>'
            if moy_ue >= 10
            else '<para align="center"><font color="red"><b>NON VALI</b></font></para>'
        )

        credits_total += credit_ue

        if moy_ue >= 10:
            ue_validees += 1
            credits_obtenus += credit_ue
          
        else:
            ue_non_validees += 1

        somme_generale += moy_ue
        total_ue += 1

        for r in lignes:
            r[6] = moy_ue
            # r[7] = decision
            r[7] = Paragraph(decision, SMALL)
            data.append(r)


    moyenne_generale = round(somme_generale / total_ue, 2) if total_ue else 0

    credits_restants = credits_total - credits_obtenus
    table = Table(data, colWidths=[
        1.4 * cm,
        6 * cm,
        6 * cm,
        1.4 * cm,
        1.4 * cm,
        1.5 * cm,
        1 * cm,
        2.1 * cm
    ],
    rowHeights=[30] + [15] * (len(data) - 1)
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        # ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        # ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
      ]   + table_style))

    elements.append(table)
    elements.append(Spacer(1, 10))
    credits_ue_total = credits_total
    credits_ue_acquis = credits_obtenus
    credits_ue_restants = credits_ue_total - credits_ue_acquis
    credits_ecue_restants = credits_ecue_total - credits_ecue_acquis
    
    
    # =========================================================
    # RECAP TABLE (TA DEMANDE EXACTE)
    # =========================================================
    rang = "-"

    
    if credits_ue_restants == 0 and credits_ecue_restants == 0:
        decision_globale = (
             '<para align="center">'
              '<font color="green"><b>ADMIS</b></font>'
             '</para>'
          )
    else:
         decision_globale = (
              '<para align="center">'
              '<font color="red"><b>SESSION DE RATTRAPAGE</b></font>'
               '</para>'
        )
         
         

    recap_final_table = Table([
        [
            Paragraph("<b>Récapitulatif du travail</b>", SMALL),
            Paragraph("<b>Responsable</b>", SMALL),
            Paragraph("<b>Année de validation</b>", SMALL),
            Paragraph("<b>Décision</b>", SMALL),
        ],
        [
            Paragraph(
                f"""
                <para color="#1F4E79">
                Total ECUE validés : {ecues_validees}/{ecues_total}<br/>
                Total UE validées : {ue_validees}/{total_ue}<br/>
                Total crédits acquis : {credits_obtenus}/{credits_total}<br/>
                Total Crédits restants : {credits_restants}/{credits_total}<br/>
                Moyenne obtenue : {moyenne_generale}/20<br/>
                 </para>
                """,
                SMALL
            ),
            # Paragraph("Dr.JERRY TAFOTIE", SMALL),
            Paragraph("""Dr.JERRY TAFOTIE<br/><br/>M. N'GORAN CELESTIN""",SMALL),
            # Paragraph("2025 - 2026", SMALL),
            Paragraph(f"{annee}", SMALL),
            Paragraph(decision_globale, SMALL),
        ]
    ], colWidths=[7.5 * cm, 4 * cm, 5 * cm, 4 * cm], # ✅ IMPORTANT : 2 lignes = 2 hauteurs
       rowHeights=[0.8 * cm, 2.7 * cm])

    recap_final_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        # ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),  # 🔥 plus grand pour header
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))

    elements.append(recap_final_table)

    # =========================================================
    # SIGNATURE
    # =========================================================
    # =========================================================
# SIGNATURE
# =========================================================

    moyenne = calcul_moyenne_etudiant(etudiant, semestre)

    if moyenne >= 10:
        decision = """
        ☑ Validé(e)<br/>
        ☐ Non validé(e)<br/>
        ☐ Validé(e) par compensation
        """
    elif moyenne >= 8:
         decision = """
         ☐ Validé(e)<br/>
         ☐ Non validé(e)<br/>
         ☑ Validé(e) par compensation
        """
    else:
        decision = """
        ☐ Validé(e)<br/>
        ☑ Non validé(e)<br/>
        ☐ Validé(e) par compensation
        """

    decision_paragraph = Paragraph(
        f"""
       <b>DÉCISION</b><br/><br/>
        {decision}
        """,
       SMALL
      )

    visa_paragraph = Paragraph(
      """
      <b>VISA DU CHEF D'ÉTABLISSEMENT</b><br/><br/>
      """,
      SMALL
    )

    signature_table = Table(
       [[decision_paragraph, visa_paragraph]],
       colWidths=[8 * cm, 8 * cm],
       rowHeights=[3 * cm]
     )

    signature_table.setStyle(TableStyle([
       ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
       ("VALIGN", (0, 0), (-1, -1), "TOP"),
       ("LINEBEFORE", (1, 0), (1, -1), 0.8, colors.HexColor("#333333")),
       ("LEFTPADDING", (0, 0), (-1, -1), 8),
       ("RIGHTPADDING", (0, 0), (-1, -1), 8),
       ("TOPPADDING", (0, 0), (-1, -1), 8),
      ]))

    elements.append(Spacer(1, 15))
    elements.append(signature_table)
  
    
    # =========================================================
    # BUILD  
    # =========================================================
     
    doc.build(elements)

    return file_path