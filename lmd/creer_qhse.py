from lmd.models import (
    FiliereLMD,
    EtudiantLMD,
    UE,
    ECUE,
    NoteLMD
)


# ==========================
# FILIERE
# ==========================

filiere = FiliereLMD.objects.get(
    code="QHSE-L3"
)


# ==========================
# CREATION ETUDIANT
# ==========================

etudiant = EtudiantLMD.objects.get(
    matricule="QHSE2026001"
)


# ==========================
# DONNEES UE / ECUE
# ==========================

programme = {

    "UE Outils scientifiques et méthodes": [
        ("MET001", "Métrologie", 13.5),
        ("STAT001", "Statistique", 10.5),
    ],


    "UE Qualité et amélioration continue": [
        ("RSE001", "RSE et Développement Durable", 11),
        ("TRAC001", "Traçabilité", 13.5),
        ("AUD001", "Audit", 19),
        ("GD001", "Gestion documentaire", 10),
        ("TDB001", "Tableau de Bord", 17.5),
        ("POI001", "Plan Opérationnel Interne", 12.5),
    ],


    "UE Management QHSE": [
        ("MQ001", "Management Qualité", 14.5),
        ("ME001", "Management Environnement", 16),
        ("MSST001", "Management Santé-Sécurité au Travail", 17),
    ],


    "UE Sécurité et prévention des risques": [
        ("SA001", "Sécurité Alimentaire", 14),
        ("SI001", "Sécurité Incendie", 14),
    ],


    "UE Management de projet": [
        ("GP001", "Gestion de Projet", 12),
        ("RP001", "Résolution de Problèmes", 10),
    ],


    "UE Langue": [
        ("ANG001", "Anglais", 10),
    ],

}



# ==========================
# CREATION UE ECUE NOTES
# ==========================

for nom_ue, ecues in programme.items():

    ue, created = UE.objects.get_or_create(
        libelle=nom_ue,
        filiere=filiere,
        semestre="S6",
        defaults={
            "code": nom_ue[:5].upper(),
            "credit": 6
        }
    )


    for code, libelle, note in ecues:


        ecue, created = ECUE.objects.get_or_create(
            ue=ue,
            code=code,
            defaults={
                "libelle": libelle,
                "coefficient": 1,
                "credit": 1
            }
        )


        NoteLMD.objects.get_or_create(
            etudiant=etudiant,
            ecue=ecue,
            defaults={
                "cc": note,
                "examen": note
            }
        )


print(
    "✅ Etudiant + UE + ECUE + Notes créés avec succès"
)