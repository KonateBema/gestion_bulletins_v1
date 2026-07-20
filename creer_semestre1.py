from lmd.models import FiliereLMD, EtudiantLMD, UE, ECUE, NoteLMD

filiere = FiliereLMD.objects.get(code="QHSE-L3")
etudiant = EtudiantLMD.objects.get(matricule="QHSE2026001")

programme_s1 = {
    "Management de la qualité": {
        "code": "MAG01",
        "ecues": [
            ("ISO001", "Norme ISO 9001", 14),
            ("TDB001", "Tableau de Bord", 17.5),
            ("GD001", "Gestion documentaire", 10),
        ]
    },
    "LANGUE": {
        "code": "LAN06",
        "ecues": [
            ("ANG001", "Anglais", 10),
        ]
    },
    "SANTE , SECURITE": {
        "code": "SST04",
        "ecues": [
            ("MET001", "Méthodologie", 13.5),
            ("POI001", "Plan Opérationnel Interne", 12.5),
            ("SI001", "Sécurité Incendie", 14),
        ]
    },
}

for nom_ue, data in programme_s1.items():
    ue, _ = UE.objects.get_or_create(
        code=data["code"],
        filiere=filiere,
        semestre="S1",
        defaults={
            "libelle": nom_ue,
            "credit": 6,
        },
    )

    for code_ecue, libelle, note in data["ecues"]:
        ecue, _ = ECUE.objects.get_or_create(
            ue=ue,
            code=code_ecue,
            defaults={
                "libelle": libelle,
                "coefficient": 1,
                "credit": 1,
            },
        )

        NoteLMD.objects.get_or_create(
            etudiant=etudiant,
            ecue=ecue,
            defaults={
                "cc": note,
                "examen": note,
            },
        )

print("✅ Semestre 1 créé avec succès.")