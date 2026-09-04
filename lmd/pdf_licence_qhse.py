from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
    PageTemplate,
    Frame,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4

from django.conf import settings
from django.db.models import Prefetch

import os

from .models import UE, ECUE, NoteLMD, SaisieNoteLMD


# ============================================================
# OUTILS
# ============================================================

def safe_date(date):
    return date.strftime("%d/%m/%Y") if date else "Non renseignée"


def safe_text(value):
    """
    Évite les problèmes de valeurs None dans les Paragraph ReportLab.
    """
    return str(value) if value is not None else ""


styles = getSampleStyleSheet()


# ============================================================
# STYLES
# ============================================================

TITLE = ParagraphStyle(
    "TITLE",
    parent=styles["Normal"],
    fontSize=14,
    leading=16,
    alignment=1,
    spaceAfter=10,
    textColor=colors.HexColor("#1a1a1a"),
    fontName="Helvetica-Bold",
)


SMALL = ParagraphStyle(
    "SMALL",
    parent=styles["Normal"],
    fontSize=6.4,
    leading=10,
    fontName="Helvetica-Bold",
)


DECISION_SMALL = ParagraphStyle(
    "DECISION_SMALL",
    parent=SMALL,
    fontSize=6.5,
    leading=6,
)


SMALL_INFO = ParagraphStyle(
    "SmallInfo",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7,
    leading=9,
)


# ============================================================
# IMAGE
# ============================================================

def get_image(path, width, height, fallback):
    if path and os.path.exists(path):
        return Image(path, width=width, height=height)

    return Paragraph(fallback, SMALL)


# ============================================================
# FOOTER
# ============================================================

def add_footer(canvas, doc):
    canvas.saveState()

    width, height = A4

    footer_text = [
        "UNIVERSITÉ INTERNATIONALE DE COCODY",
        "Arrêté n°487/MESRS/DGSE du 29/12/2015",
        "Siège Social : Cocody 2 Plateaux, Teme Tranche non loin du café de Versailles",
        "04 B.P ABJ 04, Côte d'Ivoire",
        "Email : uicinfos@gmail.com | Tel : (+225) 27 22 52 28 84 - 07 78 63 74 00",
    ]

    y = 2.2 * cm

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)

    for line in footer_text:
        canvas.drawCentredString(width / 2, y, line)
        y -= 0.35 * cm

    canvas.restoreState()


# ============================================================
# DÉCISION ECUE
# ============================================================

def decision_ecue_paragraph(moyenne, ue_validee):
    """
    Retourne :
        Paragraph,
        couleur,
        acquise,
        compensee

    Règles :

    moyenne >= 10
        -> Validée

    moyenne < 10 mais UE validée
        -> Compensée

    moyenne < 10 et UE non validée
        -> Non validée
    """

    if moyenne >= 10:

        return (
            Paragraph(
                "<font color='green'><b>Validée</b></font>",
                DECISION_SMALL,
            ),
            colors.green,
            True,
            False,
        )

    elif ue_validee:

        return (
            Paragraph(
                "<font color='#B8860B'><b>Compensée</b></font>",
                DECISION_SMALL,
            ),
            colors.HexColor("#B8860B"),
            True,
            True,
        )

    else:

        return (
            Paragraph(
                "<font color='red'><b>Non validée</b></font>",
                DECISION_SMALL,
            ),
            colors.red,
            False,
            False,
        )


# ============================================================
# SESSIONS NORMALES
# ============================================================

SESSIONS_NORMALES_RANG = ["1", "2", "3", "4"]


# ============================================================
# CALCUL MOYENNE GÉNÉRALE
# ============================================================

