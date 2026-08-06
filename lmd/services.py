from .models import NoteLMD, CandidatRattrapage

from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os
from .models import  UE, ECUE,NoteLMD
from reportlab.platypus import HRFlowable
from .models import SaisieNoteLMD
from django.db.models import Prefetch
# ==========================================================
# CALCUL MOYENNE ECUE
# ==========================================================
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
    fontSize=8,
    leading=10,
    fontName="Courier-Bold",
)


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
       
        
    ]

    y = 2.2 * cm  # position du footer

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)

    for line in footer_text:
        canvas.drawCentredString(width / 2, y, line)
        y -= 0.35 * cm

    canvas.restoreState()
    
    
# def generer_bulletin_licence2_droit_prive_pdf(etudiant, semestre, file_path):

#     return generer_bulletin_droit_prive_pdf(
#         etudiant=etudiant,
#         semestre=semestre,
#         file_path=file_path
#     )   


def calcul_moyenne_ecue(etudiant, ecue, semestre=None):

    note = NoteLMD.objects.filter(
        etudiant=etudiant,
        ecue=ecue
    )

    if semestre:
        note = note.filter(semestre=semestre)

    note = note.first()

    if not note:
        return 0

    return round(float(note.moyenne), 2)



# ==========================================================
# CALCUL MOYENNE UE
# Règle document :
# MOY UE = Somme des MOY ECUE / Nombre ECUE
# ==========================================================

def calcul_moyenne_ue(etudiant, ue, semestre=None):

    ecues = ue.ecues.all()

    total = 0
    nombre_ecue = 0


    for ecue in ecues:

        moyenne = calcul_moyenne_ecue(
            etudiant,
            ecue,
            semestre
        )

        total += moyenne
        nombre_ecue += 1


    if nombre_ecue == 0:
        return 0


    return round(
        total / nombre_ecue,
        2
    )



# ==========================================================
# CREDIT UE
# CREDIT UE = somme CREDIT ECUE
# ==========================================================

def calcul_credit_ue(ue):

    return sum(
        ecue.credit
        for ecue in ue.ecues.all()
    )



# ==========================================================
# DECISION UE
# ==========================================================

def statut_ue(moyenne):

    if moyenne >= 10:
        return "VALIDÉE"

    return "NON VALIDÉE"



# ==========================================================
# ECUE VALIDATION / COMPENSATION
# ==========================================================

def ecue_validee(
        moyenne_ecue,
        moyenne_ue
):

    """
    Une ECUE est validée :
    - directement si moyenne ECUE >=10
    - par compensation si moyenne UE >=10
    """

    if moyenne_ecue >= 10:
        return True


    if moyenne_ue >= 10:
        return True


    return False



# ==========================================================
# CREDIT ACQUIS
# ==========================================================

def calcul_credits_acquis(
        etudiant,
        ues,
        semestre=None
):

    credits = 0


    for ue in ues:


        moyenne_ue = calcul_moyenne_ue(
            etudiant,
            ue,
            semestre
        )


        for ecue in ue.ecues.all():


            moyenne_ecue = calcul_moyenne_ecue(
                etudiant,
                ecue,
                semestre
            )


            if ecue_validee(
                moyenne_ecue,
                moyenne_ue
            ):

                credits += ecue.credit



    # maximum 30 crédits

    return min(
        credits,
        30
    )



# ==========================================================
# NOMBRE ECUE VALIDES
# ==========================================================

def calcul_ecue_valides(
        etudiant,
        ues,
        semestre=None
):

    total = 0


    for ue in ues:

        moyenne_ue = calcul_moyenne_ue(
            etudiant,
            ue,
            semestre
        )


        for ecue in ue.ecues.all():

            moyenne_ecue = calcul_moyenne_ecue(
                etudiant,
                ecue,
                semestre
            )


            if ecue_validee(
                moyenne_ecue,
                moyenne_ue
            ):

                total += 1


    return total



# ==========================================================
# NOMBRE UE VALIDES
# ==========================================================

def calcul_ue_valides(
        etudiant,
        ues,
        semestre=None
):

    total = 0


    for ue in ues:

        moyenne = calcul_moyenne_ue(
            etudiant,
            ue,
            semestre
        )


        if moyenne >= 10:
            total += 1


    return total



# ==========================================================
# MOYENNE GENERALE ETUDIANT
# Document :
# Moyenne générale = somme Moy UE / Total UE
# ==========================================================

