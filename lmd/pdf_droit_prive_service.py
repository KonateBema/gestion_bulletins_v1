from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os
from .models import UE, ECUE, NoteLMD
from reportlab.platypus import HRFlowable
from .models import SaisieNoteLMD
from django.db.models import Prefetch
from reportlab.platypus import PageTemplate, Frame

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
    fontSize=6.4,
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


def generer_bulletin_droit_prive_pdf(etudiant, semestre, file_path):

    # Libellé affiché en haut du bulletin.
    session_label = "1"

    # La base contient des valeurs hétérogènes pour désigner la session
    # normale selon comment les notes ont été saisies ("1", "Normale",
    # "NORMALE", ...). On accepte donc toutes ces variantes au lieu
    # d'en imposer une seule, pour ne pas rater des notes existantes.
    SESSIONS_NORMALES = ["1", "2", "3", "4"]

    moyennes_ues = []  # une valeur par UE (moyenne pondérée des ECUE de cette UE)

    ues = (
        UE.objects
        .filter(
            filiere=etudiant.filiere,
            semestre=semestre,
            niveau=etudiant.niveau,
        )
        .select_related("grande_unite")
        .prefetch_related(
            Prefetch(
                "ecues",
                queryset=ECUE.objects.order_by("ordre"),
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
        bottomMargin=2.8 * cm,  # laisser la place au footer
    )


    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='normal',
    )

    doc.addPageTemplates([
        PageTemplate(id='main', frames=frame, onPage=add_footer)
    ])

    elements = []
    logo_path = os.path.join(settings.BASE_DIR, "core/static/logo.jpeg")
    logo = get_image(logo_path, 1.8 * cm, 1.8 * cm, "LOGO")

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
        ]
    ], colWidths=[7 * cm, 2.5 * cm, 7 * cm])

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
        niveau=etudiant.niveau,
    ).first()

    if semestre == "S1":
        libelle_semestre = "1"
    else:
        libelle_semestre = "2"

    annee = etudiant.annee_academique

    elements.append(Paragraph(f"""
        <para align="center">
        <b>
        <font color="#B30000">RELEVE DE NOTES</font>
        &nbsp;&nbsp;&nbsp;&nbsp;
        semestre {libelle_semestre} - SESSION {session_label}
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
        hAlign='CENTER',
    ))
    SMALL_INFO = ParagraphStyle( "SmallInfo", parent=styles["Normal"], fontName="Helvetica", fontSize=7, leading=9, )

    # En L1/L2, les étudiants sont en tronc commun (pas encore de
    # spécialisation) : on affiche "Tronc Commun" quel que soit le
    # libellé réel de la filière. À partir de L3, on affiche la
    # spécialité réelle de l'étudiant.
    if etudiant.niveau in ("L1", "L2"):
        specialite = "Tronc Commun"
    else:
        specialite = etudiant.filiere.libelle if etudiant.filiere else " DROIT PRIVE"

    cadre_universite = Table([[
        Paragraph(f"""
            <b>DOMAINE :  DROIT PRIVE</b><br/>
             <b></b><br/><br/>
             <b>SPECIALITE :</b> {specialite}<br/>
        """, SMALL)
    ]], colWidths=[8 * cm], rowHeights=[3.2* cm])

    cadre_universite.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 2), (-1, 2), 12),
         # TEXTE
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 16),
         # Décaler le premier cadre vers la gauche

    ]))

    elements.append(Spacer(1, 10))

    cadre_etudiant = Table([
        [Paragraph("<b>Nom et Prénoms</b>", SMALL_INFO),
         Paragraph(f"{etudiant.nom} {etudiant.prenoms}", SMALL_INFO)],
        [Paragraph("<b>Date et lieu de naissance</b>", SMALL_INFO),
         Paragraph(f"{safe_date(etudiant.date_naissance)} à {etudiant.lieu_naissance}", SMALL_INFO)],
        [Paragraph("<b>Sexe</b>", SMALL_INFO),
         Paragraph(etudiant.get_sexe_display(), SMALL_INFO)],
        [Paragraph("<b>Matricule</b>", SMALL_INFO),
         Paragraph(str(etudiant.matricule), SMALL_INFO)],
        [Paragraph("<b>Statut</b>", SMALL_INFO),
         Paragraph(etudiant.statut, SMALL_INFO)],
        [Paragraph("<b>Niveau</b>", SMALL),
         Paragraph(etudiant.get_niveau_display(), SMALL_INFO)],
    ], colWidths=[4.2 * cm, 4.3 * cm])

    cadre_etudiant.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), -2, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),

        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),

    ]))

    header_global = Table(
        [[cadre_universite, cadre_etudiant]],
        colWidths=[11 * cm, 7 * cm],
        rowHeights=[3.5 * cm],
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

    data = [["CODE", "UE:UNITES D'ENSEIGNEMENTS", "ECUE", "CRÉD\nECUE",
             "CRÉD\nUE", "MOY\nECUE", "MOY\nUE", "DÉCISION"]]
    table_style = []

    stats = {
        "ue_total": 0,
        "ue_validees": 0,
        "credits_total": 0,
        "credits_obtenus": 0,
        "ecues_total": 0,
        "ecues_validees": 0,
        "credits_ecue_total": 0,
        "credits_ecue_obtenus": 0,
    }

    grande_unite_actuelle = None

    # --- Accumulateurs pour la ligne récapitulative de la grande unité
    # en cours de traitement. IMPORTANT : le total "crédits ECUE" et le
    # total "crédits UE" sont deux sommes DIFFÉRENTES (elles ne
    # coïncident pas forcément), il faut donc les accumuler séparément.
    credits_ue_gu = 0     # somme des ue.credit de la grande unité en cours
    credits_ecue_gu = 0   # somme des ecue.credit de la grande unité en cours
    ponderation_gu = 0    # somme(moyenne_ue * credit_ue), pour la moyenne pondérée

    def inserer_ligne_grande_unite(grande_unite, credits_ue, credits_ecue, ponderation):
        """Ajoute la ligne récapitulative d'une grande unité (ex: UFO1,
        UCG2, USP3, ...) juste après les UE qui la composent, dans le
        style du bulletin papier : code, libellé, total crédits ECUE,
        total crédits UE, moyenne pondérée et décision. `data`/
        `table_style` sont capturés par closure."""
        if credits_ue == 0:
            return
        moyenne_gu = round(ponderation / credits_ue, 2)
        gu_validee = moyenne_gu >= 10
        if gu_validee:
            decision_gu = Paragraph("<font color='green'><b>Validée</b></font>", SMALL)
            couleur_gu = colors.green
        else:
            decision_gu = Paragraph("<font color='red'><b>Non validée</b></font>", SMALL)
            couleur_gu = colors.red

        code_gu = getattr(grande_unite, "code", grande_unite.nom)

        data.append([
            Paragraph(f"<b>{code_gu}</b>", SMALL),
            Paragraph(f"<b>UE : {grande_unite.nom}</b>", SMALL),
            "",
            Paragraph(f"<b>{credits_ecue:.2f}</b>", SMALL),
            Paragraph(f"<b>{credits_ue:.2f}</b>", SMALL),
            "",
            Paragraph(f"<b>{moyenne_gu:.2f}</b>", SMALL),
            decision_gu,
        ])
        ligne = len(data) - 1
        # IMPORTANT : le BACKGROUND doit être déclaré AVANT le SPAN,
        # sinon le fond ne s'affiche pas sur la ligne fusionnée.
        table_style.append(("BACKGROUND", (0, ligne), (7, ligne), colors.HexColor("#D9D9D9")))
        table_style.append(("SPAN", (1, ligne), (2, ligne)))
        table_style.append(("FONTNAME", (0, ligne), (7, ligne), "Helvetica-Bold"))
        table_style.append(("ALIGN", (0, ligne), (-1, ligne), "CENTER"))
        table_style.append(("TEXTCOLOR", (7, ligne), (7, ligne), couleur_gu))

    for ue in ues:

        ecues = ue.ecues.all()

        if not ecues.exists():
            continue

        stats["ue_total"] += 1
        stats["credits_total"] += ue.credit

        # Dès qu'on change de grande unité, on clôture la précédente par
        # sa ligne récapitulative (code, crédits, moyenne, décision).
        if ue.grande_unite != grande_unite_actuelle:
            if grande_unite_actuelle is not None:
                inserer_ligne_grande_unite(
                    grande_unite_actuelle, credits_ue_gu, credits_ecue_gu, ponderation_gu
                )
                credits_ue_gu = 0
                credits_ecue_gu = 0
                ponderation_gu = 0

            grande_unite_actuelle = ue.grande_unite

        ecue_data = []  # (ecue, moyenne) pour construire les lignes ensuite
        somme = 0
        coef = 0

        for ecue in ecues:
            note = NoteLMD.objects.filter(
                etudiant=etudiant,
                ecue=ecue,
                semestre__iexact=semestre,
                session__in=SESSIONS_NORMALES,
            ).first()

            moyenne = float(note.moyenne) if note and note.moyenne is not None else 0.0

            somme += moyenne * ecue.coefficient
            coef += ecue.coefficient

            stats["ecues_total"] += 1
            stats["credits_ecue_total"] += ecue.credit
            credits_ecue_gu += ecue.credit
            if moyenne >= 10:
                stats["ecues_validees"] += 1
                stats["credits_ecue_obtenus"] += ecue.credit

            ecue_data.append((ecue, moyenne))

        moyenne_ue = round(somme / coef, 2) if coef > 0 else 0
        moyennes_ues.append(moyenne_ue)  # une seule valeur par UE, correcte

        # accumulation pour la ligne récapitulative de la grande unité en cours
        credits_ue_gu += ue.credit
        ponderation_gu += moyenne_ue * ue.credit

        ue_validee = moyenne_ue >= 10
        if ue_validee:
            stats["ue_validees"] += 1
            stats["credits_obtenus"] += ue.credit
            decision = Paragraph("<font color='green'><b>VALIDÉE</b></font>", SMALL)
            couleur_decision = colors.green
        else:
            decision = Paragraph("<font color='red'><b>NON VALID</b></font>", SMALL)
            couleur_decision = colors.red

        # --- 2) On construit les lignes du tableau avec la moyenne UE finale ---
        lignes_ue = []
        premiere_ligne = True
        for ecue, moyenne in ecue_data:
            lignes_ue.append([
                Paragraph(ue.code if premiere_ligne else "", SMALL),
                Paragraph(ue.libelle if premiere_ligne else "", SMALL),
                Paragraph(ecue.libelle, SMALL),
                Paragraph(str(ecue.credit), SMALL),
                Paragraph(str(ue.credit) if premiere_ligne else "", SMALL),
                Paragraph(f"{moyenne:.2f}", SMALL),
                Paragraph(f"{moyenne_ue:.2f}" if premiere_ligne else "", SMALL),
                decision if premiere_ligne else "",
            ])
            premiere_ligne = False

        debut = len(data)
        data.extend(lignes_ue)
        fin = len(data) - 1

        # fusion des cellules communes à toute l'UE
        for col in [0, 1, 4, 6, 7]:
            table_style.append(("SPAN", (col, debut), (col, fin)))

        table_style.append(("TEXTCOLOR", (7, debut), (7, fin), couleur_decision))
        table_style.append(("FONTNAME", (7, debut), (7, fin), "Helvetica-Bold"))

    # Ligne récapitulative de la toute dernière grande unité : elle ne
    # passe jamais par le "if" de changement de grande unité ci-dessus,
    # donc on la clôture manuellement ici.
    if grande_unite_actuelle is not None:
        inserer_ligne_grande_unite(
            grande_unite_actuelle, credits_ue_gu, credits_ecue_gu, ponderation_gu
        )

    # Moyenne générale calculée dès maintenant pour pouvoir l'afficher à
    # la fois sur la ligne "TOTAL CREDITS ACQUIS" et dans le récapitulatif
    # final plus bas.
    moyenne_generale = (
        round(sum(moyennes_ues) / len(moyennes_ues), 2)
        if moyennes_ues
        else 0
    )

    # --- Ligne finale "TOTAL CREDITS ACQUIS" (TCA) ---
    # Comme pour les grandes unités, CRÉD ECUE et CRÉD UE sont deux
    # totaux distincts : la somme de tous les crédits ECUE d'un côté,
    # la somme de tous les crédits UE de l'autre.
    data.append([
        Paragraph("<b>TCA</b>", SMALL),
        Paragraph("<b>TOTAL CREDITS ACQUIS</b>", SMALL),
        "",
        Paragraph(f"<b>{stats['credits_ecue_total']:.2f}</b>", SMALL),
        Paragraph(f"<b>{stats['credits_total']:.2f}</b>", SMALL),
        "",
        Paragraph(f"<b>{moyenne_generale:.2f}</b>", SMALL),
        "",
    ])
    ligne_tca = len(data) - 1
    table_style.append(("SPAN", (1, ligne_tca), (2, ligne_tca)))
    table_style.append(("FONTNAME", (0, ligne_tca), (7, ligne_tca), "Helvetica-Bold"))
    table_style.append(("ALIGN", (0, ligne_tca), (-1, ligne_tca), "CENTER"))
    table_style.append(("BACKGROUND", (0, ligne_tca), (-1, ligne_tca), colors.lightgrey))

    table = Table(data, colWidths=[
        1.4 * cm,   # Code
        6 * cm,     # UE
        6 * cm,     # ECUE
        1.3 * cm,   # Crédit ECUE
        1.3 * cm,   # Crédit UE
        1.3 * cm,   # Moy ECUE
        1.3 * cm,   # Moy UE
        1.8 * cm,   # Décision
    ], rowHeights=[30] + [15] * (len(data) - 1))

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

    # =========================================================
    # Récapitulatif final
    # =========================================================
    credits_ue_total = stats["credits_total"]
    credits_ue_acquis = stats["credits_obtenus"]
    credits_ecue_total = stats["credits_ecue_total"]
    credits_ecue_acquis = stats["credits_ecue_obtenus"]

    credits_ue_restants = credits_ue_total - credits_ue_acquis
    credits_ecue_restants = credits_ecue_total - credits_ecue_acquis

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

    # moyenne_generale déjà calculée plus haut, réutilisée ici pour le récapitulatif

    recap_final_table = Table([
        [
            Paragraph("<b>Récapitulatif</b>", SMALL),
            Paragraph("<b>Responsable</b>", SMALL),
            Paragraph("<b>Année de validation</b>", SMALL),
            # Paragraph("<b>Décision</b>", SMALL),
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
                SMALL,
            ),
            Paragraph("""Dr.JERRY TAFOTIE<br/><br/>""", SMALL),
            Paragraph(f"{annee}", SMALL),
            # Paragraph(decision_globale, SMALL),
            # Paragraph("", SMALL),
        ]
    ], colWidths=[8.5 * cm, 6 * cm, 6 * cm, 4 * cm],
       rowHeights=[0.8 * cm, 2.7 * cm])

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

    signature_table = Table([[
        Paragraph("<b>DECISION</b><br/>", styles["Normal"]),
        Paragraph("<b>VISA DU CHEF D'ETABLISSEMENT</b><br/><br/>""<br/><br/>""", styles["Normal"]),
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

def generer_bulletin_lmd_pdf(etudiant, semestre, file_path):

    filiere = etudiant.filiere.libelle

    if filiere == "Droit Privé":
        from .pdf_droit_prive_service import generer_bulletin_droit_prive_pdf
        return generer_bulletin_droit_prive_pdf(etudiant, semestre, file_path)

    elif filiere == "Gestion et Droit":
        from .pdf_gestion_droit_service import generer_bulletin_gestion_droit_pdf
        return generer_bulletin_gestion_droit_pdf(etudiant, semestre, file_path)

    elif filiere == "Sciences de Gestion":
        from .pdf_sciences_gestion_service import generer_bulletin_sciences_gestion_pdf
        return generer_bulletin_sciences_gestion_pdf(etudiant, semestre, file_path)

    elif filiere == "Management QHSE":
        from .pdf_qhse_service import generer_bulletin_qhse_pdf
        return generer_bulletin_qhse_pdf(etudiant, semestre, file_path)

    else:
        raise ValueError(f"Aucun générateur PDF pour la filière {filiere}")