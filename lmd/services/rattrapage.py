from lmd.models import NoteLMD, CandidatRattrapage


def generer_candidats_rattrapage(
        etudiant,
        session_academique
):

    notes = NoteLMD.objects.filter(
        etudiant=etudiant,
        session="1"
    )


    for note in notes:

        if note.moyenne < 10:

            CandidatRattrapage.objects.get_or_create(

                etudiant=etudiant,

                ecue=note.ecue,

                session=session_academique,

                annee_academique=note.etudiant.annee_academique,

                defaults={

                    "ancienne_note": note.moyenne

                }

            )