from django.shortcuts import render, redirect
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
# from .models import ECUE, UE
# from .pdf_service_ue import bulletin_lmd_pdf
import os
from django.conf import settings
from django.http import FileResponse
from .pdf_service_ue import generate_bulletin_lmd_pdf
from .forms import EtudiantLMDForm
from django.db.models import Sum
from .pdf_service_ue import generate_bulletin_lmd_pdf
from django.core.paginator import Paginator
from django.contrib import messages

def niveau_list(request):
    niveaux = Niveau.objects.all()
    return render(request, "lmd/niveaux/list.html", {"niveaux": niveaux})


def niveau_add(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        Niveau.objects.create(nom=nom)
        return redirect("niveau_lmd_list")

    return render(request, "lmd/niveaux/add.html")

def filiere_list(request):
    filieres = FiliereLMD.objects.all()
    return render(request, "lmd/filieresLMD/list.html", {"filieres": filieres})


def filiere_add(request):
    if request.method == "POST":
        Filiere.objects.create(
            nom=request.POST.get("nom")
        )
    return redirect("filiere_lmd_list")


def filiere_delete(request, pk):
    filiere = get_object_or_404(FiliereLMD, pk=pk)
    filiere.delete()
    return redirect("filiere_list")



# UPDATE
def filiere_edit(request, pk):
    filiere = get_object_or_404(FiliereLMD, pk=pk)

    if request.method == "POST":
        filiere.code = request.POST.get("code")
        filiere.libelle = request.POST.get("libelle")
        filiere.save()
        return redirect("filiere_list")

    return render(request, "lmd/filieresLMD/edit.html", {
        "filiere": filiere
    })


def filiere_delete(request, pk):
    filiere = Filiere.objects.get(pk=pk)

    if request.method == "POST":
        filiere.delete()
        return redirect("filiere_lmd_list")

    return redirect("filiere_lmd_list")



def classe_list(request):
    classes = Classe.objects.all()
    return render(request, "lmd/classes/list.html", {
        "classes": classes
    })


def classe_add(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        niveau=request.POST.get("niveau"),
        filiere_id = request.POST.get("filiere")

        Classe.objects.create(
            nom=nom,
            niveau=request.POST.get("niveau"),   # 🔥 IMPORTANT
            filiere_id=filiere_id
        )
        return redirect("classe_lmd_list")

    return render(request, "lmd/classes/add.html", {
        "niveaux": Niveau.objects.all(),
        "filieres": FiliereLMD.objects.all()
    })


def ue_list(request):

    ues = UE.objects.select_related(
        "filiere"
    ).order_by(
        "filiere__libelle",
        "semestre",
        "code"
    )

    return render(
        request,
        "lmd/ue/list.html",
        {
            "ues": ues
        }
    )


def ue_add(request):

    if request.method == "POST":
        try:
            filiere_id = request.POST.get("filiere")
            grande_unite_id = request.POST.get("grande_unite")

            # 🔥 Vérification des ForeignKey (évite FOREIGN KEY constraint failed)
            filiere = get_object_or_404(FiliereLMD, id=filiere_id)
            grande_unite = get_object_or_404(GrandeUnite, id=grande_unite_id)

            UE.objects.create(
                code=request.POST.get("code"),
                libelle=request.POST.get("libelle"),
                credit=int(request.POST.get("credit", 0)),
                semestre=request.POST.get("semestre"),
                filiere=filiere,
                grande_unite=grande_unite,
            )

            messages.success(request, "UE ajoutée avec succès.")
            return redirect("ue_list")

        except ValueError:
            messages.error(request, "Le crédit doit être un nombre valide.")

        except Exception as e:
            messages.error(request, f"Erreur : {e}")

    return render(
        request,
        "lmd/ue/add.html",
        {
            "filieres": FiliereLMD.objects.all(),
            "grandes_unites": GrandeUnite.objects.all(),
        }
    )

def ue_edit(request, pk):

    ue = get_object_or_404(UE, pk=pk)

    if request.method == "POST":
        try:
            filiere_id = request.POST.get("filiere")
            grande_unite_id = request.POST.get("grande_unite")

            # 🔥 Sécurisation ForeignKey
            filiere = get_object_or_404(FiliereLMD, id=filiere_id)
            grande_unite = get_object_or_404(GrandeUnite, id=grande_unite_id)

            ue.code = request.POST.get("code")
            ue.libelle = request.POST.get("libelle")
            ue.credit = int(request.POST.get("credit", 0))
            ue.semestre = request.POST.get("semestre")

            ue.filiere = filiere
            ue.grande_unite = grande_unite

            ue.save()

            messages.success(request, "UE modifiée avec succès.")
            return redirect("ue_list")

        except ValueError:
            messages.error(request, "Le crédit doit être un nombre valide.")

        except Exception as e:
            messages.error(request, f"Erreur : {e}")

    return render(request, "lmd/ue/edit.html", {
        "ue": ue,
        "filieres": FiliereLMD.objects.all(),
        "grandes_unites": GrandeUnite.objects.all(),
    })

def ue_delete(request, pk):

    ue = UE.objects.get(pk=pk)

    if request.method == "POST":
        ue.delete()
        return redirect("ue_list")

    return render(
        request,
        "lmd/ue/delete.html",
        {
            "ue": ue
        }
    )


# =====================
# LISTE + FILTRE
# =====================
def ecue_list(request):

    ue_id = request.GET.get("ue")

    ecues = ECUE.objects.select_related("ue").all()

    if ue_id:
        ecues = ecues.filter(ue_id=ue_id)

    total_credits = ecues.aggregate(
     total=Sum("credit")
     )["total"] or 0

    return render(request, "lmd/ecue/list.html", {
        "ecues": ecues,
        "ues": UE.objects.all(),
        "ue_selected": ue_id,
        "total_credits": total_credits,
    })


# =====================
# CREATE
# =====================
def ecue_add(request):

    if request.method == "POST":

        ECUE.objects.create(
            ue_id=request.POST.get("ue"),
            code=request.POST.get("code"),
            libelle=request.POST.get("libelle"),
            coefficient=request.POST.get("coefficient"),
            credit=request.POST.get("credit")
        )

        return redirect("ecue_list")

    return render(request, "lmd/ecue/add.html", {
        "ues": UE.objects.all()
    })


# =====================
# UPDATE
# =====================
def ecue_edit(request, pk):

    ecue = get_object_or_404(ECUE, pk=pk)

    if request.method == "POST":

        ecue.ue_id = request.POST.get("ue")
        ecue.code = request.POST.get("code")
        ecue.libelle = request.POST.get("libelle")
        ecue.coefficient = request.POST.get("coefficient")
        ecue.credit = request.POST.get("credit")

        ecue.save()

        return redirect("ecue_list")

    return render(request, "lmd/ecue/edit.html", {
        "ecue": ecue,
        "ues": UE.objects.all()
    })


# =====================
# DELETE
# =====================
def ecue_delete(request, pk):

    ecue = get_object_or_404(ECUE, pk=pk)

    if request.method == "POST":
        ecue.delete()
        return redirect("ecue_list")

    return render(request, "lmd/ecue/delete.html", {
        "ecue": ecue
    })


from django.db.models import Q
from .models import NoteLMD, EtudiantLMD, ECUE


def note_lmd_list(request):

    notes = NoteLMD.objects.select_related(
        "etudiant",
        "ecue"
    )

    etudiant = request.GET.get("etudiant")
    ecue = request.GET.get("ecue")

    if etudiant:
        notes = notes.filter(
            Q(etudiant__nom__icontains=etudiant) |
            Q(etudiant__prenoms__icontains=etudiant) |
            Q(etudiant__matricule__icontains=etudiant)
        )

    if ecue:
        notes = notes.filter(ecue__code__icontains=ecue)

    return render(request, "lmd/notes/list.html", {
        "notes": notes,
        "ecues": ECUE.objects.all(),
    })


def note_lmd_add(request):

    if request.method == "POST":
        try:
            etudiant_id = request.POST.get("etudiant")
            ecue_id = request.POST.get("ecue")
            semestre = request.POST.get("semestre")
            session = request.POST.get("session")

            cc = float(request.POST.get("cc", "0").replace(",", "."))
            examen = float(request.POST.get("examen", "0").replace(",", "."))

            NoteLMD.objects.create(
                etudiant_id=etudiant_id,
                ecue_id=ecue_id,
                semestre=semestre,
                session=session,
                cc=cc,
                examen=examen,
            )

            messages.success(request, "La note a été enregistrée avec succès.")
            return redirect("note_lmd_list")

        except ValueError:
            messages.error(
                request,
                "Les notes de CC et d'examen doivent être des nombres valides."
            )

        except Exception as e:
            messages.error(request, f"Erreur : {e}")

    return render(
        request,
        "lmd/notes/form.html",
        {
            "etudiants": EtudiantLMD.objects.all(),
            "ecues": ECUE.objects.all(),
        },
    )


def note_lmd_edit(request, pk):

    note = get_object_or_404(NoteLMD, pk=pk)

    if request.method == "POST":
        try:
            note.etudiant_id = request.POST.get("etudiant")
            note.ecue_id = request.POST.get("ecue")
            note.semestre = request.POST.get("semestre")
            note.session = request.POST.get("session")

            # ✅ Conversion obligatoire en float
            note.cc = float(request.POST.get("cc", "0").replace(",", "."))
            note.examen = float(request.POST.get("examen", "0").replace(",", "."))

            note.save()

            messages.success(request, "Note modifiée avec succès.")
            return redirect("note_lmd_list")

        except ValueError:
            messages.error(request, "CC et Examen doivent être des nombres valides.")

    return render(request, "lmd/notes/form.html", {
        "note": note,
        "etudiants": EtudiantLMD.objects.all(),
        "ecues": ECUE.objects.all(),
    })
def note_lmd_delete(request, pk):

    note = NoteLMD.objects.get(pk=pk)
    note.delete()

    return redirect("note_lmd_list")

from .models import EtudiantLMD

from django.db.models import Q

def bulletin_lmd_listDD(request):

    classes = ClasseLMD.objects.select_related('filiere')

    matricule = request.GET.get("matricule")
    nom = request.GET.get("nom")
    telephone = request.GET.get("telephone")
    niveau = request.GET.get("niveau")
    classe = request.GET.get("classe")

    if matricule:
        etudiants = etudiants.filter(matricule__icontains=matricule)

    if nom:
        etudiants = etudiants.filter(
            Q(nom__icontains=nom) |
            Q(prenoms__icontains=nom)
        )

    if telephone:
        etudiants = etudiants.filter(
            telephone__icontains=telephone
        )

    if niveau:
        etudiants = etudiants.filter(
            niveau=request.POST.get("niveau"),   # 🔥 IMPORTANT
        )

    if classe:
        etudiants = etudiants.filter(
            classe_id=classe
        )

    return render(
        request,
        "lmd/bulletins/list.html",
        {
            "etudiants": etudiants,
            "niveaux": NiveauLMD.objects.all(),
            "classes": ClasseLMD.objects.all(),
        }
    )

from django.db.models import Q

def bulletin_lmd_list(request):

    matricule = request.GET.get("matricule")
    nom = request.GET.get("nom")
    telephone = request.GET.get("telephone")
    niveau = request.GET.get("niveau")
    classe = request.GET.get("classe")

    # Charger tous les étudiants au départ
    etudiants = EtudiantLMD.objects.select_related(
        "niveau",
        "classe"
    ).all()

    if matricule:
        etudiants = etudiants.filter(
            matricule__icontains=matricule
        )

    if nom:
        etudiants = etudiants.filter(
            Q(nom__icontains=nom) |
            Q(prenoms__icontains=nom)
        )

    if telephone:
        etudiants = etudiants.filter(
            telephone__icontains=telephone
        )

    if niveau:
        etudiants = etudiants.filter(
            niveau_id=niveau
        )

    if classe:
        etudiants = etudiants.filter(
            classe_id=classe
        )

    return render(
        request,
        "lmd/bulletins/list.html",
        {
            "etudiants": etudiants,
            "niveaux": NiveauLMD.objects.all(),
            "classes": ClasseLMD.objects.select_related("filiere"),
            "matricule": matricule,
            "nom": nom,
            "telephone": telephone,
            "niveau_selected": niveau,
            "classe_selected": classe,
        }
    )

from django.db.models import Q
def bulletin_lmd_list(request):

    etudiants = EtudiantLMD.objects.select_related(
        "user",
        "filiere"
    )

    matricule = request.GET.get("matricule")
    nom = request.GET.get("nom")
    telephone = request.GET.get("telephone")
    classe = request.GET.get("classe")

    if matricule:
        etudiants = etudiants.filter(matricule__icontains=matricule)

    if nom:
        etudiants = etudiants.filter(
            Q(nom__icontains=nom) |
            Q(prenoms__icontains=nom)
        )

    if telephone:
        etudiants = etudiants.filter(telephone__icontains=telephone)

    if classe:
        etudiants = etudiants.filter(classe_id=classe)

    return render(request, "lmd/bulletins/list.html", {
        "etudiants": etudiants,
        "classes": ClasseLMD.objects.select_related("filiere"),
    })

def bulletin_lmd_list(request):

    matricule = request.GET.get("matricule")
    nom = request.GET.get("nom")
    telephone = request.GET.get("telephone")
    classe = request.GET.get("classe")

    etudiants = EtudiantLMD.objects.select_related(
        "user",
        "filiere"
    ).all()

    if matricule:
        etudiants = etudiants.filter(matricule__icontains=matricule)

    if nom:
        etudiants = etudiants.filter(
            Q(nom__icontains=nom) |
            Q(prenoms__icontains=nom)
        )

    if telephone:
        etudiants = etudiants.filter(telephone__icontains=telephone)

    if classe:
        etudiants = etudiants.filter(classe_id=classe)

    return render(request, "lmd/bulletins/list.html", {
        "etudiants": etudiants,
        "classes": ClasseLMD.objects.select_related("filiere"),
    })


def etudiant_lmd_addENC(request):

    if request.method == "POST":

        etudiant = EtudiantLMD.objects.create(
            matricule=request.POST.get("matricule"),
            nom=request.POST.get("nom"),
            prenoms=request.POST.get("prenoms"),
            sexe=request.POST.get("sexe"),
            date_naissance=request.POST.get("date_naissance"),
            telephone=request.POST.get("telephone"),
            email=request.POST.get("email"),
            niveau=request.POST.get("niveau"),   # 🔥 IMPORTANT
            filiere_id=request.POST.get("filiere"),
            annee_academique=request.POST.get("annee_academique"),
        )

        # 🔥 UE automatique selon filière
        ues = UE.objects.filter(filiere=etudiant.filiere)

        return redirect("etudiant_lmd_list")

    return render(request, "lmd/etudiants/add.html", {
        "niveaux": Niveau.objects.all(),
        "filieres": FiliereLMD.objects.all(),
        "ues": UE.objects.all(),
        "ecues": ECUE.objects.all(),
    })

def etudiant_lmd_add(request):

    if request.method == "POST":

        from datetime import datetime

        date_naissance = request.POST.get("date_naissance")

        if date_naissance:
            try:
                date_naissance = datetime.strptime(date_naissance, "%Y-%m-%d").date()
            except ValueError:
                date_naissance = None
        else:
            date_naissance = None

        etudiant = EtudiantLMD.objects.create(
            matricule=request.POST.get("matricule"),
            nom=request.POST.get("nom"),
            prenoms=request.POST.get("prenoms"),
            sexe=request.POST.get("sexe"),
            date_naissance=date_naissance,
            telephone=request.POST.get("telephone"),
            email=request.POST.get("email"),
            niveau=request.POST.get("niveau"),
            filiere_id=request.POST.get("filiere"),
            annee_academique=request.POST.get("annee_academique"),
        )

        # ✔ récupération UE / ECUE
        ue_ids = request.POST.getlist("ue")
        ecue_ids = request.POST.getlist("ecue")

        # ✔ liaison (si ManyToMany)
        etudiant.ues.set(UE.objects.filter(id__in=ue_ids))
        etudiant.ecues.set(ECUE.objects.filter(id__in=ecue_ids))

        return redirect("etudiant_lmd_list")

    return render(request, "lmd/etudiants/add.html", {
        "niveaux": Niveau.objects.all(),
        "filieres": FiliereLMD.objects.all(),
        "ues": UE.objects.all(),
        "ecues": ECUE.objects.all(),
    })

def calcul_moyenne_ecue(note):
    if not note:
        return 0

    cc = note.cc or 0
    examen = note.examen or 0

    return round((cc * 0.4) + (examen * 0.6), 2)

def calcul_moyenne_ue(etudiant, ue):

    ecues = ue.ecues.all()

    notes = NoteLMD.objects.filter(
        etudiant=etudiant,
        ecue__ue=ue
    )

    total = 0
    count = 0

    for note in notes:
        total += calcul_moyenne_ecue(note)
        count += 1

    if count == 0:
        return 0

    return round(total / count, 2)
def ue_validee(moyenne_ue):
    return moyenne_ue >= 10

def etudiant_lmd_editDDD(request, pk):
    etudiant = EtudiantLMD.objects.get(pk=pk)
    return render(request, "lmd/etudiants/edit.html", {"etudiant": etudiant})


def etudiant_lmd_delete(request, pk):
    etudiant = get_object_or_404(EtudiantLMD, pk=pk)

    if request.method == "POST":
        etudiant.delete()

    return redirect("etudiant_lmd_list")

def etudiant_lmd_updateBBBBB(request, pk):
    etudiant = get_object_or_404(EtudiantLMD, pk=pk)

    if request.method == "POST":
        etudiant.matricule = request.POST.get("matricule")
        etudiant.nom = request.POST.get("nom")
        etudiant.prenoms = request.POST.get("prenoms")
        etudiant.telephone = request.POST.get("telephone")
        etudiant.sexe = request.POST.get("sexe")
        etudiant.annee_academique = request.POST.get("annee_academique")
        # etudiant.filiere_id = request.POST.get("filiere")
        etudiant.save()

    return redirect("etudiant_lmd_list")

def etudiant_lmd_update(request, pk):
    etudiant = get_object_or_404(EtudiantLMD, pk=pk)

    if request.method == "POST":
        try:
            matricule = request.POST.get("matricule")

            if EtudiantLMD.objects.exclude(id=etudiant.id).filter(matricule=matricule).exists():
                return redirect("etudiant_lmd_list")

            etudiant.matricule = matricule or ""
            etudiant.nom = request.POST.get("nom") or ""
            etudiant.prenoms = request.POST.get("prenoms") or ""
            etudiant.telephone = request.POST.get("telephone") or ""
            etudiant.email = request.POST.get("email") or ""

            etudiant.sexe = request.POST.get("sexe") or "M"
            etudiant.niveau = request.POST.get("niveau") or "L1"
            etudiant.statut = request.POST.get("statut") or "AF"
            etudiant.annee_academique = request.POST.get("annee_academique") or ""

            filiere_id = request.POST.get("filiere")
            if filiere_id:
                etudiant.filiere_id = filiere_id

            date_naissance = request.POST.get("date_naissance")
            if date_naissance:
                etudiant.date_naissance = date_naissance

            etudiant.save()

            # =========================
            # UE / ECUE
            # =========================
            ue_ids = request.POST.getlist("ue")
            ecue_ids = request.POST.getlist("ecue")

            etudiant.ues.set(ue_ids)
            etudiant.ecues.set(ecue_ids)

        except Exception as e:
            print("ERROR UPDATE ETUDIANT:", e)

    return redirect("etudiant_lmd_list")


def resultat_ue(request, etudiant_id):

    from .models import EtudiantLMD, UE

    etudiant = EtudiantLMD.objects.get(id=etudiant_id)
    ues = UE.objects.all()

    resultats = []

    for ue in ues:
        moyenne = calcul_moyenne_ue(etudiant, ue)

        resultats.append({
            "ue": ue,
            "moyenne": moyenne,
            "statut": statut_ue(moyenne)
        })

    return render(request, "lmd/resultats_ue.html", {
        "etudiant": etudiant,
        "resultats": resultats
    })

def bulletin_lmd_pdf(request, etudiant_id):

    file_path = os.path.join(
        settings.BASE_DIR,
        f"bulletin_{etudiant_id}.pdf"
    )

    generate_bulletin_lmd_pdf(etudiant_id, file_path)

    return FileResponse(open(file_path, "rb"))


def etudiant_lmd_list(request):

    etudiants = EtudiantLMD.objects.select_related(
        "user",
        "filiere"
    )

    matricule = request.GET.get("matricule")
    nom = request.GET.get("nom")
    telephone = request.GET.get("telephone")
    ue = request.GET.get("ue")

    if matricule:
        etudiants = etudiants.filter(
            matricule__icontains=matricule
        )

    if nom:
        etudiants = etudiants.filter(
            Q(nom__icontains=nom) |
            Q(prenoms__icontains=nom)
        )

    if telephone:
        etudiants = etudiants.filter(
            telephone__icontains=telephone
        )

    if ue:
        etudiants = etudiants.filter(
            note_lmd__ecue__code__icontains=ue
        ).distinct()

    # Trier les étudiants
    etudiants = etudiants.order_by("nom")

    # Pagination (10 étudiants par page)
    paginator = Paginator(etudiants, 10)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "lmd/etudiants/list.html", {
        "page_obj": page_obj,
    })



def note_lmdecue_add(request):

    filieres = FiliereLMD.objects.all()
    ecues = ECUE.objects.all()

    if request.method == "POST":

        filiere_id = request.POST["filiere"]
        niveau = request.POST["niveau"]
        semestre = request.POST["semestre"]
        session = request.POST["session"]
        ecue_id = request.POST["ecue"]

        etudiants = (
            EtudiantLMD.objects
            .filter(
                filiere_id=filiere_id,
                niveau=niveau
            )
            .order_by("nom", "prenoms")
        )

        return render(request,
            "lmd/notes/saisie_notes.html",
            {
                "etudiants": etudiants,
                "ecue_id": ecue_id,
                "semestre": semestre,
                "session": session,
            }
        )

    return render(
        request,
        "lmd/notes/choix.html",
        {
            "filieres": filieres,
            "ecues": ecues,
        }
    )

def note_lmd_save_batch(request):

    if request.method == "POST":

        ecue_id = request.POST.get("ecue_id")
        semestre = request.POST.get("semestre")
        session = request.POST.get("session")

        etudiants_ids = request.POST.getlist("etudiant_id")

        for etu_id in etudiants_ids:

            NoteLMD.objects.update_or_create(
                etudiant_id=etu_id,
                ecue_id=ecue_id,
                semestre=semestre,
                session=session,
                defaults={
                    "cc": request.POST.get(f"cc_{etu_id}"),
                    "examen": request.POST.get(f"examen_{etu_id}"),
                }
            )

        return redirect("note_lmd_list")

from django.shortcuts import render
from .models import NoteLMD

def note_lmd_listecue(request):

    notes = (
        NoteLMD.objects
        .select_related(
            "etudiant",
            "ecue",
            "etudiant__filiere",
        )
        .order_by(
            "etudiant__filiere__nom",
            "etudiant__niveau",
            "etudiant__nom",
        )
    )

    return render(
        request,
        "lmd/notes/listecue.html",
        {
            "notes": notes
        }
    )

def saisie_list(request):
    saisies = SaisieNoteLMD.objects.select_related(
        "filiere", "ecue"
    ).order_by("-date_creation")

    return render(request, "lmd/saisies/list.html", {
        "saisies": saisies
    })

def saisie_add(request):

    filieres = FiliereLMD.objects.all()
    niveaux = Niveau.objects.all()
    ecues = ECUE.objects.all()

    if request.method == "POST":
        SaisieNoteLMD.objects.create(
            filiere_id=request.POST.get("filiere"),
            niveau=request.POST.get("niveau"),
            ecue_id=request.POST.get("ecue"),
            semestre=request.POST.get("semestre"),
            session=request.POST.get("session"),
            created_by=request.user
        )

        return redirect("saisie_list")

    return render(request, "lmd/saisies/form.html", {
        "filieres": filieres,
        "niveaux": niveaux,
        "ecues": ecues,
    })


def saisie_edit1(request, pk):

    saisie = SaisieNoteLMD.objects.get(pk=pk)
    filieres = FiliereLMD.objects.all().order_by("libelle")
    # niveaux = Niveau.objects.all().order_by("ordre")
    niveaux = Niveau.objects.all().order_by("nom")
    ecues = ECUE.objects.all().order_by("libelle")
    if request.method == "POST":

        saisie.filiere_id = request.POST["filiere"]
        saisie.niveau = request.POST["niveau"]
        saisie.ecue_id = request.POST["ecue"]
        saisie.semestre = request.POST["semestre"]
        saisie.session = request.POST["session"]

        saisie.save()

        return redirect("saisie_list")

    return render(request, "lmd/saisies/form.html", {
        "saisie": saisie,
        "filieres": filieres,
        "niveaux": niveaux,
        "ecues": ecues,
    })

from django.shortcuts import get_object_or_404, render, redirect
from .models import SaisieNoteLMD

def saisie_edit(request, pk):

    saisie = get_object_or_404(SaisieNoteLMD, pk=pk)

    filieres = FiliereLMD.objects.all()
    ecues = ECUE.objects.all()

    if request.method == "POST":

        filiere_id = request.POST.get("filiere")
        ecue_id = request.POST.get("ecue")

        saisie.filiere = get_object_or_404(FiliereLMD, id=filiere_id)
        saisie.ecue = get_object_or_404(ECUE, id=ecue_id)

        saisie.niveau = request.POST.get("niveau")
        saisie.semestre = request.POST.get("semestre")
        saisie.session = request.POST.get("session")

        saisie.save()

        return redirect("saisie_list")

    return render(request, "lmd/saisies/edit.html", {
        "saisie": saisie,
        "filieres": filieres,
        "ecues": ecues
    })

def saisie_delete(request, pk):

    saisie = SaisieNoteLMD.objects.get(pk=pk)

    if request.method == "POST":
        saisie.delete()
        return redirect("saisie_list")

    return render(request, "lmd/saisies/delete.html", {
        "saisie": saisie
    })

def saisie_detail(request, pk):

    saisie = SaisieNoteLMD.objects.get(pk=pk)

    etudiants = EtudiantLMD.objects.filter(
        filiere=saisie.filiere,
        niveau=saisie.niveau
    ).order_by("nom")

    return render(request, "lmd/saisies/detail.html", {
        "saisie": saisie,
        "etudiants": etudiants
    })

    

# views.py



def filiereLMD_list(request):
    filieres = FiliereLMD.objects.all()
    return render(request, "lmd/filieresLMD/list.html", {"filieres": filieres})


# def filiereLMD_add(request):
#     if request.method == "POST":
#         code = request.POST.get("code")
#         libelle = request.POST.get("libelle")

#         # Vérification doublon
#         if FiliereLMD.objects.filter(code=code).exists():
#             messages.error(request, "Ce code de filière existe déjà.")
#             return redirect("filiere_add")

#         FiliereLMD.objects.create(code=code, libelle=libelle)
#         messages.success(request, "Filière ajoutée avec succès.")
#         return redirect("filiere_list")

#     return render(request, "lmd/filieresLMD/add.html")
def filiereLMD_add(request):

    if request.method == "POST":
        code = request.POST.get("code")
        libelle = request.POST.get("libelle")

        if not code or not libelle:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect("filiere_add")

        if FiliereLMD.objects.filter(code=code).exists():
            messages.error(request, "Ce code existe déjà.")
            return redirect("filiere_add")

        FiliereLMD.objects.create(
            code=code,
            libelle=libelle
        )

        messages.success(request, "Filière ajoutée avec succès.")
        return redirect("filiere_list")

    return render(request, "lmd/filieresLMD/add.html")



from django.db import transaction

def saisie_note_etudiant(request, pk):

    saisie = get_object_or_404(SaisieNoteLMD, pk=pk)

    # étudiants concernés (filtre filière + niveau)
    etudiants = EtudiantLMD.objects.filter(
        filiere=saisie.filiere,
        niveau=saisie.niveau
    ).order_by("nom", "prenoms")

    if request.method == "POST":

        with transaction.atomic():

            for etudiant in etudiants:

                note_value = request.POST.get(f"note_{etudiant.id}")

                if note_value != "" and note_value is not None:

                    NoteLMD.objects.update_or_create(
                        etudiant=etudiant,
                        ecue=saisie.ecue,
                        semestre=saisie.semestre,
                        session=saisie.session,
                        defaults={
                            "note": note_value,
                            "saisie": saisie
                        }
                    )

        return redirect("saisie_detail", pk=saisie.id)

    # récupérer notes existantes
    notes_existantes = {
        n.etudiant.id: {
        "cc": n.cc,
        "examen": n.examen
        }
        # n.etudiant.id: n.note
        for n in NoteLMD.objects.filter(
            ecue=saisie.ecue,
            semestre=saisie.semestre,
            session=saisie.session
        )
    }

    context = {
        "saisie": saisie,
        "etudiants": etudiants,
        "notes_existantes": notes_existantes,
    }

    return render(request, "lmd/saisie_note_etudiant.html", context)
    

from django.db import transaction

def enregistrer_notesAA(request, pk):

    saisie = get_object_or_404(SaisieNoteLMD, pk=pk)

    etudiants = EtudiantLMD.objects.filter(
        filiere=saisie.filiere,
        niveau=saisie.niveau
    )

    if request.method == "POST":

        with transaction.atomic():

            for etudiant in etudiants:

                cc = request.POST.get(f"cc_{etudiant.id}")
                examen = request.POST.get(f"examen_{etudiant.id}")

                # on ignore les lignes vides
                if cc == "" and examen == "":
                    continue

                NoteLMD.objects.update_or_create(
                    etudiant=etudiant,
                    ecue=saisie.ecue,
                    semestre=saisie.semestre,
                    session=saisie.session,
                    defaults={
                        "cc": cc or 0,
                        "examen": examen or 0,
                        "saisie": saisie,
                    }
                )

        return redirect("saisie_detail", pk=saisie.id)

    # GET -> affichage formulaire
    notes = {
        n.etudiant_id: n
        for n in NoteLMD.objects.filter(
            ecue=saisie.ecue,
            semestre=saisie.semestre,
            session=saisie.session
        )
    }

    for etudiant in etudiants:
        etudiant.note = notes.get(etudiant.id)

    return render(request, "lmd/saisie_note_etudiant.html", {
        "saisie": saisie,
        "etudiants": etudiants,
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction

def enregistrer_notes(request, pk):

    saisie = get_object_or_404(SaisieNoteLMD, pk=pk)

    etudiants = EtudiantLMD.objects.filter(
        filiere=saisie.filiere,
        niveau=saisie.niveau
    )

    if request.method == "POST":

        with transaction.atomic():

            for etudiant in etudiants:

                cc = request.POST.get(f"cc_{etudiant.id}")
                examen = request.POST.get(f"examen_{etudiant.id}")

                # ✅ conversion sécurisée
                try:
                    cc = float(cc)
                except (TypeError, ValueError):
                    cc = 0

                try:
                    examen = float(examen)
                except (TypeError, ValueError):
                    examen = 0

                # on ignore totalement si vide
                if cc == 0 and examen == 0:
                    continue

                NoteLMD.objects.update_or_create(
                    etudiant=etudiant,
                    ecue=saisie.ecue,
                    semestre=saisie.semestre,
                    session=saisie.session,
                    defaults={
                        "cc": cc,
                        "examen": examen,
                        "saisie": saisie,
                    }
                )

        return redirect("saisie_detail", pk=saisie.id)

    # GET -> affichage formulaire
    notes = {
        n.etudiant_id: n
        for n in NoteLMD.objects.filter(
            ecue=saisie.ecue,
            semestre=saisie.semestre,
            session=saisie.session
        )
    }

    for etudiant in etudiants:
        etudiant.note = notes.get(etudiant.id)

    return render(request, "lmd/saisie_note_etudiant.html", {
        "saisie": saisie,
        "etudiants": etudiants,
    })


def filiereLMD_edit(request, pk):
    filiere = get_object_or_404(FiliereLMD, pk=pk)

    if request.method == "POST":
        code = request.POST.get("code")
        libelle = request.POST.get("libelle")

        # vérification doublon (optionnel mais recommandé)
        if FiliereLMD.objects.exclude(pk=pk).filter(code=code).exists():
            messages.error(request, "Ce code existe déjà.")
            return redirect("filiereLMD_edit", pk=pk)

        filiere.code = code
        filiere.libelle = libelle
        filiere.save()

        messages.success(request, "Filière modifiée avec succès.")
        return redirect("filiereLMD_list")

    return render(request, "lmd/filieresLMD/edit.html", {
        "filiere": filiere
    })

def filiereLMD_delete(request, pk):
    filiere = get_object_or_404(FiliereLMD, pk=pk)
    filiere.delete()
    return redirect("filiereLMD_list")