def calcul_moyenne_etudiant(
        etudiant,
        semestre=None
):

    from .models import UE


    ues = UE.objects.filter(
        filiere=etudiant.filiere
    )


    total = 0
    nombre = 0


    for ue in ues:

        moyenne = calcul_moyenne_ue(
            etudiant,
            ue,
            semestre
        )


        total += moyenne
        nombre += 1



    if nombre == 0:
        return 0


    return round(
        total / nombre,
        2
    )



# ==========================================================
# DECISION FINALE BULLETIN
# ==========================================================

def decision_bulletin(
        etudiant,
        ues,
        semestre=None
):


    credits = calcul_credits_acquis(
        etudiant,
        ues,
        semestre
    )


    ue_valides = calcul_ue_valides(
        etudiant,
        ues,
        semestre
    )


    ecue_valides = calcul_ecue_valides(
        etudiant,
        ues,
        semestre
    )


    total_ue = ues.count()


    total_ecue = sum(
        ue.ecues.count()
        for ue in ues
    )


    if (
        credits == 30
        and ue_valides == total_ue
        and ecue_valides == total_ecue
    ):

        return "VALIDÉE AU COMPLET"



    elif credits == 30:

        return "VALIDÉE PAR COMPENSATION"



    else:

        return "NON VALIDÉE"



# ==========================================================
# CREATION CANDIDATS RATTRAPAGE
# ==========================================================

def creer_candidats_rattrapage(etudiant):

    notes = NoteLMD.objects.filter(
        etudiant=etudiant,
        session="1"
    )


    for note in notes:


        if note.moyenne < 10:


            CandidatRattrapage.objects.get_or_create(

                etudiant=etudiant,

                ecue=note.ecue,

                semestre=note.semestre,

                annee_academique=etudiant.annee_academique,


                defaults={

                    "ancienne_note": note.moyenne,

                    "session":"2"

                }

            )
            
def generer_bulletin_licence2_droit_prive_pdf(etudiant, semestre, file_path):

    return generer_bulletin_droit_prive_pdf(
        etudiant=etudiant,
        semestre=semestre,
        file_path=file_path
    )
