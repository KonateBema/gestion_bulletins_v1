from lmd.models import UE, ECUE, NoteLMD,FiliereLMD,EtudiantLMD


# Récupération de la filière
filiere = FiliereLMD.objects.get(
    code="QHSE-L3"
)

# Récupération de l'étudiant
etudiant = EtudiantLMD.objects.get(
    matricule="QHSE2026001"
)
programme_s2 = {

    "Management de la qualité": {
        "code": "MAG01",
        "ecues": [
            ("MQ001", "Management Qualité", 14.5),
        ]
    },

    "Qualité et amélioration continue": {
        "code": "QAC02",
        "ecues": [
            ("TRA001", "Traçabilité", 13.5),
            ("AUD001", "Audit", 19),
            ("GD001", "Gestion documentaire", 10),
            ("TDB001", "Tableau de Bord", 17.5),
        ]
    },

    "Santé, Sécurité": {
        "code": "SST04",
        "ecues": [
            ("MSST001", "Management Santé-Sécurité au Travail", 17),
            ("POI001", "Plan Opérationnel Interne", 12.5),
        ]
    },

    "Management de projet": {
        "code": "PRO05",
        "ecues": [
            ("GP001", "Gestion de Projet", 12),
        ]
    },

    "LANGUE": {
        "code": "LAN06",
        "ecues": [
            ("ANG001", "Anglais", 10),
        ]
    },

}

for nom_ue, data in programme_s2.items():

    ue, created = UE.objects.get_or_create(
        code=data["code"],
        filiere=filiere,
        semestre="S2",
        defaults={
            "libelle": nom_ue,
            "credit": 6
        }
    )

    for code_ecue, libelle, note in data["ecues"]:

        ecue, created = ECUE.objects.get_or_create(
            ue=ue,
            code=code_ecue,
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

print("✅ Semestre 2 créé avec succès.")