def calculer_moyenne_generale_etudiant(etudiant, semestre):
    """
    Calcule la moyenne générale d'un étudiant.

    Logique :

    1. Moyenne de chaque ECUE pondérée par son coefficient.
    2. Moyenne de l'UE.
    3. Moyenne simple des UE.
    """

    saisie = SaisieNoteLMD.objects.filter(
        filiere=etudiant.filiere,
        niveau=etudiant.niveau,
    ).first()

    semestre_resolu = saisie.semestre if saisie else semestre

    ues = (
        UE.objects
        .filter(
            filiere=etudiant.filiere,
            semestre=semestre_resolu,
            niveau=etudiant.niveau,
        )
        .prefetch_related(
            Prefetch(
                "ecues",
                queryset=ECUE.objects.order_by("ordre"),
            )
        )
        .order_by(
            "grande_unite__ordre",
            "ordre",
        )
    )

    moyennes_ues = []

    for ue in ues:

        ecues = ue.ecues.all()

        if not ecues.exists():
            continue

        somme = 0
        coef = 0

        for ecue in ecues:

            note = NoteLMD.objects.filter(
                etudiant=etudiant,
                ecue=ecue,
                semestre__iexact=semestre_resolu,
                session__in=SESSIONS_NORMALES_RANG,
            ).first()

            moyenne = (
                float(note.moyenne)
                if note and note.moyenne is not None
                else 0.0
            )

            coefficient = float(ecue.coefficient or 0)

            somme += moyenne * coefficient
            coef += coefficient

        moyenne_ue = (
            round(somme / coef, 2)
            if coef > 0
            else 0
        )

        moyennes_ues.append(moyenne_ue)

    if not moyennes_ues:
        return 0

    return round(
        sum(moyennes_ues) / len(moyennes_ues),
        2,
    )


# ============================================================
# CALCUL DU RANG
# ============================================================

def calculer_rang_etudiant(etudiant, semestre, moyenne_etudiant):

    from .models import EtudiantLMD

    camarades = (
        EtudiantLMD.objects
        .filter(
            filiere=etudiant.filiere,
            niveau=etudiant.niveau,
            annee_academique=etudiant.annee_academique,
        )
        .exclude(pk=etudiant.pk)
    )

    moyennes_autres = [
        calculer_moyenne_generale_etudiant(
            camarade,
            semestre,
        )
        for camarade in camarades
    ]

    effectif = len(moyennes_autres) + 1

    rang = 1 + sum(
        1
        for moyenne in moyennes_autres
        if moyenne > moyenne_etudiant
    )

    return rang, effectif


# ============================================================
# GÉNÉRATION BULLETIN GESTION ET DROIT
# ============================================================