def generer_bulletin_droit_prive_pdf(etudiant, semestre, file_path):
    
    somme_ue = 0
    total_credit = 0
    credits_obtenus = 0
    moyenne_generale = 0
    moyennes_ues = []   # <-- ajouter cette ligne

    ues = (
         UE.objects
         .filter(
              filiere=etudiant.filiere,
              semestre=semestre,
              niveau=etudiant.niveau
       )
       .select_related("grande_unite")
       .prefetch_related(
          Prefetch(
            "ecues",
             queryset=ECUE.objects.order_by("ordre")
            )
       )
       .order_by("ordre")
    )
    somme_ue = 0
    count = 0
    total_credit = 0
    credits_obtenus = 0
    moyenne_generale = 0

    
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


    doc.addPageTemplates([
          PageTemplate(id='main', frames=frame, onPage=add_footer)
        ])
    elements = []
    logo_path = os.path.join(settings.BASE_DIR, "core/static/logo.jpeg")
    logo = get_image(logo_path, 1.8* cm, 1.8 * cm, "LOGO")

    header_table = Table([
    [
        Paragraph("""
        <para align="center">
       <b>
       <font color="#002147" size="11">
        MINISTÈRE DE L'ENSEIGNEMENT <br/>SUPÉRIEUR
        ET DE LA <br/>RECHERCHE SCIENTIFIQUE
        </font>
        </b>
        </para>
        """, SMALL),
         logo,
        
        Paragraph("""
        <para align="center">
        <b>RÉPUBLIQUE DE CÔTE D'IVOIRE</b><br/>
        Union - Discipline - Travail
        </para>
        """, SMALL)
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
    saisie = SaisieNoteLMD.objects.filter(
    filiere=etudiant.filiere,
    niveau=etudiant.niveau
   ).first()

    session = "NORMALE"

    if semestre == "S1":
       libelle_semestre = "1er SEMESTRE"
    else:
       libelle_semestre = "2ème SEMESTRE"
    
    annee = etudiant.annee_academique

    elements.append(Paragraph(f"""
        <para align="center">
        <b>
        <font color="#B30000">RELEVE DE NOTES</font>
        &nbsp;&nbsp;&nbsp;&nbsp;
         {libelle_semestre} - SESSION {session}
        &nbsp;&nbsp;&nbsp;&nbsp;
        ANNÉE SCOLAIRE : {annee}
        </b>
       </para>
       """, SMALL))

    elements.append(HRFlowable(
         width="40%",
         thickness=2,
         color=colors.HexColor("#B30000"),
         lineCap='round',
         spaceBefore=3,
         spaceAfter=10,
         hAlign='CENTER'
        ))

    specialite = etudiant.filiere.libelle if etudiant.filiere else " DROIT PRIVE"
    cadre_universite = Table([[
        Paragraph(f"""
            <b>DOMAINE : <br/> DROIT PRIVE </b><br/>
             <b></b><br/><br/>
             <b>SPECIALITE :</b><br/> {specialite}<br/>
        """, SMALL)
    ]], colWidths=[8 * cm], rowHeights=[3.7 * cm])

    cadre_universite.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
        ("TOPPADDING", (0, 2), (-1, 2), 12),  # espace avant SPÉCIALITÉ
    ]))

    elements.append(Spacer(1, 10))
    # =========================================================
    # LOGO CENTER
    # =========================================================
    cadre_etudiant = Table([
        [
        Paragraph("<b>Nom et Prénoms</b>", SMALL),
        Paragraph(f"{etudiant.nom} {etudiant.prenoms}", SMALL)],
        [
        Paragraph("<b>Date de naissance</b>", SMALL),
        Paragraph(
            f"{safe_date(etudiant.date_naissance)}",
            SMALL
        )
       ],

        # lieu = etudiant.lieu_naissance or "-"

        # Paragraph(f"{date_naissance} à {lieu}", SMALL)
        [Paragraph("<b>Sexe</b>", SMALL),Paragraph(etudiant.get_sexe_display(), SMALL)],
        [Paragraph("<b>Matricule</b>", SMALL), Paragraph(str(etudiant.matricule), SMALL)],
        [Paragraph("<b>Statut</b>", SMALL),Paragraph(etudiant.statut, SMALL)],
        [Paragraph("<b>Niveau</b>", SMALL), 
         Paragraph(etudiant.get_niveau_display(), SMALL)],
    ], colWidths=[5 * cm, 3.5 * cm])

    cadre_etudiant.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
    ]))


    header_global = Table(
        [[cadre_universite, cadre_etudiant]],
        colWidths=[12 * cm, 8 * cm],
        rowHeights=[3.5 * cm]
    )
    header_global.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    
    

    elements.append(header_global)
    elements.append(Spacer(1, 10))

    elements.append(Spacer(1, 10))
    
    data = [["CODE","UE:UNITES D'ENSEIGNEMENTS","ECUE","CRÉD\nECUE","CRÉD\nUE","MOY\nECUE","MOY\nUE","DÉCISION"]]
    table_style = []
    ecues_total = 0
    ecues_validees = 0
    ue_validees = 0
    credits_total = 0
    credits_obtenus = 0
    total_ue = 0
    ecues_validees = 0
    credits_total = 0
    credits_obtenus = 0
    credits_restants = 0
    credits_ecue_total = 0
    credits_ecue_acquis = 0
    moyenne_generale = 0
    stats = {
    "ue_total":0,
    "ue_validees":0,
    "credits_total":0,
    "credits_obtenus":0,
    "ecues_total":0,
    "ecues_validees":0,
    "credits_ecue_total":0,
    "credits_ecue_obtenus":0,
    "moyenne_generale":0,
    }
  
    def add_section(title, data, table_style):
        row_index = len(data)
        table_style.append(("SPAN", (0, row_index), (2, row_index)))
        table_style.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#D9D9D9")))
        table_style.append(("ALIGN", (0, row_index), (-1, row_index), "CENTER"))
        table_style.append(("VALIGN", (0, row_index), (-1, row_index), "MIDDLE"))
        table_style.append(("FONTNAME", (0, row_index), (-1, row_index), "Courier-Bold"))
        table_style.append(("FONTSIZE", (0, row_index), (-1, row_index), 10))
        table_style.append(("TOPPADDING", (0, row_index), (-1, row_index), 6))
        table_style.append(("BOTTOMPADDING", (0, row_index), (-1, row_index), 6))
        table_style.append(("TEXTCOLOR", (0, row_index), (-1, row_index), colors.green))

    grande_unite_actuelle = None
    somme_moyennes = 0
    nb_ue = 0
    somme_ue = 0
    moyenne_ue = 0      # <-- ajouter ceci
    for ue in ues: 
        ecues = ue.ecues.all()
        
        if not ecues.exists():
            continue
        
        lignes_ue = []
        premiere_ligne = True
      
        count = 0
        stats["ue_total"] += 1
        stats["credits_total"] += ue.credit
        
      
             
        if ue.grande_unite != grande_unite_actuelle:
           grande_unite_actuelle = ue.grande_unite
           data.append([
               Paragraph(
                   f"<b>{grande_unite_actuelle.nom}</b>",
                    SMALL
                    ),
                "",
                 "",
                 "",
                 "",
                 "",
                 "",
                ""
            ])
           ligne = len(data)-1
           
           table_style.append(
               ("SPAN",(0,ligne),(7,ligne))
            )
           
           table_style.append(
                 ("BACKGROUND",(0,ligne),(7,ligne),colors.HexColor("#D9D9D9"))
             )
           table_style.append(
                  ("FONTNAME",(0,ligne),(7,ligne),"Helvetica-Bold")
            )
               
        ecues = ue.ecues.all()
        somme_ue = 0
        count = 0
        credit_ue = getattr(ue, "credit", 6)
        premiere_ligne = True
        somme = 0
        coef = 0
        if count > 0:
           moy_ue = round(somme_ue / count, 2)
        else:
           moy_ue = 0
        moyenne_ue = round(somme / coef, 2)
        somme_moyennes += moyenne_ue
        nb_ue += 1

        for ecue in ecues:
           
            note = NoteLMD.objects.filter(
                etudiant=etudiant,
                ecue=ecue,
                semestre=semestre,
                session="1"
            ).first()
            moy_ecue = float(note.moyenne) if note and note.moyenne is not None else 0.0
            if moy_ecue >= 10:
                 stats["ecues_validees"] += 1
                 stats["credits_ecue_obtenus"] += ecue.credit
                 
            moyenne = note.moyenne if note else 0
            somme += moyenne * ecue.coefficient
            coef += ecue.coefficient
           
            moyenne_ue = (round(somme / coef, 2)if coef > 0 else 0)
            # ✔ ECUE validéeCODE
            moyennes_ues.append(moyenne_ue)
            somme_ue += moy_ecue
            count += 1
          
            if moyenne_ue >= 10:
               stats["ue_validees"] += 1
               stats["credits_obtenus"] += ue.credit
               decision = Paragraph("<font color='green'><b>VALIDÉE</b></font>",SMALL)
            else:
               decision = Paragraph("<font color='red'><b>NON VALI</b></font>",SMALL)   
            
            lignes_ue.append([
            Paragraph(ue.code if premiere_ligne else "", SMALL),
            Paragraph(ue.libelle if premiere_ligne else "", SMALL),
            Paragraph(ecue.libelle, SMALL),
            Paragraph(str(ecue.credit), SMALL),
            Paragraph(str(ue.credit) if premiere_ligne else "", SMALL),
            Paragraph(f"{moyenne:.2f}", SMALL),
            Paragraph(f"{moyenne_ue:.2f}" if premiere_ligne else "", SMALL),
            decision if premiere_ligne else ""
             ])
            
            stats["ecues_total"] += 1
            stats["credits_ecue_total"] += ecue.credit

            premiere_ligne = False
            
            if count == 0:
                continue
                        
        debut = len(data)
        for ligne in lignes_ue:
             data.append(ligne)
        fin = len(data)-1
             # fusion des cellules UE
        for col in [0,1,4,6,7]:    
                 table_style.append(
                       (
                       "SPAN",
                       (col,debut),
                       (col,fin)
                    )
                      )
        couleur = colors.green if moyenne_ue >= 10 else colors.red
        table_style.append(
                  ("TEXTCOLOR",(7,debut),(7,fin),couleur)
                  )
        table_style.append(
                 ("FONTNAME",(7,debut),(7,fin),"Helvetica-Bold")
                   )  
         
    if count > 0:
           moy_ue = round(somme_ue / count, 2)
    else:
             moy_ue = 0

    if coef > 0:
            moyenne_ue = round(somme / coef, 2)
    else:
            moyenne_ue = 0


    somme_moyennes += moyenne_ue
    nb_ue += 1         
            

    decision = (
            '<para align="center"><font color="green"><b>VALIDÉE</b></font></para>'
            if moy_ue >= 10
            else '<para align="center"><font color="red"><b>NON VALI</b></font></para>'
        )

    table = Table(data, colWidths=[
        1.4 * cm,   # Code
        6 * cm,   # UE
        6 * cm,   # ECUE
        1.1 * cm,   # Crédit ECUE
        1.1 * cm,   # Crédit UE
        1.5 * cm,   # Moy ECUE
        1.5 * cm,   # Moy UE
        2.1 * cm    # Décision
    ],
    rowHeights=[30] + [15] * (len(data) - 1)
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
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
    ecues_total = stats["ecues_total"]
    ecues_validees = stats["ecues_validees"] 
    total_ue = stats["ue_total"]
    ue_validees = stats["ue_validees"]

    credits_total = stats["credits_total"]
    credits_obtenus = stats["credits_obtenus"]

    credits_restants = credits_total - credits_obtenus
   
    moyenne_generale = (
          round(sum(moyennes_ues) / len(moyennes_ues), 2)
          if moyennes_ues
          else 0
        )

    # moyenne_generale = (
    # round(somme / credits_total, 2)
    # if credits_total > 0 else 0
    # )
         
    recap_final_table = Table([
        [
            Paragraph("<b>Récapitulatif</b>", SMALL),
            Paragraph("<b>Responsable</b>", SMALL),
            Paragraph("<b>Année</b>", SMALL),
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
            Paragraph("""Dr.JERRY TAFOTIE<br/><br/>""",SMALL),
            Paragraph(f"ANNÉE SCOLAIRE : {annee}", SMALL),
            Paragraph(decision_globale, SMALL),
        ]
    ], colWidths=[8.5 * cm, 4 * cm, 4 * cm, 4 * cm], # ✅ IMPORTANT : 2 lignes = 2 hauteurs
       rowHeights=[0.8 * cm, 2.7 * cm])

    recap_final_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),  # 🔥 plus grand pour header
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    elements.append(recap_final_table)

    signature_table = Table([[
        Paragraph("<b>RESPONSABLE</b><br/>", styles["Normal"]),
        Paragraph("<b>VISA</b><br/><br/>""Dr.JERRY TAFOTIE<br/><br/>""",styles["Normal"]),
    ]], colWidths=[8 * cm, 8 * cm], rowHeights=[3 * cm])

    signature_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBEFORE", (1, 0), (1, -1), 0.8, colors.HexColor("#333333")),
    ]))

    elements.append(Spacer(1, 15))
    elements.append(signature_table)
     
    doc.build(elements)

    return file_path

