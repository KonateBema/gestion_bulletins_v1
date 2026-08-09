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
# lmd/views.py


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


def generer_bulletin_gestion_pdf(etudiant, semestre, file_path):

    # =========================================================
    # SESSIONS "NORMALES" ACCEPTÉES
    # =========================================================
    # La base contient des valeurs hétérogènes pour désigner la
    # session normale selon comment les notes ont été saisies
    # ("1", "Normale", "NORMALE", ...). On accepte donc toutes ces
    # variantes au lieu d'en imposer une seule, pour ne pas rater
    # des notes existantes (cf. bug déjà rencontré sur le bulletin
    # Droit Privé).
    SESSIONS_NORMALES = ["1", "Normale", "NORMALE", "normale"]

    # =========================================================
    # RÉCUPÉRATION DES UE / ECUE
    # =========================================================

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

    # =========================================================
    # DOCUMENT PDF
    # =========================================================

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=0.6 * cm,
        rightMargin=0.6 * cm,
        topMargin=0.6 * cm,
        bottomMargin=2.8 * cm,
    )

    from reportlab.platypus import PageTemplate, Frame

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal"
    )

    doc.addPageTemplates([
        PageTemplate(
            id="main",
            frames=frame,
            onPage=add_footer
        )
    ])

    elements = []

    # =========================================================
    # LOGO
    # =========================================================

    logo_path = os.path.join(
        settings.BASE_DIR,
        "core/static/logo.jpeg"
    )

    logo = get_image(
        logo_path,
        1.8 * cm,
        1.8 * cm,
        "LOGO"
    )

    # =========================================================
    # EN-TÊTE
    # =========================================================

    header_table = Table(
        [[
            Paragraph(
                """
                <para align="center">
                <b>
                <font color="#002147" size="8">
                MINISTÈRE DE L'ENSEIGNEMENT <br/>
                SUPÉRIEUR ET DE LA <br/>
                RECHERCHE SCIENTIFIQUE
                </font>
                </b>
                </para>
                """,
                SMALL
            ),

            logo,

            Paragraph(
                """
                <para align="center">
                <b>RÉPUBLIQUE DE CÔTE D'IVOIRE</b><br/>
                Union - Discipline - Travail
                </para>
                """,
                SMALL
            )
        ]],
        colWidths=[
            7 * cm,
            2.5 * cm,
            7 * cm
        ]
    )

    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    elements.append(header_table)
    elements.append(Spacer(1, 14))

    # =========================================================
    # SEMESTRE / SESSION
    # =========================================================

    session_label = "Normale"

    if semestre == "S1":
        libelle_semestre = "1er SEMESTRE"
    else:
        libelle_semestre = "2ème SEMESTRE"

    annee = etudiant.annee_academique

    elements.append(
        Paragraph(
            f"""
            <para align="center">
            <b>
            <font color="#B30000">
            RELEVE DE NOTES
            </font>
            &nbsp;&nbsp;&nbsp;&nbsp;
            {libelle_semestre}
            - SESSION {session_label}
            &nbsp;&nbsp;&nbsp;&nbsp;
            ANNÉE SCOLAIRE : {annee}
            </b>
            </para>
            """,
            SMALL
        )
    )

    elements.append(
        HRFlowable(
            width="40%",
            thickness=2,
            color=colors.HexColor("#B30000"),
            lineCap="round",
            spaceBefore=3,
            spaceAfter=10,
            hAlign="CENTER"
        )
    )

    # =========================================================
    # CADRE UNIVERSITÉ
    # =========================================================

    specialite = (
        etudiant.filiere.libelle
        if etudiant.filiere
        else "Sciences de Gestion"
    )

    cadre_universite = Table(
        [[
            Paragraph(
                f"""
                <b>DOMAINE :</b><br/>
                Sciences de Gestion
                <br/><br/>
                <b>SPECIALITE :</b><br/>
                {specialite}
                """,
                SMALL
            )
        ]],
        colWidths=[6 * cm],
        rowHeights=[3.5 * cm]
    )

    cadre_universite.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.whitesmoke
            ),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    # =========================================================
    # CADRE ÉTUDIANT
    # =========================================================

    cadre_etudiant = Table(
        [
            [
                Paragraph("<b>Nom et Prénoms</b>", SMALL),
                Paragraph(
                    f"{etudiant.nom} {etudiant.prenoms}",
                    SMALL
                )
            ],
            [
                Paragraph("<b>Date de naissance</b>", SMALL),
                Paragraph(
                    safe_date(etudiant.date_naissance),
                    SMALL
                )
            ],
            [
                Paragraph("<b>Sexe</b>", SMALL),
                Paragraph(
                    etudiant.get_sexe_display(),
                    SMALL
                )
            ],
            [
                Paragraph("<b>Matricule</b>", SMALL),
                Paragraph(
                    str(etudiant.matricule),
                    SMALL
                )
            ],
            [
                Paragraph("<b>Statut</b>", SMALL),
                Paragraph(
                    etudiant.statut,
                    SMALL
                )
            ],
            [
                Paragraph("<b>Niveau</b>", SMALL),
                Paragraph(
                    etudiant.get_niveau_display(),
                    SMALL
                )
            ],
        ],
        colWidths=[
            5 * cm,
            5.5 * cm
        ]
    )

    cadre_etudiant.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),
            ("FONTNAME", (0, 0), (-1, -1), "Courier"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ])
    )

    # =========================================================
    # CADRES UNIVERSITÉ + ÉTUDIANT
    # =========================================================

    header_global = Table(
        [[
            cadre_universite,
            cadre_etudiant
        ]],
        colWidths=[
            9 * cm,
            8 * cm
        ],
        rowHeights=[3.5 * cm]
    )

    header_global.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),

            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),

            # Décalage du cadre université vers la gauche
            ("LEFTPADDING", (0, 0), (0, 0), -90),
            ("RIGHTPADDING", (0, 0), (0, 0), 0),

            # Cadre étudiant
            ("LEFTPADDING", (1, 0), (1, 0), 0),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ])
    )

    elements.append(Spacer(1, 10))
    elements.append(header_global)
    elements.append(Spacer(1, 15))

    # =========================================================
    # TABLEAU DES NOTES
    # =========================================================

    data = [[
        "CODE",
        "UE:UNITES D'ENSEIGNEMENTS",
        "ECUE",
        "CRÉD\nECUE",
        "CRÉD\nUE",
        "MOY\nECUE",
        "MOY\nUE",
        "DÉCISION"
    ]]

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

    moyennes_ues = []

    grande_unite_actuelle = None

    # =========================================================
    # PARCOURS DES UE
    # =========================================================

    for ue in ues:

        ecues = list(ue.ecues.all())

        if not ecues:
            continue

        # -----------------------------------------------------
        # STATISTIQUES UE
        # -----------------------------------------------------

        stats["ue_total"] += 1
        stats["credits_total"] += ue.credit

        # -----------------------------------------------------
        # GRANDE UNITÉ
        # -----------------------------------------------------

        if ue.grande_unite != grande_unite_actuelle:

            grande_unite_actuelle = ue.grande_unite

            nom_grande_unite = (
                grande_unite_actuelle.nom
                if grande_unite_actuelle
                else ""
            )

            data.append([
                Paragraph(
                    f"<b>{nom_grande_unite}</b>",
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

            ligne = len(data) - 1

            table_style.append(
                ("SPAN", (0, ligne), (7, ligne))
            )

            table_style.append(
                (
                    "BACKGROUND",
                    (0, ligne),
                    (7, ligne),
                    colors.HexColor("#D9D9D9")
                )
            )

            table_style.append(
                (
                    "FONTNAME",
                    (0, ligne),
                    (7, ligne),
                    "Helvetica-Bold"
                )
            )

        # -----------------------------------------------------
        # CALCUL MOYENNE UE
        # -----------------------------------------------------

        somme = 0.0
        coef = 0.0

        lignes_ue = []

        # On stocke d'abord les informations
        # avant de calculer la moyenne finale de l'UE.

        notes_ecues = []

        for ecue in ecues:

            note = NoteLMD.objects.filter(
                etudiant=etudiant,
                ecue=ecue,
                semestre__iexact=semestre,
                session__in=SESSIONS_NORMALES,
            ).first()

            moyenne = (
                float(note.moyenne)
                if note and note.moyenne is not None
                else 0.0
            )

            notes_ecues.append(
                (ecue, moyenne)
            )

            # Moyenne pondérée par coefficient
            somme += moyenne * ecue.coefficient
            coef += ecue.coefficient

            # Statistiques ECUE
            stats["ecues_total"] += 1
            stats["credits_ecue_total"] += ecue.credit

            if moyenne >= 10:
                stats["ecues_validees"] += 1
                stats["credits_ecue_obtenus"] += ecue.credit

        # -----------------------------------------------------
        # MOYENNE FINALE UE
        # -----------------------------------------------------

        moyenne_ue = (
            round(somme / coef, 2)
            if coef > 0
            else 0
        )

        moyennes_ues.append(moyenne_ue)

        # -----------------------------------------------------
        # DÉCISION UE
        # -----------------------------------------------------

        if moyenne_ue >= 10:

            stats["ue_validees"] += 1
            stats["credits_obtenus"] += ue.credit

            decision = Paragraph(
                "<font color='green'><b>VALIDÉE</b></font>",
                SMALL
            )

            couleur_decision = colors.green

        else:

            decision = Paragraph(
                "<font color='red'><b>NON VALIDÉE</b></font>",
                SMALL
            )

            couleur_decision = colors.red

        # -----------------------------------------------------
        # CONSTRUCTION DES LIGNES
        # -----------------------------------------------------

        premiere_ligne = True

        for ecue, moyenne in notes_ecues:

            lignes_ue.append([
                Paragraph(
                    ue.code if premiere_ligne else "",
                    SMALL
                ),

                Paragraph(
                    ue.libelle if premiere_ligne else "",
                    SMALL
                ),

                Paragraph(
                    ecue.libelle,
                    SMALL
                ),

                Paragraph(
                    str(ecue.credit),
                    SMALL
                ),

                Paragraph(
                    str(ue.credit)
                    if premiere_ligne
                    else "",
                    SMALL
                ),

                Paragraph(
                    f"{moyenne:.2f}",
                    SMALL
                ),

                # IMPORTANT :
                # on met la moyenne FINALE de l'UE
                # uniquement sur la première ligne
                Paragraph(
                    f"{moyenne_ue:.2f}"
                    if premiere_ligne
                    else "",
                    SMALL
                ),

                # Décision sur la première ligne
                decision if premiere_ligne else ""
            ])

            premiere_ligne = False

        # =====================================================
        # AJOUT DES LIGNES
        # =====================================================

        debut = len(data)

        for ligne in lignes_ue:
            data.append(ligne)

        fin = len(data) - 1

        # =====================================================
        # FUSION DES CELLULES
        # =====================================================

        for col in [0, 1, 4, 6, 7]:

            table_style.append(
                (
                    "SPAN",
                    (col, debut),
                    (col, fin)
                )
            )

        # =====================================================
        # COULEUR DÉCISION
        # =====================================================

        table_style.append(
            (
                "TEXTCOLOR",
                (7, debut),
                (7, fin),
                couleur_decision
            )
        )

        table_style.append(
            (
                "FONTNAME",
                (7, debut),
                (7, fin),
                "Helvetica-Bold"
            )
        )

    # =========================================================
    # TABLEAU FINAL
    # =========================================================

    table = Table(
        data,
        colWidths=[
            1.4 * cm,   # Code
            5 * cm,     # UE
            7.2 * cm,   # ECUE
            1.1 * cm,   # Crédit ECUE
            1.1 * cm,   # Crédit UE
            1.5 * cm,   # Moy ECUE
            1.5 * cm,   # Moy UE
            1.8 * cm    # Décision
        ],
        rowHeights=[
            30
        ] + [
            15
        ] * (len(data) - 1)
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Courier"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                4
            ),

            (
                "ROUNDEDCORNERS",
                [6, 6, 6, 6]
            ),
        ] + table_style)
    )

    elements.append(table)
    elements.append(Spacer(1, 10))

    # =========================================================
    # STATISTIQUES FINALES
    # =========================================================

    credits_ue_total = stats["credits_total"]
    credits_ue_acquis = stats["credits_obtenus"]

    credits_ecue_total = stats["credits_ecue_total"]
    credits_ecue_acquis = stats["credits_ecue_obtenus"]

    credits_ue_restants = (
        credits_ue_total - credits_ue_acquis
    )

    credits_ecue_restants = (
        credits_ecue_total - credits_ecue_acquis
    )

    # =========================================================
    # DÉCISION GLOBALE
    # =========================================================

    if (
        credits_ue_restants == 0
        and credits_ecue_restants == 0
    ):

        decision_globale = (
            '<para align="center">'
            '<font color="green">'
            '<b>ADMIS</b>'
            '</font>'
            '</para>'
        )

    else:

        decision_globale = (
            '<para align="center">'
            '<font color="red">'
            '<b>SESSION DE RATTRAPAGE</b>'
            '</font>'
            '</para>'
        )

    # =========================================================
    # MOYENNE GÉNÉRALE
    # =========================================================

    moyenne_generale = (
        round(
            sum(moyennes_ues) / len(moyennes_ues),
            2
        )
        if moyennes_ues
        else 0
    )

    # =========================================================
    # RÉCAPITULATIF
    # =========================================================

    recap_final_table = Table(
        [
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
                    Total ECUE validés :
                    {stats["ecues_validees"]}/{stats["ecues_total"]}
                    <br/>

                    Total UE validées :
                    {stats["ue_validees"]}/{stats["ue_total"]}
                    <br/>

                    Total crédits acquis :
                    {credits_ue_acquis}/{credits_ue_total}
                    <br/>

                    Total crédits restants :
                    {credits_ue_restants}/{credits_ue_total}
                    <br/>

                    Moyenne obtenue :
                    {moyenne_generale}/20
                    <br/>
                    </para>
                    """,
                    SMALL
                ),

                Paragraph(
                    "Dr.JERRY TAFOTIE<br/><br/>",
                    SMALL
                ),

                Paragraph(
                    f"ANNÉE SCOLAIRE : {annee}",
                    SMALL
                ),

                Paragraph(
                    decision_globale,
                    SMALL
                ),
            ]
        ],

        colWidths=[
            8.5 * cm,
            4 * cm,
            4 * cm,
            4 * cm
        ],

        rowHeights=[
            0.8 * cm,
            2.7 * cm
        ]
    )

    recap_final_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#D9D9D9")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Courier"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, 0),
                "CENTER"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                11
            ),

            (
                "ROUNDEDCORNERS",
                [6, 6, 6, 6]
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
        ])
    )

    elements.append(recap_final_table)

    # =========================================================
    # SIGNATURE
    # =========================================================

    signature_table = Table(
        [[
            Paragraph(
                "<b>RESPONSABLE</b><br/>",
                styles["Normal"]
            ),

            Paragraph(
                "<b>VISA</b><br/><br/>"
                "Dr.JERRY TAFOTIE<br/><br/>",
                styles["Normal"]
            ),
        ]],
        colWidths=[
            8 * cm,
            8 * cm
        ],
        rowHeights=[3 * cm]
    )

    signature_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.whitesmoke
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LINEBEFORE",
                (1, 0),
                (1, -1),
                0.8,
                colors.HexColor("#333333")
            ),
        ])
    )

    elements.append(Spacer(1, 15))
    elements.append(signature_table)

    # =========================================================
    # GÉNÉRATION
    # =========================================================

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