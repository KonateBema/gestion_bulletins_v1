from .models import NoteLMD, CandidatRattrapage


# ==========================================================
# CALCUL MOYENNE ECUE
# ==========================================================

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