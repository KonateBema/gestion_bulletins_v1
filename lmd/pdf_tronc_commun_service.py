from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
    HRFlowable, PageTemplate, Frame,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os
from lmd.models import EtudiantLMD
from .models import UE, NoteLMD, SaisieNoteLMD
from .services import calcul_moyenne_etudiant

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


def add_footer(c, doc):
    # BUG CORRIGÉ : le paramètre s'appelait "canvas" et masquait le module
    # "from reportlab.pdfgen import canvas" importé plus haut.
    c.saveState()

    width, height = A4

    footer_text = [
        "UNIVERSITÉ INTERNATIONALE DE COCODY",
        "Arrêté n°487/MESRS/DGSE du 29/12/2015",
        "Siège Social : Cocody 2 Plateaux, Teme Tranche non loin du café de Versailles",
        "04 B.P ABJ 04, Côte d'Ivoire",
        "Email : uicinfos@gmail.com | Tel : (+225) 27 22 52 28 84 - 07 78 63 74 00",
    ]

    y = 2.2 * cm  # position du footer

    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)

    for line in footer_text:
        c.drawCentredString(width / 2, y, line)
        y -= 0.35 * cm

    c.restoreState()


# =========================================================
# GENERATION PDF
# =========================================================

def generer_bulletin_tronc_commun_pdf(etudiant, semestre, file_path):

    # NOTE : ce filtre est volontairement codé en dur sur la filière
    # "Gestion et Droit" (bulletin de tronc commun). Si ce bulletin doit
    # au contraire refléter la filière réelle de l'étudiant, remplacer par :
    #     UE.objects.filter(filiere=etudiant.filiere)
    ues = UE.objects.filter(
        filiere__libelle="Gestion et Droit"
    ).prefetch_related("ecues")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=0.6 * cm,
        rightMargin=0.6 * cm,
        topMargin=0.6 * cm,
        bottomMargin=2.8 * cm,  # laisser la place au footer
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )

    doc.addPageTemplates([
        PageTemplate(id="main", frames=frame, onPage=add_footer)
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
    logo_path = os.path.join(settings.BASE_DIR, "core/static/logo.jpeg")
    logo = get_image(logo_path, 1.8 * cm, 1.8 * cm, "LOGO")

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
            """, style_universite),
        ]
    ], colWidths=[7 * cm, 2.5 * cm, 7 * cm])

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 14))

    # Le semestre vient directement de l'URL
    semestre_saisie = semestre

    # Récupérer la session correspondant au semestre
    saisie = SaisieNoteLMD.objects.filter(
        filiere=etudiant.filiere,
        niveau=etudiant.niveau,
        semestre=semestre,
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
        lineCap="round",
        spaceBefore=3,
        spaceAfter=10,
        hAlign="CENTER",
    ))

    # =========================================================
    # CADRE UNIVERSITE
    # =========================================================
    cadre_universite = Table(
        [[
            logo,
            Paragraph("""
                <b>UNIVERSITÉ INTER. DE COCODY</b><br/><br/>
                <b>DOMAINE :  TRONC COMMUN </b><br/>
                <b>SPECIALITE :</b> TRONC COMMUN<br/>
                Site: www.uci-ci.com<br/>
                Email: uicinfos@gmail.com
            """, style_universite),
            # BUG CORRIGÉ : "TROMS COMMUN" -> "TRONC COMMUN" (coquille)
        ]],
        colWidths=[1.7 * cm, 6.5 * cm],
        rowHeights=[3.2 * cm],
    )

    cadre_universite.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
        ("LEFTPADDING", (0, 0), (0, 0), 3),
        ("RIGHTPADDING", (0, 0), (0, 0), 3),
    ]))

    elements.append(Spacer(1, 10))

    # =========================================================
    # ETUDIANT
    # =========================================================
    if etudiant.date_naissance and etudiant.lieu_naissance:
        date_lieu = f"{safe_date(etudiant.date_naissance)} à {etudiant.lieu_naissance}"
    elif etudiant.date_naissance:
        date_lieu = safe_date(etudiant.date_naissance)
    else:
        date_lieu = "Non renseignée"

    etudiant_data = [
        ["Nom & Prénom", f"{etudiant.nom} {etudiant.prenoms}"[:21]],
        ["Matricule", etudiant.matricule],
        ["Date/lieu de naissance", date_lieu],
        ["Sexe", getattr(etudiant, "sexe", "")],
        ["Niveau", etudiant.get_niveau_display()],
        ["Filière", etudiant.filiere],
    ]

    HAUTEUR_HEADER = 3.3 * cm
    NB_LIGNES = len(etudiant_data)

    cadre_etudiant = Table(
        etudiant_data,
        colWidths=[4 * cm, 6.8 * cm],
        rowHeights=[HAUTEUR_HEADER / NB_LIGNES] * NB_LIGNES,
    )
    cadre_etudiant.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Courier-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))

    page_width = A4[0]
    usable_width = page_width - doc.leftMargin - doc.rightMargin

    header_global = Table(
        [[cadre_universite, cadre_etudiant]],
        colWidths=[usable_width * 0.45, usable_width * 0.55],
    )
    header_global.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    elements.append(header_global)
    elements.append(Spacer(1, 20))

    # =========================================================
    # TABLE BULLETIN
    # =========================================================

    data = [["CODE", "UE:UNITES D'ENSEIGNEMENTS", "ECUE", "CRÉDIT\nECUE",
              "CRÉDIT\nUE", "MOY\nECUE", "MOY\nUE", "DÉCISION"]]

    somme_generale = 0
    total_ue = 0
    ue_validees = 0
    ue_non_validees = 0
    credits_total = 0
    credits_obtenus = 0
    ecues_total = 0
    ecues_validees = 0
    ecues_non_validees = 0
    credits_ecue_total = 0
    credits_ecue_acquis = 0
    table_style = []

    # Accumulateurs de section
    section_credit_ecue = 0
    section_credit_ue = 0
    section_sum_moy_ue = 0
    section_count_ue = 0

    # BUG CORRIGÉ : les titres de section étaient codés en dur dans 3 appels
    # séparés à add_section, un par seuil. Comme l'ajout ne se déclenchait
    # QUE lorsqu'un seuil était atteint pendant la boucle, la toute
    # dernière section (celle qui reste accumulée après la fin de la
    # boucle "for ue in ues") n'était jamais ajoutée : ses lignes de notes
    # apparaissaient dans le tableau sans bandeau d'en-tête ni ligne de
    # sous-total. On utilise maintenant une liste ordonnée de titres et un
    # index, et on force l'ajout de la dernière section restante après la
    # boucle.
    SECTION_TITLES = [
        "UE : UNITÉS FONDAMENTALES",
        "UE : UNITES DE CULTURE GENERALES",
        "UE : UNITES DE SPECIALITES",
    ]
    section_index = 0

    def add_section(title, credit_ecue, credit_ue, moy_ue_section):
        row_index = len(data)
        moy_moyenne = round(moy_ue_section / section_count_ue, 2) if section_count_ue else 0
        data.append([
            Paragraph(f'<para align="LEFT" color="red"><b>{title}</b></para>', SMALL),
            "", "", credit_ecue, credit_ue, "-", moy_moyenne, "",
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

    # Avec 3 UE par section, les paliers corrects sont 4 (après les 3
    # premières UE), 7 (après les 6 premières) et 10 (après les 9 premières).
    SEUIL_FONDAMENTALES = 4
    SEUIL_CULTURE = 7
    SEUIL_SPECIALITES = 10

    def flush_section():
        """Ajoute la section accumulée courante et avance l'index de titre."""
        nonlocal section_credit_ecue, section_credit_ue, section_sum_moy_ue
        nonlocal section_count_ue, section_index
        title = (
            SECTION_TITLES[section_index]
            if section_index < len(SECTION_TITLES)
            else "UE : AUTRES"
        )
        add_section(title, section_credit_ecue, section_credit_ue, section_sum_moy_ue)
        section_credit_ecue = section_credit_ue = section_sum_moy_ue = 0
        section_count_ue = 0
        section_index += 1

    compteur_ue = 0
    for ue in ues:
        compteur_ue += 1

        if compteur_ue in (SEUIL_FONDAMENTALES, SEUIL_CULTURE, SEUIL_SPECIALITES):
            flush_section()

        ecues = ue.ecues.all()
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
                semestre=semestre,
                session=session,
            ).first()

            moy_ecue = float(note.moyenne) if note and note.moyenne is not None else 0.0

            credits_ecue_total += ecue.credit
            if moy_ecue >= 10:
                ecues_validees += 1
                credits_ecue_acquis += ecue.credit
            else:
                ecues_non_validees += 1

            credit_ecue = ecue.credit
            somme_ponderee += credit_ecue * moy_ecue
            credit_total_ue += credit_ecue

            somme_ue += moy_ecue
            count += 1

            lignes.append([
                ue.code if premiere_ligne else "",
                ue.libelle if premiere_ligne else "",
                ecue.libelle,
                ecue.credit,
                credit_ue,
                round(moy_ecue, 2),
                "",
                "",
            ])
            premiere_ligne = False

        if count == 0:
            continue

        moy_ue = round(somme_ponderee / credit_total_ue, 2) if credit_total_ue else round(somme_ue / count, 2)

        decision = (
            '<para align="center"><font color="green"><b>VALIDÉE</b></font></para>'
            if moy_ue >= 10
            else '<para align="center"><font color="red"><b>NON VALIDÉE</b></font></para>'
        )

        credits_total += credit_ue
        if moy_ue >= 10:
            ue_validees += 1
            credits_obtenus += credit_ue
        else:
            ue_non_validees += 1

        somme_generale += moy_ue
        total_ue += 1

        section_credit_ecue += credit_total_ue
        section_credit_ue += credit_ue
        section_sum_moy_ue += moy_ue
        section_count_ue += 1

        for r in lignes:
            r[6] = moy_ue
            r[7] = Paragraph(decision, SMALL)
            data.append(r)

    # BUG CORRIGÉ : on force l'ajout de la dernière section restante,
    # sinon les UE de la dernière tranche n'ont jamais de bandeau/sous-total.
    if section_count_ue > 0:
        flush_section()

    moyenne_generale = round(somme_generale / total_ue, 2) if total_ue else 0
    credits_restants = credits_total - credits_obtenus

    table = Table(
        data,
        colWidths=[1.4 * cm, 6 * cm, 6 * cm, 1.4 * cm, 1.4 * cm, 1.5 * cm, 1 * cm, 2.1 * cm],
        rowHeights=[30] + [15] * (len(data) - 1),
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ] + table_style))

    elements.append(table)
    elements.append(Spacer(1, 10))

    credits_ue_total = credits_total
    credits_ue_acquis = credits_obtenus
    credits_ue_restants = credits_ue_total - credits_ue_acquis
    credits_ecue_restants = credits_ecue_total - credits_ecue_acquis

    if credits_ue_restants == 0 and credits_ecue_restants == 0:
        decision_globale = '<para align="center"><font color="green"><b>ADMIS</b></font></para>'
    else:
        decision_globale = '<para align="center"><font color="red"><b>SESSION DE RATTRAPAGE</b></font></para>'

    recap_final_table = Table([
        [
            Paragraph("<b>Récapitulatif du travail</b>", SMALL),
            Paragraph("<b>Responsable</b>", SMALL),
            Paragraph("<b>Année de validation</b>", SMALL),
            Paragraph("<b>Décision</b>", SMALL),
        ],
        [
            Paragraph(f"""
                <para color="#1F4E79">
                Total ECUE validés : {ecues_validees}/{ecues_total}<br/>
                Total UE validées : {ue_validees}/{total_ue}<br/>
                Total crédits acquis : {credits_obtenus}/{credits_total}<br/>
                Total Crédits restants : {credits_restants}/{credits_total}<br/>
                Moyenne obtenue : {moyenne_generale}/20<br/>
                </para>
                """, SMALL),
            Paragraph("""Dr.JERRY TAFOTIE<br/><br/>M. N'GORAN CELESTIN""", SMALL),
            Paragraph(f"{annee}", SMALL),
            Paragraph(decision_globale, SMALL),
        ],
    ], colWidths=[7.5 * cm, 4 * cm, 5 * cm, 4 * cm], rowHeights=[0.8 * cm, 2.7 * cm])

    recap_final_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(recap_final_table)

    # =========================================================
    # SIGNATURE
    # =========================================================
    # NOTE : cette moyenne est calculée par un service externe
    # (calcul_moyenne_etudiant), potentiellement différent de
    # "moyenne_generale" calculée ci-dessus à partir des seules UE
    # "Gestion et Droit". Si les deux logiques de calcul diffèrent, la
    # décision cochée ici peut contredire la "DÉCISION GLOBALE" affichée
    # plus haut dans le récapitulatif. À vérifier selon la logique métier.
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

    decision_paragraph = Paragraph(f"""
        <b>DÉCISION</b><br/><br/>
        {decision}
        """, SMALL)

    visa_paragraph = Paragraph("""
        <b>VISA DU CHEF D'ÉTABLISSEMENT</b><br/><br/>
        """, SMALL)

    signature_table = Table(
        [[decision_paragraph, visa_paragraph]],
        colWidths=[8 * cm, 8 * cm],
        rowHeights=[3 * cm],
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