def generer_bulletin_qhse_pdf(etudiant, semestre, file_path):
    """
    Génère le bulletin PDF.

    La logique de calcul est conservée :
    - résolution du semestre via SaisieNoteLMD ;
    - UE filtrées par filière, niveau et semestre ;
    - ECUE pondérées par coefficient ;
    - compensation ;
    - grandes unités ;
    - crédits ;
    - moyenne générale ;
    - rang ;
    - décision finale.
    """

    session_label = "1"

    SESSIONS_NORMALES = [
        "1",
        "2",
        "3",
        "4",
    ]

    moyennes_ues = []

    compensation_utilisee = False

    # ========================================================
    # RÉSOLUTION DU SEMESTRE
    # ========================================================

    saisie = SaisieNoteLMD.objects.filter(
        filiere=etudiant.filiere,
        niveau=etudiant.niveau,
    ).first()

    semestre_resolu = (
        saisie.semestre
        if saisie
        else semestre
    )

    session = (
        saisie.session
        if saisie
        else session_label
    )

    # ========================================================
    # RÉCUPÉRATION DES UE
    # ========================================================

    ues = (
        UE.objects
        .filter(
            filiere=etudiant.filiere,
            semestre=semestre_resolu,
            niveau=etudiant.niveau,
        )
        .select_related("grande_unite")
        .prefetch_related(
            Prefetch(
                "ecues",
                queryset=ECUE.objects.order_by("ordre"),
            )
        )
        .order_by(
            "grande_unite__ordre",
            "ordre",
        )
    )

    # ========================================================
    # DOCUMENT
    # ========================================================

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=0.6 * cm,
        rightMargin=0.6 * cm,
        topMargin=0.6 * cm,
        bottomMargin=2.8 * cm,
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )

    doc.addPageTemplates([
        PageTemplate(
            id="main",
            frames=frame,
            onPage=add_footer,
        )
    ])

    elements = []

    # ========================================================
    # CONSTANTES DE MISE EN PAGE
    # ========================================================

    LARGEUR_BULLETIN = 19.6 * cm
    HAUTEUR_ENTETE = 3 * cm

    # ========================================================
    # EN-TÊTE RÉPUBLIQUE
    # ========================================================

    logo_path = os.path.join(
        settings.BASE_DIR,
        "core/static/logo.jpeg",
    )

    logo = get_image(
        logo_path,
        3.2 * cm,
        3.2 * cm,
        "LOGO",
    )

    header_table = Table(
        [[
            Paragraph(
                """
                <para align="center">
                    <b>
                        <font color="#002147" size="6.5">
                            MINISTÈRE DE L'ENSEIGNEMENT
                            <br/>
                            SUPÉRIEUR
                            <br/>
                            ET DE LA
                            <br/>
                            RECHERCHE SCIENTIFIQUE
                        </font>
                    </b>
                </para>
                """,
                SMALL,
            ),

            logo,

            Paragraph(
                """
                <para align="center">
                    <b>
                        <font size="8">
                            RÉPUBLIQUE DE CÔTE D'IVOIRE
                        </font>
                    </b>
                    <br/>
                    <font size="7">
                        Union - Discipline - Travail
                    </font>
                </para>
                """,
                SMALL,
            ),
        ]],
        colWidths=[
            6.5 * cm,
            3.6 * cm,
            6.5 * cm,
        ],
    )

    header_table.setStyle(TableStyle([
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (0, 0),
            0,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (0, 0),
            40,
        ),

        (
            "LEFTPADDING",
            (1, 0),
            (1, 0),
            0,
        ),

        (
            "RIGHTPADDING",
            (1, 0),
            (1, 0),
            0,
        ),

        (
            "LEFTPADDING",
            (2, 0),
            (2, 0),
            40,
        ),

        (
            "RIGHTPADDING",
            (2, 0),
            (2, 0),
            0,
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),
    ]))

    elements.append(header_table)

    elements.append(
        Spacer(1, 6)
    )

    # ========================================================
    # ANNÉE
    # ========================================================

    annee = etudiant.annee_academique

    if semestre_resolu == "S1":
        libelle_semestre = "1"
    else:
        libelle_semestre = "2"

    elements.append(
        Paragraph(
            f"""
            <para align="center">
                <b>
                    <font color="#B30000">
                        RELEVE DE NOTES
                    </font>

                    &nbsp;&nbsp;&nbsp;&nbsp;

                    semestre {libelle_semestre}
                    - SESSION {session}

                    &nbsp;&nbsp;&nbsp;&nbsp;

                    ANNÉE SCOLAIRE : {safe_text(annee)}
                </b>
            </para>
            """,
            SMALL,
        )
    )

    # ========================================================
    # LIGNE ROUGE
    # ========================================================

    elements.append(
        HRFlowable(
            width=LARGEUR_BULLETIN,
            thickness=2,
            color=colors.HexColor("#B30000"),
            lineCap="round",
            spaceBefore=3,
            spaceAfter=8,
            hAlign="LEFT",
        )
    )

    # ========================================================
    # DOMAINE / SPÉCIALITÉ
    # ========================================================

    specialite = (
        etudiant.filiere.libelle
        if etudiant.filiere
        else "GESTION ET DROIT"
    )

    domaine = "SCIENCES ECONOMIQUES &amp; DE GESTION"

    # ========================================================
    # CADRE UNIVERSITÉ
    # ========================================================

    cadre_universite = Table(
        [[
            Paragraph(
                f"""
                <para align="left">
                    <b>
                        <font size="7.5">
                            DOMAINE : {domaine}
                        </font>
                    </b>

                    <br/><br/>

                    <b>
                        <font size="7.5">
                            SPECIALITE :
                        </font>
                    </b>

                    <font size="7.5">
                        {safe_text(specialite).upper()}
                    </font>
                </para>
                """,
                SMALL,
            )
        ]],
        colWidths=[8.2 * cm],
        rowHeights=[HAUTEUR_ENTETE],
    )

    cadre_universite.setStyle(TableStyle([
        (
            "BOX",
            (0, 0),
            (-1, -1),
            1,
            colors.black,
        ),

        (
            "BACKGROUND",
            (0, 0),
            (-1, -1),
            colors.whitesmoke,
        ),

        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "LEFT",
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            8,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),

        (
            "ROUNDEDCORNERS",
            [6, 6, 6, 6],
        ),
    ]))

    # ========================================================
    # CADRE ÉTUDIANT
    # ========================================================

    cadre_etudiant = Table(
        [
            [
                Paragraph(
                    "<b>Nom et Prénoms</b>",
                    SMALL,
                ),
                Paragraph(
                    f"{safe_text(etudiant.nom)} "
                    f"{safe_text(etudiant.prenoms)}",
                    SMALL,
                ),
            ],

            [
                Paragraph(
                    "<b>Date de naissance</b>",
                    SMALL,
                ),
                Paragraph(
                    safe_date(etudiant.date_naissance),
                    SMALL,
                ),
            ],

            [
                Paragraph(
                    "<b>Sexe</b>",
                    SMALL,
                ),
                Paragraph(
                    safe_text(
                        etudiant.get_sexe_display()
                    ),
                    SMALL,
                ),
            ],

            [
                Paragraph(
                    "<b>Matricule</b>",
                    SMALL,
                ),
                Paragraph(
                    safe_text(etudiant.matricule),
                    SMALL,
                ),
            ],

            [
                Paragraph(
                    "<b>Statut</b>",
                    SMALL,
                ),
                Paragraph(
                    safe_text(etudiant.statut),
                    SMALL,
                ),
            ],

            [
                Paragraph(
                    "<b>Niveau</b>",
                    SMALL,
                ),
                Paragraph(
                    safe_text(
                        etudiant.get_niveau_display()
                    ),
                    SMALL,
                ),
            ],
        ],

        colWidths=[
            4 * cm,
            6.4 * cm,
        ],

        rowHeights=[
            HAUTEUR_ENTETE / 6
        ] * 6,
    )

    cadre_etudiant.setStyle(TableStyle([
        (
            "BOX",
            (0, 0),
            (-1, -1),
            1,
            colors.black,
        ),

        (
            "BACKGROUND",
            (0, 0),
            (0, -1),
            colors.lightgrey,
        ),

        (
            "FONTNAME",
            (0, 0),
            (-1, -1),
            "Helvetica",
        ),

        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            7,
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "LEFT",
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            1.5,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            1.5,
        ),

        (
            "ROUNDEDCORNERS",
            [6, 6, 6, 6],
        ),
    ]))

    # ========================================================
    # EN-TÊTE GLOBAL
    # ========================================================

    header_global = Table(
        [[
            cadre_universite,
            cadre_etudiant,
        ]],

        colWidths=[
            9.2 * cm,
            8.4 * cm,
        ],

        rowHeights=[
            HAUTEUR_ENTETE
        ],

        hAlign="LEFT",
    )

    header_global.setStyle(TableStyle([
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "LEFT",
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            0,
        ),
    ]))

    elements.append(header_global)

    elements.append(
        Spacer(1, 10)
    )

    # ========================================================
    # TABLEAU BULLETIN
    # ========================================================

    data = [
        [
            "CODE",
            "UE:UNITES D'ENSEIGNEMENTS",
            "ECUE",
            "CRÉD\nECUE",
            "CRÉD\nUE",
            "MOY\nECUE",
            "MOY\nUE",
            "DÉCISION",
        ]
    ]

    table_style = []

    # ========================================================
    # STATISTIQUES
    # ========================================================

    stats = {
        "ue_total": 0,
        "ue_validees": 0,
        "credits_total": 0,
        "credits_obtenus": 0,

        "ecues_total": 0,
        "ecues_validees": 0,

        "credits_ecue_total": 0,
        "credits_ecue_obtenus": 0,

        "gu_total": 0,
        "gu_validees": 0,
    }

    # ========================================================
    # GRANDE UNITÉ
    # ========================================================

    grande_unite_actuelle = None

    credits_ue_gu = 0
    credits_ecue_gu = 0
    ponderation_gu = 0

    def inserer_ligne_grande_unite(
        grande_unite,
        credits_ue,
        credits_ecue,
        ponderation,
    ):
        """
        Ajoute la ligne récapitulative de la grande unité.
        """

        if credits_ue == 0:
            return

        moyenne_gu = round(
            ponderation / credits_ue,
            2,
        )

        gu_validee = moyenne_gu >= 10

        stats["gu_total"] += 1

        if gu_validee:
            stats["gu_validees"] += 1

        if gu_validee:

            decision_gu = Paragraph(
                "<font color='green'><b>Validée</b></font>",
                DECISION_SMALL,
            )

            couleur_gu = colors.green

        else:

            decision_gu = Paragraph(
                "<font color='red'><b>Non validée</b></font>",
                DECISION_SMALL,
            )

            couleur_gu = colors.red

        code_gu = (
            getattr(grande_unite, "code", None)
            or getattr(grande_unite, "nom", "")
        )

        data.append([
            Paragraph(
                f"<b>{safe_text(code_gu)}</b>",
                SMALL,
            ),

            Paragraph(
                f"<b>UE : "
                f"{safe_text(grande_unite.nom)}</b>",
                SMALL,
            ),

            "",

            Paragraph(
                f"<b>{credits_ecue:.2f}</b>",
                SMALL,
            ),

            Paragraph(
                f"<b>{credits_ue:.2f}</b>",
                SMALL,
            ),

            "",

            Paragraph(
                f"<b>{moyenne_gu:.2f}</b>",
                SMALL,
            ),

            decision_gu,
        ])

        ligne = len(data) - 1

        table_style.append(
            (
                "BACKGROUND",
                (0, ligne),
                (7, ligne),
                colors.HexColor("#D9D9D9"),
            )
        )

        table_style.append(
            (
                "SPAN",
                (1, ligne),
                (2, ligne),
            )
        )

        table_style.append(
            (
                "FONTNAME",
                (0, ligne),
                (7, ligne),
                "Helvetica-Bold",
            )
        )

        table_style.append(
            (
                "ALIGN",
                (0, ligne),
                (-1, ligne),
                "CENTER",
            )
        )

        table_style.append(
            (
                "TEXTCOLOR",
                (7, ligne),
                (7, ligne),
                couleur_gu,
            )
        )

    # ========================================================
    # PARCOURS DES UE
    # ========================================================

    for ue in ues:

        ecues = ue.ecues.all()

        if not ecues.exists():
            continue

        stats["ue_total"] += 1

        credit_ue = float(
            ue.credit or 0
        )

        stats["credits_total"] += credit_ue

        # ----------------------------------------------------
        # CHANGEMENT DE GRANDE UNITÉ
        # ----------------------------------------------------

        if ue.grande_unite != grande_unite_actuelle:

            if grande_unite_actuelle is not None:

                inserer_ligne_grande_unite(
                    grande_unite_actuelle,
                    credits_ue_gu,
                    credits_ecue_gu,
                    ponderation_gu,
                )

                credits_ue_gu = 0
                credits_ecue_gu = 0
                ponderation_gu = 0

            grande_unite_actuelle = ue.grande_unite

        # ----------------------------------------------------
        # CALCUL UE
        # ----------------------------------------------------

        ecue_data = []

        somme = 0
        coef = 0

        for ecue in ecues:

            note = NoteLMD.objects.filter(
                etudiant=etudiant,
                ecue=ecue,
                semestre__iexact=semestre_resolu,
                session__in=SESSIONS_NORMALES,
            ).first()

            moyenne = (
                float(note.moyenne)
                if note and note.moyenne is not None
                else 0.0
            )

            coefficient = float(
                ecue.coefficient or 0
            )

            somme += (
                moyenne * coefficient
            )

            coef += coefficient

            stats["ecues_total"] += 1

            ecue_data.append(
                (
                    ecue,
                    moyenne,
                )
            )

        moyenne_ue = (
            round(somme / coef, 2)
            if coef > 0
            else 0
        )

        moyennes_ues.append(
            moyenne_ue
        )

        # ----------------------------------------------------
        # GRANDE UNITÉ
        # ----------------------------------------------------

        credits_ue_gu += credit_ue

        ponderation_gu += (
            moyenne_ue * credit_ue
        )

        # ----------------------------------------------------
        # VALIDATION UE
        # ----------------------------------------------------

        ue_validee = moyenne_ue >= 10

        if ue_validee:

            stats["ue_validees"] += 1

            stats["credits_obtenus"] += (
                credit_ue
            )

        # ----------------------------------------------------
        # LIGNES ECUE
        # ----------------------------------------------------

        lignes_ue = []

        premiere_ligne = True

        for ecue, moyenne in ecue_data:

            (
                decision_ecue,
                couleur_ecue,
                ecue_acquise,
                ecue_compensee,
            ) = decision_ecue_paragraph(
                moyenne,
                ue_validee,
            )

            credit_ecue_affiche = (
                float(ecue.credit or 0)
                if ecue_acquise
                else 0
            )

            if ecue_acquise:

                stats["ecues_validees"] += 1

            stats["credits_ecue_obtenus"] += (
                credit_ecue_affiche
            )

            stats["credits_ecue_total"] += (
                credit_ecue_affiche
            )

            credits_ecue_gu += (
                credit_ecue_affiche
            )

            if ecue_compensee:
                compensation_utilisee = True

            lignes_ue.append([
                Paragraph(
                    safe_text(ue.code)
                    if premiere_ligne
                    else "",
                    SMALL,
                ),

                Paragraph(
                    safe_text(ue.libelle)
                    if premiere_ligne
                    else "",
                    SMALL,
                ),

                Paragraph(
                    safe_text(ecue.libelle),
                    SMALL,
                ),

                Paragraph(
                    f"{credit_ecue_affiche:.2f}",
                    SMALL,
                ),

                Paragraph(
                    f"{credit_ue:.2f}"
                    if premiere_ligne
                    else "",
                    SMALL,
                ),

                Paragraph(
                    f"{moyenne:.2f}",
                    SMALL,
                ),

                Paragraph(
                    f"{moyenne_ue:.2f}"
                    if premiere_ligne
                    else "",
                    SMALL,
                ),

                decision_ecue,
            ])

            premiere_ligne = False

        debut = len(data)

        data.extend(
            lignes_ue
        )

        fin = len(data) - 1

        # Fusion UE / code / crédits / moyenne UE

        for col in [
            0,
            1,
            4,
            6,
        ]:

            table_style.append(
                (
                    "SPAN",
                    (col, debut),
                    (col, fin),
                )
            )

    # ========================================================
    # DERNIÈRE GRANDE UNITÉ
    # ========================================================

    if grande_unite_actuelle is not None:

        inserer_ligne_grande_unite(
            grande_unite_actuelle,
            credits_ue_gu,
            credits_ecue_gu,
            ponderation_gu,
        )

    # ========================================================
    # MOYENNE GÉNÉRALE
    # ========================================================

    moyenne_generale = (
        round(
            sum(moyennes_ues)
            / len(moyennes_ues),
            2,
        )
        if moyennes_ues
        else 0
    )

    # ========================================================
    # RANG
    # ========================================================

    rang_etudiant, effectif_classe = (
        calculer_rang_etudiant(
            etudiant,
            semestre_resolu,
            moyenne_generale,
        )
    )

    # ========================================================
    # TCA
    # ========================================================

    data.append([
        Paragraph(
            "<b>TCA</b>",
            SMALL,
        ),

        Paragraph(
            "<b>TOTAL CREDITS ACQUIS</b>",
            SMALL,
        ),

        "",

        Paragraph(
            f"<b>"
            f"{stats['credits_ecue_obtenus']:.2f}"
            f"</b>",
            SMALL,
        ),

        Paragraph(
            f"<b>"
            f"{stats['credits_total']:.2f}"
            f"</b>",
            SMALL,
        ),

        "",

        Paragraph(
            f"<b>"
            f"{moyenne_generale:.2f}"
            f"</b>",
            SMALL,
        ),

        "",
    ])

    ligne_tca = len(data) - 1

    table_style.append(
        (
            "SPAN",
            (1, ligne_tca),
            (2, ligne_tca),
        )
    )

    table_style.append(
        (
            "FONTNAME",
            (0, ligne_tca),
            (7, ligne_tca),
            "Helvetica-Bold",
        )
    )

    table_style.append(
        (
            "ALIGN",
            (0, ligne_tca),
            (-1, ligne_tca),
            "CENTER",
        )
    )

    table_style.append(
        (
            "BACKGROUND",
            (0, ligne_tca),
            (-1, ligne_tca),
            colors.lightgrey,
        )
    )

    # ========================================================
    # TABLEAU FINAL
    # ========================================================

    table = Table(
        data,
        colWidths=[
            1.3 * cm,
            5.1 * cm,
            6.0 * cm,
            1.2 * cm,
            1.2 * cm,
            1.2 * cm,
            1.2 * cm,
            2.4 * cm,
        ],
        rowHeights=[
            30
        ] + [
            15
        ] * (
            len(data) - 1
        ),
    )

    table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.black,
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey,
            ),

            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica",
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),

            (
                "ROUNDEDCORNERS",
                [6, 6, 6, 6],
            ),
        ] + table_style)
    )

    elements.append(table)

    elements.append(
        Spacer(1, 10)
    )

    # ========================================================
    # RÉCAPITULATIF
    # ========================================================

    credits_ue_total = (
        stats["credits_total"]
    )

    credits_ue_acquis = (
        stats["credits_obtenus"]
    )

    credits_ecue_total = (
        stats["credits_ecue_total"]
    )

    credits_ecue_acquis = (
        stats["credits_ecue_obtenus"]
    )

    credits_ue_restants = (
        credits_ue_total
        - credits_ue_acquis
    )

    credits_ecue_restants = (
        credits_ecue_total
        - credits_ecue_acquis
    )

    # ========================================================
    # DÉCISION FINALE
    # ========================================================

    donnees_presentes = (
        stats["ue_total"] > 0
        and stats["ecues_total"] > 0
    )

    admis = (
        donnees_presentes
        and credits_ue_restants == 0
        and credits_ecue_restants == 0
    )

    if not donnees_presentes:

        decision_globale = (
            "<para align='center'>"
            "<font color='red'>"
            "<b>AUCUNE NOTE SAISIE</b>"
            "</font>"
            "</para>"
        )

        decision_globale_inline = (
            "<font color='red'>"
            "<b>AUCUNE NOTE SAISIE</b>"
            "</font>"
        )

    elif not admis:

        decision_globale = (
            "<para align='center'>"
            "<font color='red'>"
            "<b>NON VALIDÉE</b>"
            "</font>"
            "</para>"
        )

        decision_globale_inline = (
            "<font color='red'>"
            "<b>NON VALIDÉE</b>"
            "</font>"
        )

    elif compensation_utilisee:

        decision_globale = (
            "<para align='center'>"
            "<font color='#B8860B'>"
            "<b>VALIDÉE PAR COMPENSATION</b>"
            "</font>"
            "</para>"
        )

        decision_globale_inline = (
            "<font color='#B8860B'>"
            "<b>VALIDÉE PAR COMPENSATION</b>"
            "</font>"
        )

    else:

        decision_globale = (
            "<para align='center'>"
            "<font color='green'>"
            "<b>VALIDÉE AU COMPLET</b>"
            "</font>"
            "</para>"
        )

        decision_globale_inline = (
            "<font color='green'>"
            "<b>VALIDÉE AU COMPLET</b>"
            "</font>"
        )

    # ========================================================
    # STATISTIQUES RÉCAP
    # ========================================================

    ecues_total = stats["ecues_total"]
    ecues_validees = stats["ecues_validees"]

    gu_total = stats["gu_total"]
    gu_validees = stats["gu_validees"]

    credits_total = stats["credits_total"]
    credits_obtenus = stats["credits_obtenus"]

    credits_restants = (
        credits_total
        - credits_obtenus
    )

    # ========================================================
    # STYLE RESPONSABLE
    # ========================================================

    RESPONSABLE_STYLE = ParagraphStyle(
        "ResponsableStyle",
        parent=SMALL,
        alignment=1,
        fontSize=7,
        leading=10,
    )

    # ========================================================
    # TABLEAU RÉCAPITULATIF
    # ========================================================

    recap_final_table = Table(
        [
            [
                Paragraph(
                    "<b>Récapitulatif</b>",
                    SMALL,
                ),

                Paragraph(
                    "<b>Responsable</b>",
                    SMALL,
                ),

                Paragraph(
                    "<b>Année de validation</b>",
                    SMALL,
                ),

                Paragraph(
                    "<b>Décision</b>",
                    SMALL,
                ),
            ],

            [
                Paragraph(
                    f"""
                    <para color="#1F4E79">
                        Total ECUE validés :
                        {ecues_validees}/{ecues_total}
                        <br/>

                        Total UE validées :
                        {gu_validees}/{gu_total}
                        <br/>

                        Total crédits acquis :
                        {credits_obtenus:.2f}/{credits_total:.2f}
                        <br/>

                        Total Crédits restants :
                        {credits_restants:.2f}/{credits_total:.2f}
                        <br/>

                        Moyenne obtenue :
                        {moyenne_generale:.2f}/20
                        <br/>

                        Rang :
                        {rang_etudiant}e / {effectif_classe}
                    </para>
                    """,
                    SMALL,
                ),

                Paragraph(
                    "Dr.JERRY TAFOTIE",
                    RESPONSABLE_STYLE,
                ),

                Paragraph(
                    f"{safe_text(annee)}",
                    SMALL,
                ),

                Paragraph(
                    decision_globale,
                    DECISION_SMALL,
                ),
            ],
        ],

        colWidths=[
            8.5 * cm,
            6.5 * cm,
            4.5 * cm,
        ],
    )

    # --------------------------------------------------------
    # IMPORTANT :
    # Le tableau possède 4 colonnes.
    # On utilise donc une largeur totale cohérente de 19.5 cm.
    # --------------------------------------------------------

    recap_final_table = Table(
        [
            [
                Paragraph(
                    "<b>Récapitulatif</b>",
                    SMALL,
                ),

                Paragraph(
                    "<b>Responsable</b>",
                    SMALL,
                ),

                Paragraph(
                    "<b>Année de validation</b>",
                    SMALL,
                ),

                Paragraph(
                    "<b>Décision</b>",
                    SMALL,
                ),
            ],

            [
                Paragraph(
                    f"""
                    <para color="#1F4E79">
                        Total ECUE validés :
                        {ecues_validees}/{ecues_total}
                        <br/>

                        Total UE validées :
                        {gu_validees}/{gu_total}
                        <br/>

                        Total crédits acquis :
                        {credits_obtenus:.2f}/{credits_total:.2f}
                        <br/>

                        Total Crédits restants :
                        {credits_restants:.2f}/{credits_total:.2f}
                        <br/>

                        Moyenne obtenue :
                        {moyenne_generale:.2f}/20
                        <br/>

                        Rang :
                        {rang_etudiant}e / {effectif_classe}
                    </para>
                    """,
                    SMALL,
                ),

                Paragraph(
                    "Dr.JERRY TAFOTIE",
                    RESPONSABLE_STYLE,
                ),

                Paragraph(
                    f"{safe_text(annee)}",
                    SMALL,
                ),

                Paragraph(
                    decision_globale,
                    DECISION_SMALL,
                ),
            ],
        ],

        colWidths=[
            7.5 * cm,
            5.0 * cm,
            4.0 * cm,
            3.0 * cm,
        ],

        rowHeights=[
            0.8 * cm,
            2.4 * cm,
        ],
    )

    recap_final_table.setStyle(
        TableStyle([
            (
                "BOX",
                (0, 0),
                (-1, -1),
                1,
                colors.black,
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey,
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#D9D9D9"),
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica",
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, 0),
                "CENTER",
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                11,
            ),

            (
                "ROUNDEDCORNERS",
                [6, 6, 6, 6],
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ])
    )

    elements.append(
        recap_final_table
    )

    # ========================================================
    # SIGNATURE / DÉCISION
    # ========================================================

    DECISION_STYLE = ParagraphStyle(
        "DecisionStyle",
        parent=styles["Normal"],
        alignment=1,
        fontSize=12,
        leading=16,
    )

    signature_table = Table(
        [[
            Paragraph(
                f"""
                <b>DECISION</b>
                <br/><br/>
                {decision_globale_inline}
                """,
                DECISION_STYLE,
            ),

            Paragraph(
                """
                <b>VISA</b>
                <br/><br/>
                Dr.JERRY TAFOTIE
                <br/><br/>
                """,
                styles["Normal"],
            ),
        ]],

        colWidths=[
            9.8 * cm,
            9.8 * cm,
        ],

        rowHeights=[
            3 * cm
        ],
    )

    signature_table.setStyle(
        TableStyle([
            (
                "BOX",
                (0, 0),
                (-1, -1),
                1,
                colors.black,
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.whitesmoke,
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),

            (
                "LINEBEFORE",
                (1, 0),
                (1, -1),
                0.8,
                colors.HexColor("#333333"),
            ),
        ])
    )

    elements.append(
        Spacer(1, 15)
    )

    elements.append(
        signature_table
    )

    # ========================================================
    # GÉNÉRATION
    # ========================================================

    doc.build(elements)

    return file_path


# ============================================================
# ALIAS
# ============================================================

generer_bulletin_gestion_pdf = generer_bulletin_qhse_pdf