# lmd/services.py

def generer_bulletin_lmd_pdf(
    etudiant,
    semestre,
    file_path
):

    filiere = etudiant.filiere.libelle


    if filiere == "Droit Privé":

        from .pdf_droit_prive_service import (
            generer_bulletin_droit_prive_pdf
        )

        return generer_bulletin_droit_prive_pdf(
            etudiant,
            semestre,
            file_path
        )


    elif filiere == "Gestion et Droit":

        from .pdf_gestion_droit_service import (
            generer_bulletin_gestion_droit_pdf
        )

        return generer_bulletin_gestion_droit_pdf(
            etudiant,
            semestre,
            file_path
        )


    elif filiere == "Sciences de Gestion":

        from .pdf_sciences_gestion_service import (
            generer_bulletin_sciences_gestion_pdf
        )

        return generer_bulletin_sciences_gestion_pdf(
            etudiant,
            semestre,
            file_path
        )


    elif filiere == "Management QHSE":

        from .pdf_qhse_service import (
            generer_bulletin_qhse_pdf
        )

        return generer_bulletin_qhse_pdf(
            etudiant,
            semestre,
            file_path
        )


    else:
        raise ValueError(
            f"Aucun générateur PDF pour la filière {filiere}"
        )

def generer_bulletin_droit_prive_pdfAA(etudiant, semestre, file_path):

    ues = (
         UE.objects
         .filter(
              filiere=etudiant.filiere,
              semestre=semestre,
              niveau=etudiant.niveau
       )
       .select_related("grande_unite")
       .prefetch_related(
          Prefetch(
            "ecues",
             queryset=ECUE.objects.order_by("ordre")
            )
       )
       .order_by("ordre")
    )
    
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


    doc.addPageTemplates([
          PageTemplate(id='main', frames=frame, onPage=add_footer)
        ])
    elements = []
    logo_path = os.path.join(settings.BASE_DIR, "core/static/logo.jpeg")
    logo = get_image(logo_path, 1.8* cm, 1.8 * cm, "LOGO")

    header_table = Table([
    [
        Paragraph("""
        <para align="center">
       <b>
       <font color="#002147" size="11">
        MINISTÈRE DE L'ENSEIGNEMENT <br/>SUPÉRIEUR
        ET DE LA <br/>RECHERCHE SCIENTIFIQUE
        </font>
        </b>
        </para>
        """, SMALL),
         logo,
        
        Paragraph("""
        <para align="center">
        <b>RÉPUBLIQUE DE CÔTE D'IVOIRE</b><br/>
        Union - Discipline - Travail
        </para>
        """, SMALL)
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
    saisie = SaisieNoteLMD.objects.filter(
    filiere=etudiant.filiere,
    niveau=etudiant.niveau
   ).first()

    session = "NORMALE"

    if semestre == "S1":
       libelle_semestre = "1er SEMESTRE"
    else:
       libelle_semestre = "2ème SEMESTRE"
    
    annee = etudiant.annee_academique

    elements.append(Paragraph(f"""
        <para align="center">
        <b>
        <font color="#B30000">RELEVE DE NOTES</font>
        &nbsp;&nbsp;&nbsp;&nbsp;
         {libelle_semestre} - SESSION {session}
        &nbsp;&nbsp;&nbsp;&nbsp;
        ANNÉE SCOLAIRE : {annee}
        </b>
       </para>
       """, SMALL))

    elements.append(HRFlowable(
         width="40%",
         thickness=2,
         color=colors.HexColor("#B30000"),
         lineCap='round',
         spaceBefore=3,
         spaceAfter=10,
         hAlign='CENTER'
        ))

    specialite = etudiant.filiere.libelle if etudiant.filiere else " DROIT PRIVE"
    cadre_universite = Table([[
        Paragraph(f"""
            <b>DOMAINE : <br/> DROIT PRIVE </b><br/>
             <b></b><br/><br/>
             <b>SPECIALITE :</b><br/> {specialite}<br/>
        """, SMALL)
    ]], colWidths=[8 * cm], rowHeights=[3.7 * cm])

    cadre_universite.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
        ("TOPPADDING", (0, 2), (-1, 2), 12),  # espace avant SPÉCIALITÉ
    ]))

    elements.append(Spacer(1, 10))
    # =========================================================
    # LOGO CENTER
    # =========================================================
    cadre_etudiant = Table([
        [
        Paragraph("<b>Nom et Prénoms</b>", SMALL),
        Paragraph(f"{etudiant.nom} {etudiant.prenoms}", SMALL)],
        [
        Paragraph("<b>Date de naissance</b>", SMALL),
        Paragraph(
            f"{safe_date(etudiant.date_naissance)}",
            SMALL
        )
       ],

        # lieu = etudiant.lieu_naissance or "-"

        # Paragraph(f"{date_naissance} à {lieu}", SMALL)
        [Paragraph("<b>Sexe</b>", SMALL),Paragraph(etudiant.get_sexe_display(), SMALL)],
        [Paragraph("<b>Matricule</b>", SMALL), Paragraph(str(etudiant.matricule), SMALL)],
        [Paragraph("<b>Statut</b>", SMALL),Paragraph(etudiant.statut, SMALL)],
        [Paragraph("<b>Niveau</b>", SMALL), 
         Paragraph(etudiant.get_niveau_display(), SMALL)],
    ], colWidths=[5 * cm, 3.5 * cm])

    cadre_etudiant.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
    ]))


    header_global = Table(
        [[cadre_universite, cadre_etudiant]],
        colWidths=[12 * cm, 8 * cm],
        rowHeights=[3.5 * cm]
    )
    header_global.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    
    

    elements.append(header_global)
    elements.append(Spacer(1, 10))

    elements.append(Spacer(1, 10))
    
    data = [["CODE","UE:UNITES D'ENSEIGNEMENTS","ECUE","CRÉD\nECUE","CRÉD\nUE","MOY\nECUE","MOY\nUE","DÉCISION"]]
    table_style = []
    ecues_total = 0
    ecues_validees = 0
    ue_validees = 0
    credits_total = 0
    credits_obtenus = 0
    total_ue = 0
    ecues_validees = 0
    credits_total = 0
    credits_obtenus = 0
    credits_restants = 0
    credits_ecue_total = 0
    credits_ecue_acquis = 0
    moyenne_generale = 0
    stats = {
    "ue_total":0,
    "ue_validees":0,
    "credits_total":0,
    "credits_obtenus":0,
    "ecues_total":0,
    "ecues_validees":0,
    "credits_ecue_total":0,
    "credits_ecue_obtenus":0,
    "moyenne_generale":0,
    }
  
    def add_section(title, data, table_style):
        row_index = len(data)
        table_style.append(("SPAN", (0, row_index), (2, row_index)))
        table_style.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#D9D9D9")))
        table_style.append(("ALIGN", (0, row_index), (-1, row_index), "CENTER"))
        table_style.append(("VALIGN", (0, row_index), (-1, row_index), "MIDDLE"))
        table_style.append(("FONTNAME", (0, row_index), (-1, row_index), "Courier-Bold"))
        table_style.append(("FONTSIZE", (0, row_index), (-1, row_index), 10))
        table_style.append(("TOPPADDING", (0, row_index), (-1, row_index), 6))
        table_style.append(("BOTTOMPADDING", (0, row_index), (-1, row_index), 6))
        table_style.append(("TEXTCOLOR", (0, row_index), (-1, row_index), colors.green))

    grande_unite_actuelle = None
    somme_moyennes = 0
    nb_ue = 0
    moyenne_ue = 0      # <-- ajouter ceci
    for ue in ues: 
        ecues = ue.ecues.all()
       
        lignes_ue = []
        premiere_ligne = True
        somme_ue = 0
        count = 0
        stats["ue_total"] += 1
        stats["credits_total"] += ue.credit
        
        if moyenne_ue >= 10:
             stats["ue_validees"] += 1
             stats["credits_obtenus"] += ue.credit
             
        if ue.grande_unite != grande_unite_actuelle:
           grande_unite_actuelle = ue.grande_unite
           data.append([
               Paragraph(
                   f"<b>{grande_unite_actuelle.nom}</b>",
                    SMALL
                    ),
                "",
                 "",
                 "",
                 "",
                 "",
                 "",
                ""
            ])
           ligne = len(data)-1
           
           table_style.append(
               ("SPAN",(0,ligne),(7,ligne))
            )
           
           table_style.append(
                 ("BACKGROUND",(0,ligne),(7,ligne),colors.HexColor("#D9D9D9"))
             )
           table_style.append(
                  ("FONTNAME",(0,ligne),(7,ligne),"Helvetica-Bold")
            )
               
        ecues = ue.ecues.all()
        somme_ue = 0
        count = 0
        credit_ue = getattr(ue, "credit", 6)
        premiere_ligne = True
        somme = 0
        coef = 0
        for ecue in ecues:
           
            note = NoteLMD.objects.filter(
                etudiant=etudiant,
                ecue=ecue,
                semestre=semestre,
                session="1"
            ).first()
            moy_ecue = float(note.moyenne) if note and note.moyenne is not None else 0.0
            if moy_ecue >= 10:
                 stats["ecues_validees"] += 1
                 stats["credits_ecue_obtenus"] += ecue.credit
                 
            moyenne = note.moyenne if note else 0
            somme += moyenne * ecue.coefficient
            coef += ecue.coefficient
           
            moyenne_ue = round(somme/coef,2) if coef else 0
            # ✔ ECUE validéeCODE
            somme_ue += moy_ecue
            count += 1
          
            if moyenne_ue >= 10:
               stats["ue_validees"] += 1
               stats["credits_obtenus"] += ue.credit
               decision = Paragraph("<font color='green'><b>VALIDÉE</b></font>",SMALL)
            else:
               decision = Paragraph("<font color='red'><b>NON VALI</b></font>",SMALL)   
            
            lignes_ue.append([
            Paragraph(ue.code if premiere_ligne else "", SMALL),
            Paragraph(ue.libelle if premiere_ligne else "", SMALL),
            Paragraph(ecue.libelle, SMALL),
            Paragraph(str(ecue.credit), SMALL),
            Paragraph(str(ue.credit) if premiere_ligne else "", SMALL),
            Paragraph(f"{moyenne:.2f}", SMALL),
            Paragraph(f"{moyenne_ue:.2f}" if premiere_ligne else "", SMALL),
            decision if premiere_ligne else ""
             ])
            
            stats["ecues_total"] += 1
            stats["credits_ecue_total"] += ecue.credit

            premiere_ligne = False
            
            if count == 0:
                continue
                        
        debut = len(data)
        for ligne in lignes_ue:
             data.append(ligne)
        fin = len(data)-1
             # fusion des cellules UE
        for col in [0,1,4,6,7]:    
                 table_style.append(
                       (
                       "SPAN",
                       (col,debut),
                       (col,fin)
                    )
                      )
        couleur = colors.green if moyenne_ue >= 10 else colors.red
        table_style.append(
                  ("TEXTCOLOR",(7,debut),(7,fin),couleur)
                  )
        table_style.append(
                 ("FONTNAME",(7,debut),(7,fin),"Helvetica-Bold")
                   )            
             
    # moy_ue = round(somme_ue / count, 2)
    if count > 0:
         moy_ue = round(somme_ue / count, 2)
    else:
       moy_ue = 0
    moyenne_ue = round(somme / coef, 2)
    somme_moyennes += moyenne_ue
    nb_ue += 1

    decision = (
            '<para align="center"><font color="green"><b>VALIDÉE</b></font></para>'
            if moy_ue >= 10
            else '<para align="center"><font color="red"><b>NON VALI</b></font></para>'
        )

    table = Table(data, colWidths=[
        1.4 * cm,   # Code
        6 * cm,   # UE
        6 * cm,   # ECUE
        1.1 * cm,   # Crédit ECUE
        1.1 * cm,   # Crédit UE
        1.5 * cm,   # Moy ECUE
        1.5 * cm,   # Moy UE
        2.1 * cm    # Décision
    ],
    rowHeights=[30] + [15] * (len(data) - 1)
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
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
    ecues_total = stats["ecues_total"]
    ecues_validees = stats["ecues_validees"] 
    total_ue = stats["ue_total"]
    ue_validees = stats["ue_validees"]

    credits_total = stats["credits_total"]
    credits_obtenus = stats["credits_obtenus"]

    credits_restants = credits_total - credits_obtenus

    moyenne_generale = (
    round(somme / credits_total, 2)
    if credits_total > 0 else 0
    )
         
    recap_final_table = Table([
        [
            Paragraph("<b>Récapitulatif</b>", SMALL),
            Paragraph("<b>Responsable</b>", SMALL),
            Paragraph("<b>Année</b>", SMALL),
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
            Paragraph("""Dr.JERRY TAFOTIE<br/><br/>""",SMALL),
            Paragraph(f"ANNÉE SCOLAIRE : {annee}", SMALL),
            Paragraph(decision_globale, SMALL),
        ]
    ], colWidths=[8.5 * cm, 4 * cm, 4 * cm, 4 * cm], # ✅ IMPORTANT : 2 lignes = 2 hauteurs
       rowHeights=[0.8 * cm, 2.7 * cm])

    recap_final_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),  # 🔥 plus grand pour header
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),  # 👉 arrondi
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    elements.append(recap_final_table)

    signature_table = Table([[
        Paragraph("<b>RESPONSABLE</b><br/>", styles["Normal"]),
        Paragraph("<b>VISA</b><br/><br/>""Dr.JERRY TAFOTIE<br/><br/>""",styles["Normal"]),
    ]], colWidths=[8 * cm, 8 * cm], rowHeights=[3 * cm])

    signature_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBEFORE", (1, 0), (1, -1), 0.8, colors.HexColor("#333333")),
    ]))

    elements.append(Spacer(1, 15))
    elements.append(signature_table)
     
    doc.build(elements)

    return file_path

# lmd/services.py

def generer_bulletin_lmd_pdf(
    etudiant,
    semestre,
    file_path
):

    filiere = etudiant.filiere.libelle


    if filiere == "Droit Privé":

        from .pdf_droit_prive_service import (
            generer_bulletin_droit_prive_pdf
        )

        return generer_bulletin_droit_prive_pdf(
            etudiant,
            semestre,
            file_path
        )


    elif filiere == "Gestion et Droit":

        from .pdf_gestion_droit_service import (
            generer_bulletin_gestion_droit_pdf
        )

        return generer_bulletin_gestion_droit_pdf(
            etudiant,
            semestre,
            file_path
        )


    elif filiere == "Sciences de Gestion":

        from .pdf_sciences_gestion_service import (
            generer_bulletin_sciences_gestion_pdf
        )

        return generer_bulletin_sciences_gestion_pdf(
            etudiant,
            semestre,
            file_path
        )


    elif filiere == "Management QHSE":

        from .pdf_qhse_service import (
            generer_bulletin_qhse_pdf
        )

        return generer_bulletin_qhse_pdf(
            etudiant,
            semestre,
            file_path
        )


    else:
        raise ValueError(
            f"Aucun générateur PDF pour la filière {filiere}"
        )