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
    # fontName="Courier-Bold",
    fontName="Helvetica-Bold",
)

SMALL = ParagraphStyle(
    "SMALL",
    parent=styles["Normal"],
    fontSize=6.4,
    leading=10,
    # fontName="Courier-Bold",
    fontName="Helvetica-Bold",
)

# Style dédié à la colonne DÉCISION du tableau : même traitement que
# sur le bulletin Gestion, pour que les libellés plus longs ("Validée
# par compensation") tiennent sans déborder.
DECISION_SMALL = ParagraphStyle(
    "DECISION_SMALL",
    parent=SMALL,
    fontSize=6.5,
    leading=6,
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


def decision_ecue_paragraph(moyenne, ue_validee):
    """Retourne (Paragraph, couleur, acquise, compensee) pour la
    décision d'un ECUE.

    - moyenne >= 10                  -> "Validée"
    - moyenne < 10 mais UE validée    -> "Compensée"
    - moyenne < 10 et UE non validée  -> "Non validée"
    """
    if moyenne >= 10:
        return (
            Paragraph("<font color='green'><b>Validée</b></font>", DECISION_SMALL),
            colors.green,
            True,
            False,
        )
    elif ue_validee:
        return (
            Paragraph("<font color='#B8860B'><b>Compensée</b></font>", DECISION_SMALL),
            colors.HexColor("#B8860B"),
            True,
            True,
        )
    else:
        return (
            Paragraph("<font color='red'><b>Non validée</b></font>", DECISION_SMALL),
            colors.red,
            False,
            False,
        )


# ---------------------------------------------------------------------
# Moyenne générale "réutilisable" (sans rendu PDF), utilisée pour le
# calcul du rang de l'étudiant parmi ses camarades.
# ---------------------------------------------------------------------
SESSIONS_NORMALES = ["1", "2", "3", "4"]


def calculer_moyenne_generale_etudiant(etudiant, semestre):
    """Recalcule la moyenne générale d'un étudiant pour un semestre donné,
    en suivant exactement la même méthode que le bulletin (moyenne ECUE
    pondérée par les coefficients au sein de chaque UE, puis moyenne simple
    des moyennes d'UE).

    Ne fait aucun rendu : sert uniquement de brique de calcul, notamment
    pour comparer les étudiants entre eux et déterminer un rang.
    """
    ues = (
        UE.objects
        .filter(filiere=etudiant.filiere, semestre=semestre, niveau=etudiant.niveau)
        .prefetch_related(Prefetch("ecues", queryset=ECUE.objects.order_by("ordre")))
        .order_by("ordre")
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
                semestre__iexact=semestre,
                session__in=SESSIONS_NORMALES,
            ).first()
            moyenne = float(note.moyenne) if note and note.moyenne is not None else 0.0
            somme += moyenne * ecue.coefficient
            coef += ecue.coefficient

        moyenne_ue = round(somme / coef, 2) if coef > 0 else 0
        moyennes_ues.append(moyenne_ue)

    return round(sum(moyennes_ues) / len(moyennes_ues), 2) if moyennes_ues else 0


def calculer_rang_etudiant(etudiant, semestre, moyenne_etudiant):
    """Calcule le rang de l'étudiant parmi les étudiants de la même filière,
    du même niveau et de la même année académique, pour ce semestre.

    Classement "façon compétition" : les ex-aequo ont le même rang et le
    rang suivant saute (1, 2, 2, 4, ...).

    Retourne (rang, effectif_de_la_classe).
    """
    from .models import EtudiantLMD

    camarades = EtudiantLMD.objects.filter(
        filiere=etudiant.filiere,
        niveau=etudiant.niveau,
        annee_academique=etudiant.annee_academique,
    ).exclude(pk=etudiant.pk)

    moyennes_autres = [
        calculer_moyenne_generale_etudiant(camarade, semestre)
        for camarade in camarades
    ]

    effectif = len(moyennes_autres) + 1
    rang = 1 + sum(1 for m in moyennes_autres if m > moyenne_etudiant)

    return rang, effectif


def generer_bulletin_droit_prive_pdf(etudiant, semestre, file_path):

    # Libellé affiché en haut du bulletin.
    session_label = "1"

    # La base contient des valeurs hétérogènes pour désigner la session
    # normale selon comment les notes ont été saisies ("1", "Normale",
    # "NORMALE", ...). On accepte donc toutes ces variantes au lieu
    # d'en imposer une seule, pour ne pas rater des notes existantes.
    SESSIONS_NORMALES = ["1", "2", "3", "4"]

    moyennes_ues = []  # une valeur par UE (moyenne pondérée des ECUE de cette UE)

    # Indique si au moins une ECUE du bulletin a été validée grâce à
    # la compensation (moyenne ECUE < 10 mais UE validée), pour
    # déterminer la décision finale.
    compensation_utilisee = False

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
        specialite = "TRONC COMMUN"
    else:
        specialite = etudiant.filiere.libelle if etudiant.filiere else " SCIENCES JURIDIQUE"

    cadre_universite = Table([[
        Paragraph(f"""
            <b>DOMAINE :  SCIENCES JURIDIQUE</b><br/>
             <b></b><br/><br/>
             <b>SPECIALITE :</b> {specialite.upper()}<br/>
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

        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
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
        # Compteurs au niveau des GRANDES UNITÉS (UFO1, UCG2, ...),
        # incrémentés dans inserer_ligne_grande_unite ci-dessous.
        # C'est ce niveau, et non celui des UE "techniques", qui doit
        # servir pour "Total UE validées" dans le récapitulatif final.
        "gu_total": 0,
        "gu_validees": 0,
    }

    grande_unite_actuelle = None

    # --- Accumulateurs pour la ligne récapitulative de la grande unité
    # en cours de traitement. IMPORTANT : le total "crédits ECUE" et le
    # total "crédits UE" sont deux sommes DIFFÉRENTES (elles ne
    # coïncident pas forcément), il faut donc les accumuler séparément.
    credits_ue_gu = 0     # somme des ue.credit de la grande unité en cours
    credits_ecue_gu = 0   # somme des crédits ECUE *obtenus* de la grande unité en cours
    ponderation_gu = 0    # somme(moyenne_ue * credit_ue), pour la moyenne pondérée

    def inserer_ligne_grande_unite(grande_unite, credits_ue, credits_ecue, ponderation):
        """Ajoute la ligne récapitulative d'une grande unité (ex: UFO1,
        UCG2, USP3, ...) juste après les UE qui la composent, dans le
        style du bulletin papier : code, libellé, total crédits ECUE,
        total crédits UE, moyenne pondérée et décision. `data`/
        `table_style`/`stats` sont capturés par closure."""
        if credits_ue == 0:
            return
        moyenne_gu = round(ponderation / credits_ue, 2)
        gu_validee = moyenne_gu >= 10

        # Comptage "Total UE validées" au niveau grande unité.
        stats["gu_total"] += 1
        if gu_validee:
            stats["gu_validees"] += 1

        if gu_validee:
            decision_gu = Paragraph("<font color='green'><b>Validée</b></font>", DECISION_SMALL)
            couleur_gu = colors.green
        else:
            decision_gu = Paragraph("<font color='red'><b>Non Validée</b></font>", DECISION_SMALL)
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
            # NOTE : le décompte des crédits ECUE (obtenus/affichés) se
            # fait plus bas, une fois la décision de chaque ECUE connue
            # (elle dépend de la moyenne de l'UE, qui n'est calculée
            # qu'une fois toutes les notes de l'UE lues).

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

        # --- 2) On construit les lignes du tableau, une décision PAR ECUE ---
        # Règle de décision par ECUE :
        #   - moyenne ECUE >= 10                        -> "Validée"
        #   - moyenne ECUE < 10 mais moyenne UE >= 10    -> "Compensée"
        #   - moyenne ECUE < 10 et moyenne UE < 10       -> "Non validée"
        # Règle de crédit ECUE affiché :
        #   - "Validée" ou "Compensée" -> crédit plein (ecue.credit)
        #   - "Non validée"            -> crédit remis à 0
        lignes_ue = []
        premiere_ligne = True
        for ecue, moyenne in ecue_data:
            decision_ecue, couleur_ecue, ecue_acquise, ecue_compensee = decision_ecue_paragraph(moyenne, ue_validee)

            credit_ecue_affiche = ecue.credit if ecue_acquise else 0

            if ecue_acquise:
                stats["ecues_validees"] += 1

            stats["credits_ecue_obtenus"] += credit_ecue_affiche
            # CORRECTIF : le total "crédits ECUE" doit compter le crédit
            # MAXIMUM possible (ecue.credit), pas seulement ce qui a été
            # obtenu. Avant, "credits_ecue_total" recevait la même valeur
            # que "credits_ecue_obtenus", ce qui rendait le total
            # toujours égal à l'obtenu, et donc le test de validation
            # totalement inefficace (toujours "0 restant").
            stats["credits_ecue_total"] += ecue.credit
            credits_ecue_gu += credit_ecue_affiche

            if ecue_compensee:
                compensation_utilisee = True

            lignes_ue.append([
                Paragraph(ue.code if premiere_ligne else "", SMALL),
                Paragraph(ue.libelle if premiere_ligne else "", SMALL),
                Paragraph(ecue.libelle, SMALL),
                Paragraph(f"{credit_ecue_affiche:.2f}", SMALL),
                Paragraph(f"{ue.credit:.2f}" if premiere_ligne else "", SMALL),
                Paragraph(f"{moyenne:.2f}", SMALL),
                Paragraph(f"{moyenne_ue:.2f}" if premiere_ligne else "", SMALL),
                decision_ecue,
            ])
            premiere_ligne = False

        debut = len(data)
        data.extend(lignes_ue)
        fin = len(data) - 1

        # fusion des cellules communes à toute l'UE (la colonne DÉCISION
        # n'est PLUS fusionnée puisqu'elle est désormais propre à chaque ECUE)
        for col in [0, 1, 4, 6]:
            table_style.append(("SPAN", (col, debut), (col, fin)))

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

    # Rang de l'étudiant parmi ses camarades (même filière/niveau/année),
    # à afficher dans le récapitulatif final.
    rang_etudiant, effectif_classe = calculer_rang_etudiant(etudiant, semestre, moyenne_generale)

    # --- Ligne finale "TOTAL CREDITS ACQUIS" (TCA) ---
    # Comme pour les grandes unités, CRÉD ECUE et CRÉD UE sont deux
    # totaux distincts : la somme de tous les crédits ECUE d'un côté,
    # la somme de tous les crédits UE de l'autre. Le total CRÉD ECUE
    # affiché ici représente désormais le maximum possible (voir
    # correctif ci-dessus).
    data.append([
        Paragraph("<b>TCA</b>", SMALL),
        Paragraph("<b>TOTAL CREDITS ACQUIS</b>", SMALL),
        "",
        Paragraph(f"<b>{stats['credits_ecue_obtenus']:.2f}</b>", SMALL),
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
        1.3 * cm,   # Code
        5.1 * cm,     # UE
        6   * cm,     # ECUE
        1.2 * cm,   # Crédit ECUE
        1.2 * cm,   # Crédit UE
        1.2 * cm,   # Moy ECUE
        1.2 * cm,   # Moy UE
        2.4 * cm,   # Décision
    ], rowHeights=[30] + [15] * (len(data) - 1))

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
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

    # CORRECTIF PRINCIPAL : s'il n'y a aucune UE (ou aucune ECUE) trouvée
    # pour ce semestre (pas encore de notes saisies, etc.), tous les
    # totaux valent 0 et "0 restant == 0" était auparavant interprété à
    # tort comme "tout est acquis" -> le bulletin affichait "VALIDÉE"
    # alors qu'il n'y avait simplement AUCUNE donnée. On bloque ce
    # faux positif explicitement.
    donnees_presentes = stats["ue_total"] > 0 and stats["ecues_total"] > 0

    # Décision finale sur le même vocabulaire à 3 états que les ECUE :
    #   - aucune donnée pour ce semestre               -> "Aucune note saisie"
    #   - des crédits UE/ECUE manquent                 -> "Non validée"
    #   - tous les crédits acquis, mais au moins
    #     une ECUE compensée quelque part               -> "Validée par compensation"
    #   - tous les crédits acquis, sans compensation    -> "Validée complète"
    admis = (
        donnees_presentes
        and credits_ue_restants == 0
        and credits_ecue_restants == 0
    )

    if not donnees_presentes:
        decision_globale = (
            '<para align="center">'
            '<font color="red"><b>AUCUNE NOTE SAISIE</b></font>'
            '</para>'
        )
        decision_globale_inline = "<font color='red'><b>AUCUNE NOTE SAISIE</b></font>"
    elif not admis:
        decision_globale = (
            '<para align="center">'
            '<font color="red"><b>NON VALIDÉE</b></font>'
            '</para>'
        )
        decision_globale_inline = "<font color='red'><b>NON VALIDÉE</b></font>"
    elif compensation_utilisee:
        decision_globale = (
            '<para align="center">'
            '<font color="#B8860B"><b> VALIDÉE PAR COMPENSATION</b></font>'
            '</para>'
        )
        decision_globale_inline = "<font color='#B8860B'><b>VALIDÉE PAR COMPENSATION</b></font>"
    else:
        decision_globale = (
            '<para align="center">'
            '<font color="green"><b>VALIDÉE AU COMPLET</b></font>'
            '</para>'
        )
        decision_globale_inline = "<font color='green'><b>VALIDÉE AU COMPLET</b></font>"

    ecues_total = stats["ecues_total"]
    ecues_validees = stats["ecues_validees"]
    # "Total UE validées" est désormais basé sur les GRANDES UNITÉS
    # (celles affichées sur les lignes récapitulatives, ex: UFO1, UCG2),
    # et non plus sur les UE techniques qui portent les ECUE.
    gu_total = stats["gu_total"]
    gu_validees = stats["gu_validees"]
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
                Total UE validées : {gu_validees}/{gu_total}<br/>
                Total crédits acquis : {credits_obtenus}/{credits_total}<br/>
                Total Crédits restants : {credits_restants}/{credits_total}<br/>
                Moyenne obtenue : {moyenne_generale}/20<br/>
                Rang : {rang_etudiant}e / {effectif_classe}<br/>
                 </para>
                """,
                SMALL,
            ),
            Paragraph("""Dr.JERRY TAFOTIE<br/><br/>""", SMALL),
            Paragraph(f"{annee}", SMALL),
            # Paragraph(decision_globale, DECISION_SMALL),
        ]
    ], colWidths=[7 * cm, 4.5 * cm, 4 * cm],
       rowHeights=[0.8 * cm, 2.7 * cm])

    recap_final_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9D9D9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(recap_final_table)

    DECISION_STYLE = ParagraphStyle(
        "DecisionStyle", parent=styles["Normal"], alignment=1, fontSize=12, leading=16,
    )

    signature_table = Table([[
        Paragraph(f"<b>DECISION</b><br/><br/>{decision_globale_inline}", DECISION_STYLE),
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