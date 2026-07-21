from django.shortcuts import render, redirect, get_object_or_404
# from .models import *
from .forms import *
import os
from django.conf import settings
from django.http import FileResponse
from django.db.models import Sum
from .pdf_tc_service_ue import generate_bulletin_lmd_pdf
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import EtudiantDroitForm ,EtudiantGestionForm,UEForm,ECUEForm,MasterEtudiantForm ,QHSEEtudiantForm ,QHSEECUEForm
from .pdf_gestion_service import generer_bulletin_gestion_pdf
from .pdf_droit_prive_service import generer_bulletin_droit_prive_pdf
from .pdf_tronc_commun_service import generer_bulletin_tronc_commun_pdf
from .models import MasterUE,EtudiantMaster , CandidatRattrapage ,FiliereLMD
from .models import MasterECUE, NoteMaster
from .pdf_masters import generer_bulletin_masters_pdf
from .pdf_licence_qhse import generer_bulletin_licence_qhse_pdf
from reportlab.platypus import SimpleDocTemplate
from django.db.models import Avg
from .models import (
    EtudiantLMD,
    NoteLMD,
    SessionAcademique
)


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

def bulletin_lmd_listQQ(request):

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

def bulletin_lmd_listRE(request):

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

def etudiant_lmd_addens(request):

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
def etudiant_lmd_add(request):

    if request.method == "POST":

        from datetime import datetime

        matricule = request.POST.get("matricule")
        annee_academique = request.POST.get("annee_academique")


        # ==========================
        # Vérification doublon
        # ==========================
        if EtudiantLMD.objects.filter(
            matricule=matricule
        ).exists():

            messages.error(
                request,
                "Ce matricule existe déjà."
            )

            return redirect("etudiant_lmd_add")


        # ==========================
        # Conversion date naissance
        # ==========================
        date_naissance = request.POST.get("date_naissance")

        if date_naissance:
            try:
                date_naissance = datetime.strptime(
                    date_naissance,
                    "%Y-%m-%d"
                ).date()

            except ValueError:
                date_naissance = None

        else:
            date_naissance = None



        # ==========================
        # Création étudiant
        # ==========================
        EtudiantLMD.objects.create(

            matricule=matricule,

            nom=request.POST.get("nom"),

            prenoms=request.POST.get("prenoms"),

            sexe=request.POST.get("sexe"),

            statut=request.POST.get("statut", "NF"),

            date_naissance=date_naissance,

            lieu_naissance=request.POST.get(
                "lieu_naissance"
            ),

            telephone=request.POST.get(
                "telephone"
            ),

            email=request.POST.get(
                "email"
            ),

            niveau=request.POST.get(
                "niveau"
            ),

            filiere_id=request.POST.get(
                "filiere"
            ),

            annee_academique=annee_academique,

        )


        messages.success(
            request,
            "Étudiant ajouté avec succès."
        )


        return redirect(
            "etudiant_lmd_list"
        )


    return render(
        request,
        "lmd/etudiants/add.html",
        {
            "niveaux": NiveauLMD.objects.all(),
            "filieres": FiliereLMD.objects.all(),
        }
    )
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
            ue_ids = request.POST.getlist("ues")
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
         "ues": UE.objects.all(),
         "ecues": ECUE.objects.all(),
        "filieres": FiliereLMD.objects.all(),
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

     # Aucun étudiant trouvé
    aucun_etudiant = not etudiants.exists()

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

                try:
                    cc = float(cc)
                except (TypeError, ValueError):
                    cc = 0

                try:
                    examen = float(examen)
                except (TypeError, ValueError):
                    examen = 0

                # Ignore si aucune note
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
                    }
                )

        return redirect("saisie_detail", pk=saisie.id)

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


def ajouter_etudiants_saisie(request, saisie_id):

    saisie = get_object_or_404(
        SaisieNoteLMD,
        id=saisie_id
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere=saisie.filiere,
        niveau=saisie.niveau
    )

    compteur = 0

    for etudiant in etudiants:

        existe = NoteLMD.objects.filter(
            etudiant=etudiant,
            ecue=saisie.ecue,
            semestre=saisie.semestre,
            session=saisie.session
        ).exists()

        if not existe:

            NoteLMD.objects.create(
                etudiant=etudiant,
                ecue=saisie.ecue,
                semestre=saisie.semestre,
                session=saisie.session,
                cc=0,
                examen=0
            )

            compteur += 1


    messages.success(
        request,
        f"{compteur} étudiant(s) ajouté(s)."
    )


    return redirect(
        "saisie_detail",
         pk=saisie.id
    )
def filiere_l3_detail(request, id):

    filiere = FiliereLMD.objects.get(id=id)

    ues = UE.objects.filter(
        filiere=filiere
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau="L3"
    )

    return render(
        request,
        "lmd/l3_detail.html",
        {
            "filiere":filiere,
            "ues":ues,
            "etudiants":etudiants
        }
    )
    
@login_required
def filiere_master_detail(request,id):

    filiere = FiliereLMD.objects.get(id=id)


    ues = UE.objects.filter(
        filiere=filiere
    )


    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau__in=["M1","M2"]
    )


    return render(
        request,
        "lmd/master_detail.html",
        {
            "filiere":filiere,
            "ues":ues,
            "etudiants":etudiants
        }
    )
    
def generer_rattrapages(etudiant):

    notes = NoteLMD.objects.filter(
        etudiant=etudiant,
        session="1"
    )

    for note in notes:
        
        if note.moyenne < 10:

            CandidatRattrapage.objects.create(

                etudiant=etudiant,

                ecue=note.ecue,

                ancienne_note=note.moyenne

            )
            
def meilleure_note(note1,note2):

    return max(
        note1,
        note2
    )
    

@login_required
def rattrapage_liste(request):

    candidats = CandidatRattrapage.objects.select_related(
        "etudiant",
        "ecue",
        "session"
    ).all()


    return render(
        request,
        "lmd/rattrapage/liste.html",
        {
            "candidats": candidats
        }
    )
    


def saisie_rattrapage(request):

    # Session de rattrapage active
    session = SessionAcademique.objects.filter(
        type_session="RATTRAPAGE",
        active=True
    ).first()


    if not session:
        return render(
            request,
            "lmd/rattrapage/saisie.html",
            {
                "candidats": []
            }
        )


    # Chercher les notes session normale
    notes = NoteLMD.objects.filter(
        session="1"
    ).select_related(
        "etudiant",
        "ecue"
    )


    candidats = []


    for note in notes:


        # Si la moyenne ECUE est < 10
        if note.moyenne < 10:


            candidat, created = CandidatRattrapage.objects.get_or_create(

                etudiant=note.etudiant,

                ecue=note.ecue,

                session=session,

                annee_academique="2025-2026",

                defaults={

                    "ancienne_note": note.moyenne

                }

            )


            candidats.append(candidat)



    return render(

        request,

        "lmd/rattrapage/saisie.html",

        {

            "candidats": candidats

        }

    )
    
def liste_rattrapage(request):

    session_rattrapage = SessionAcademique.objects.filter(
        type_session="RATTRAPAGE",
        active=True
    ).first()


    if not session_rattrapage:

        return render(
            request,
            "lmd/rattrapage/liste.html",
            {
                "candidats": []
            }
        )


    # Notes de session normale
    notes = NoteLMD.objects.filter(
        session="1"
    ).select_related(
        "etudiant",
        "ecue"
    )


    for note in notes:


        # étudiant non validé
        if note.moyenne < 10:


            CandidatRattrapage.objects.get_or_create(

                etudiant=note.etudiant,

                ecue=note.ecue,

                session=session_rattrapage,

                annee_academique="2025-2026",

                defaults={

                    "ancienne_note": note.moyenne

                }

            )



    candidats = CandidatRattrapage.objects.select_related(

        "etudiant",

        "ecue",

        "session"

    ).filter(

        session=session_rattrapage

    ).order_by(

        "etudiant__nom"

    )

    return render(

        request,

        "lmd/rattrapage/liste.html",

        {

            "candidats": candidats

        }

    )
    
def deliberation_rattrapage(request):

    candidats = CandidatRattrapage.objects.select_related(
        "etudiant",
        "ecue",
        "session"
    ).all()

    return render(
        request,
        "lmd/rattrapage/deliberation.html",
        {
            "candidats": candidats
        }
    )
    
def bulletin_rattrapage_list(request):

    candidats = CandidatRattrapage.objects.select_related(
        "etudiant",
        "ecue",
        "session"
    ).all()
    
    return render(
        request,
        "lmd/rattrapage/bulletins.html",
        {
            "candidats": candidats
        }
    )

from django.shortcuts import render

def l3_droit_dashboard(request):

    filiere = FiliereLMD.objects.get(
        libelle="Droit Privé"
    )


    ues = UE.objects.filter(
        filiere=filiere
    ).prefetch_related(
        "ecues"
    )


    return render(
        request,
        "lmd/l3/droit/dashboard.html",
        {
            "filiere": filiere,
            "ues": ues
        }
    )

def l3_gestion_dashboard(request):

    return render(
        request,
        "lmd/l3/gestion/dashboard.html"
    )


def l3_droit_etudiants(request):

    filiere = get_object_or_404(
        FiliereLMD,
        libelle="Droit Privé"
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau="L3",
        actif=True
    ).order_by(
        "nom",
        "prenoms"
    )


    context = {
        "filiere": filiere,
        "etudiants": etudiants,
        "total_etudiants": etudiants.count(),
    }


    return render(
        request,
        "lmd/l3/droit/etudiants.html",
        context
    )

def l3_droit_etudiant_add(request):

    filiere = get_object_or_404(
        FiliereLMD,
        libelle="Droit Privé"
    )


    if request.method=="POST":

        form = EtudiantDroitForm(request.POST)


        if form.is_valid():

            etudiant=form.save(commit=False)


            etudiant.filiere=filiere

            etudiant.niveau="L3"

            etudiant.statut="AF"


            etudiant.save()


            return redirect(
                "l3_droit_etudiants"
            )


    else:

        form=EtudiantDroitForm()



    return render(
        request,
        "lmd/l3/droit/etudiant_form.html",
        {
            "form":form,
            "titre":"Ajouter étudiant L3 Droit Privé"
        }
    )

def l3_droit_etudiant_update(request,pk):

    etudiant=get_object_or_404(
        EtudiantLMD,
        pk=pk
    )


    form=EtudiantDroitForm(
        request.POST or None,
        instance=etudiant
    )


    if form.is_valid():

        form.save()

        return redirect(
            "l3_droit_etudiants"
        )


    return render(
        request,
        "lmd/l3/droit/etudiant_form.html",
        {
            "form":form,
            "titre":"Modifier étudiant"
        }
    )

def l3_droit_etudiant_delete(request,pk):

    etudiant=get_object_or_404(
        EtudiantLMD,
        pk=pk
    )


    if request.method=="POST":

        etudiant.delete()

        return redirect(
            "l3_droit_etudiants"
        )


    return render(
        request,
        "lmd/l3/droit/delete.html",
        {
            "etudiant":etudiant
        }
    )


def l3_droit_ue(request):

    filiere = get_object_or_404(
        FiliereLMD,
        libelle="Droit Privé"
    )


    ues = UE.objects.filter(
        filiere=filiere
    ).prefetch_related(
        "ecues"
    )


    return render(
        request,
        "lmd/l3/droit/ue.html",
        {
            "filiere": filiere,
            "ues": ues
        }
    )

def l3_droit_ue_add(request):

    filiere = get_object_or_404(
        FiliereLMD,
        libelle="Droit Privé"
    )


    if request.method == "POST":

        UE.objects.create(

            code=request.POST.get("code"),

            libelle=request.POST.get("libelle"),

            credit=request.POST.get("credit"),

            semestre=request.POST.get("semestre"),

            filiere=filiere

        )


        return redirect(
            "l3_droit_ue"
        )


    return render(
        request,
        "lmd/l3/droit/ue_form.html",
        {
            "titre":"Ajouter une UE - L3 Droit Privé"
        }
    )



from django.shortcuts import render, redirect, get_object_or_404
from .models import UE

def l3_droit_ue_update(request, pk):

    ue = get_object_or_404(
        UE,
        pk=pk
    )


    if request.method == "POST":

        ue.code = request.POST.get("code")
        ue.libelle = request.POST.get("libelle")
        ue.credit = request.POST.get("credit")
        ue.semestre = request.POST.get("semestre")

        ue.save()


        return redirect(
            "l3_droit_ue"
        )


    return render(
        request,
        "lmd/l3/droit/ue_form.html",
        {
            "titre":"Modifier UE",
            "ue":ue
        }
    )

def l3_droit_ue_delete(request, pk):

    ue = get_object_or_404(
        UE,
        pk=pk
    )


    ue.delete()


    return redirect(
        "l3_droit_ue"
    )



def l3_droit_prive_notes(request):

    notes = (
        NoteLMD.objects
        .filter(etudiant__filiere__libelle="Droit Privé")
        .select_related("etudiant", "ecue")
        .order_by(
            "etudiant__nom",
            "etudiant__prenoms",
            "ecue__code"
        )
    )

    return render(
        request,
        "lmd/l3/droit/notes.html",
        {
            "notes": notes
        }
    )

from django.shortcuts import render
from .models import NoteLMD

def l3_droit_prive_notes_detail(request):

    notes = (
        NoteLMD.objects
        .filter(etudiant__filiere__libelle="Droit Privé")
        .select_related("etudiant", "ecue")
        .order_by(
            "etudiant__nom",
            "etudiant__prenoms",
            "ecue__code"
        )
    )

    return render(
        request,
        "lmd/l3/droit/detail_notes.html",
        {
            "notes": notes,
        }
    )


def l3_droit_notes(request):

    etudiants = EtudiantLMD.objects.filter(
        filiere__libelle__icontains="Droit",
        niveau__icontains="L3"
    ).order_by(
        "nom",
        "prenoms"
    )

    notes = NoteLMD.objects.filter(
        etudiant__in=etudiants
    ).select_related(
        "etudiant",
        "ecue"
    )

    return render(
        request,
        "lmd/l3/droit/notes.html",
        {
            "etudiants": etudiants,
            "notes": notes
        }
    )


def l3_droit_bulletins(request):

    filiere = get_object_or_404(
        FiliereLMD,
        libelle="Droit Privé"
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau="L3"
    ).order_by(
        "nom",
        "prenoms"
    )

    return render(
        request,
        "lmd/l3/droit/bulletins.html",
        {
            "etudiants": etudiants,
            "filiere": filiere
        }
    )




def l3_gestion_etudiants(request):

    return render(
        request,
        "lmd/l3/gestion/etudiants.html"
    )



def l3_gestion_ue(request):

    ues = UE.objects.filter(
        filiere__libelle__icontains="Sciences de Gestion"
    ).order_by("code")

    return render(
        request,
        "lmd/l3/gestion/ue/list.html",
        {
            "ues": ues
        }
    )

def l3_gestion_noteseee(request):

    return render(
        request,
        "lmd/l3/gestion/notes/saisie.html"
    )

def l3_gestion_notes(request, ecue_id):

    ecue = get_object_or_404(
        ECUE,
        id=ecue_id
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere__libelle__icontains="Sciences de Gestion",
        niveau="L3"
    )


    if request.method == "POST":

        for e in etudiants:

            cc = request.POST.get(
                f"cc_{e.id}"
            )

            examen = request.POST.get(
                f"examen_{e.id}"
            )


            if cc or examen:

                NoteLMD.objects.update_or_create(
                    etudiant=e,
                    ecue=ecue,
                    defaults={
                        "cc": float(cc or 0),
                        "examen": float(examen or 0),
                    }
                )


        return redirect(
            "l3_gestion_ecue_list",
            ecue.ue.id
        )


    return render(
        request,
        "lmd/l3/gestion/notes/saisie.html",
        {
            "ecue": ecue,
            "etudiants": etudiants,
        }
    )

def l3_gestion_bulletins(request):

    return render(
        request,
        "lmd/l3/gestion/bulletins.html"
    )


def l3_gestion_notes_selection(request):

    ecues = ECUE.objects.filter(
        ue__filiere__libelle__icontains="Sciences de Gestion"
    )

    return render(
        request,
        "lmd/l3/gestion/notes/ecue_list.html",
        {
            "ecues": ecues
        }
    )
# ================= MASTER =================

def master_dashboard(request):

    return render(
        request,
        "lmd/master/dashboard.html"
    )

def master_filiere_list(request):

    return render(
        request,
        "lmd/master/filieres.html"
    )


    
def master_etudiant_list(request):

    etudiants = EtudiantMaster.objects.select_related(
        "programme"
    ).all()


    return render(
        request,
        "lmd/master/etudiants/list.html",
        {
            "etudiants":etudiants
        }
    )
    
def master_etudiant_add(request):

    if request.method == "POST":

        form = MasterEtudiantForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect(
                "master_etudiant_list"
            )

    else:

        form = MasterEtudiantForm()


    return render(
        request,
        "lmd/master/etudiants/form.html",
        {
            "form": form,
            "titre": "Ajouter étudiant Master"
        }
    )


def master_etudiant_edit(request, id):

    etudiant = get_object_or_404(
        EtudiantMaster,
        id=id
    )


    if request.method == "POST":

        form = MasterEtudiantForm(
            request.POST,
            instance=etudiant
        )


        if form.is_valid():

            form.save()

            return redirect(
                "master_etudiant_list"
            )


    else:

        form = MasterEtudiantForm(
            instance=etudiant
        )


    return render(
        request,
        "lmd/master/etudiants/form.html",
        {
            "form": form,
            "titre": "Modifier étudiant Master"
        }
    )

def master_etudiant_delete(request, id):

    etudiant = get_object_or_404(
        EtudiantMaster,
        id=id
    )


    if request.method == "POST":

        etudiant.delete()

        return redirect(
            "master_etudiant_list"
        )


    return render(
        request,
        "lmd/master/etudiants/delete.html",
        {
            "etudiant": etudiant
        }
    )

from .forms import MasterProgrammeForm


def master_programme_add(request):

    if request.method == "POST":

        form = MasterProgrammeForm(request.POST)


        if form.is_valid():

            form.save()

            return redirect(
                "master_etudiant_list"
            )


    else:

        form = MasterProgrammeForm()


    return render(
        request,
        "lmd/master/programmes/form.html",
        {
            "form": form,
            "titre": "Ajouter Programme Master"
        }
    )


def master_programme_edit(request, id):

    programme = get_object_or_404(
        MasterProgramme,
        id=id
    )

    if request.method == "POST":

        form = MasterProgrammeForm(
            request.POST,
            instance=programme
        )

        if form.is_valid():

            form.save()

            return redirect(
                "master_programme_list"
            )

    else:

        form = MasterProgrammeForm(
            instance=programme
        )

    return render(
        request,
        "lmd/master/programme_form.html",
        {
            "form": form,
            "titre": "Modifier Programme Master"
        }
    )
    
def master_programme_delete(request, id):

    programme = get_object_or_404(
        MasterProgramme,
        id=id
    )

    programme.delete()

    return redirect(
        "master_programme_list"
    ) 
    
# def master_ue_list(request):

#     return render(
#         request,
#         "lmd/master/ue_list.html"
#     )

def master_ue_listPASS(request):
    ues = MasterUE.objects.select_related("programme").all()

    return render(
        request,
        "lmd/master/ue_list.html",
        {
            "ues": ues,
        },
    )

def master_ue_list(request):

    programme_id = request.GET.get("programme")


    programme = None


    if programme_id:

        programme = get_object_or_404(
            MasterProgramme,
            id=programme_id
        )


        ues = MasterUE.objects.filter(
            programme=programme
        )


    else:

        ues = MasterUE.objects.all()



    return render(
        request,
         "lmd/master/ue_list.html",
        {
            "ues":ues,
            "programme":programme
        }
    )

def master_saisie_notes_ecuePASS(request, id):

    ecue = MasterECUE.objects.select_related(
        "ue",
        "ue__programme"
    ).get(id=id)


    etudiants = EtudiantMaster.objects.filter(
        programme=ecue.ue.programme
    )



    # Notes existantes
    notes_existantes = NoteMaster.objects.filter(
        ecue=ecue
    )



    notes_par_etudiant = {
        note.etudiant_id: note
        for note in notes_existantes
    }



    # Association étudiant + note
    for etudiant in etudiants:

        etudiant.note_existante = notes_par_etudiant.get(
            etudiant.id
        )



    if request.method == "POST":


        for etudiant in etudiants:


            cc = request.POST.get(
                f"cc_{etudiant.id}"
            )


            examen = request.POST.get(
                f"examen_{etudiant.id}"
            )


            if cc is not None or examen is not None:


                NoteMaster.objects.update_or_create(

                    etudiant=etudiant,

                    ecue=ecue,

                    defaults={

                        "cc": cc or 0,

                        "examen": examen or 0

                    }

                )



        messages.success(
            request,
            "Notes enregistrées avec succès"
        )


        return redirect(
            "master_saisie_notes",
            id=id
        )



    return render(
        request,
        "lmd/master/saisie_notes_ecue.html",
        {
            "ecue": ecue,
            "etudiants": etudiants
        }
    )

def master_saisie_notes_ecue(request, id):

    ecue = MasterECUE.objects.select_related(
        "ue",
        "ue__programme"
    ).get(id=id)


    etudiants = EtudiantMaster.objects.filter(
        programme=ecue.ue.programme
    )



    notes_existantes = NoteMaster.objects.filter(
        ecue=ecue
    )


    notes_dict = {
        note.etudiant_id: note
        for note in notes_existantes
    }


    for etudiant in etudiants:

        etudiant.note_existante = notes_dict.get(
            etudiant.id
        )



    if request.method == "POST":


        erreurs = []


        for etudiant in etudiants:


            cc = request.POST.get(
                f"cc_{etudiant.id}"
            )


            examen = request.POST.get(
                f"examen_{etudiant.id}"
            )



            if cc == "" and examen == "":
                continue



            cc = float(cc or 0)

            examen = float(examen or 0)



            # Validation

            if cc < 0 or cc > 20:

                erreurs.append(
                    f"CC invalide pour {etudiant.nom}"
                )

                continue



            if examen < 0 or examen > 20:

                erreurs.append(
                    f"Examen invalide pour {etudiant.nom}"
                )

                continue




            NoteMaster.objects.update_or_create(

                etudiant=etudiant,

                ecue=ecue,

                defaults={

                    "cc":cc,

                    "examen":examen

                }

            )




        if erreurs:


            for erreur in erreurs:

                messages.error(
                    request,
                    erreur
                )


        else:


            messages.success(
                request,
                "Les notes ont été enregistrées avec succès."
            )



        return redirect(
            "master_saisie_notes",
            id=id
        )



    return render(
        request,
        "lmd/master/saisie_notes_ecue.html",
        {
            "ecue":ecue,
            "etudiants":etudiants
        }
    )

def master_saisie_notes(request):

    programmes = MasterProgramme.objects.prefetch_related(
        "ues__ecues"
    ).all()


    return render(
        request,
        "lmd/master/notes.html",
        {
            "programmes": programmes
        }
    )


from django.shortcuts import render
from .models import EtudiantLMD


from .models import EtudiantMaster


from django.shortcuts import render
from .models import EtudiantMaster


def master_bulletin_list(request):

    etudiants = EtudiantMaster.objects.select_related(
        "programme",
        "programme__filiere"
    ).filter(
        programme__specialite__in=[
            "DROIT",
            "GESTION",
            "QHSE"
        ]
    )


    # ==========================
    # FILTRE MATRICULE
    # ==========================
    matricule = request.GET.get("matricule")

    if matricule:
        etudiants = etudiants.filter(
            matricule__icontains=matricule
        )


    # ==========================
    # FILTRE NIVEAU
    # ==========================
    niveau = request.GET.get("niveau")

    if niveau:
        etudiants = etudiants.filter(
            niveau=niveau
        )


    # ==========================
    # FILTRE FILIERE
    # ==========================
    specialite = request.GET.get("specialite")

    if specialite:
        etudiants = etudiants.filter(
            programme__specialite=specialite
        )


    context = {

        "etudiants": etudiants,

        "matricule": matricule or "",

        "niveau": niveau or "",

        "specialite": specialite or "",

    }


    return render(
        request,
        "lmd/master/bulletins.html",
        context
    )

def master_bulletin_pdfES(request, id):

    etudiant = get_object_or_404(
        EtudiantLMD,
        id=id
    )

    # création fichier PDF temporaire
    temp_dir = os.path.join(
        settings.MEDIA_ROOT,
        "bulletins_master"
    )

    os.makedirs(
        temp_dir,
        exist_ok=True
    )

    file_path = os.path.join(
        temp_dir,
        f"bulletin_{etudiant.matricule}.pdf"
    )


    # Génération PDF
    generer_bulletin_masters_pdf(
        etudiant,
        file_path
    )


    # affichage dans navigateur
    return FileResponse(
        open(file_path, "rb"),
        content_type="application/pdf"
    )

def master_bulletin_pdf(request, id):

    etudiant = get_object_or_404(
        EtudiantMaster,
        id=id
    )

    file_path = os.path.join(
        settings.MEDIA_ROOT,
        f"bulletin_master_{etudiant.matricule}.pdf"
    )


    generer_bulletin_masters_pdf(
        etudiant,
        file_path
    )


    with open(file_path, "rb") as pdf:
        response = HttpResponse(
            pdf.read(),
            content_type="application/pdf"
        )

    response["Content-Disposition"] = (
        f'inline; filename="bulletin_{etudiant.matricule}.pdf"'
    )

    return response

def l3_droit_ecue_add(request, pk):

    ue = get_object_or_404(
        UE,
        pk=pk
    )
    
    if request.method == "POST":
        form = ECUEForm(request.POST)

        if form.is_valid():
            ecue = form.save(commit=False)
            ecue.ue = ue
            ecue.save()

            return redirect(
                "l3_droit_ecue",
                pk=ue.id
            )

    else:

        form = ECUEForm()

    return render(
        request,
        "lmd/l3/droit/ecue_form.html",
        {
            "form": form,
            "ue": ue
        }
    )
    

def l3_droit_saisie_notes(request, ecue_id):

    ecue = get_object_or_404(
        ECUE,
        id=ecue_id
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere=ecue.ue.filiere,
        niveau="L3"
    )


    notes_existantes = NoteLMD.objects.filter(
        ecue=ecue
    )


    notes_dict = {
        note.etudiant_id: note
        for note in notes_existantes
    }


    etudiants_notes = []


    for etudiant in etudiants:

        etudiants_notes.append({

            "etudiant": etudiant,

            "note": notes_dict.get(etudiant.id)

        })



    if request.method == "POST":


        for item in etudiants_notes:

            etudiant = item["etudiant"]


            cc = request.POST.get(
                f"cc_{etudiant.id}"
            )

            examen = request.POST.get(
                f"examen_{etudiant.id}"
            )



            if cc or examen:


                NoteLMD.objects.update_or_create(

                    etudiant=etudiant,

                    ecue=ecue,

                    defaults={

                        "cc": cc or 0,

                        "examen": examen or 0

                    }

                )


        return redirect(
            "l3_droit_ecue",
            pk=ecue.ue.id
        )



    return render(
        request,
        "lmd/l3/droit/saisie_notes.html",
        {
            "ecue": ecue,
            "etudiants_notes": etudiants_notes
        }
    )
# ==============================
# Liste des ECUE d'une UE
# ==============================

def l3_droit_ecue(request, pk):

    ue = get_object_or_404(
        UE,
        id=pk
    )

    ecues = ECUE.objects.filter(
        ue=ue
    )


    return render(
        request,
        "lmd/l3/droit/ecue.html",
        {
            "ue": ue,
            "ecues": ecues
        }
    )



# ==============================
# Ajouter ECUE
# ==============================


# ==============================
# Modifier ECUE
# ==============================

def l3_droit_ecue_update(request, pk):

    ecue = get_object_or_404(
        ECUE,
        pk=pk
    )


    if request.method == "POST":

        form = ECUEForm(
            request.POST,
            instance=ecue
        )

        if form.is_valid():

            form.save()

            return redirect(
                "l3_droit_ecue",
                pk=ecue.ue.pk
            )


    else:

        form = ECUEForm(
            instance=ecue
        )


    return render(
        request,
        "lmd/l3/droit/ecue_form.html",
        {
            "form": form,
            "titre": "Modifier ECUE",
            "ue": ecue.ue,
            "ecue": ecue
        }
    )

# ==============================
# Supprimer ECUE
# ==============================

def l3_droit_ecue_delete(request, pk):

    ecue = get_object_or_404(
        ECUE,
        id=pk
    )

    ue_id = ecue.ue.id

    ecue.delete()


    return redirect(
        "l3_droit_ecue",
        pk=ue_id
    )



def l3_sciences_gestion_etudiants(request):

    etudiants = EtudiantLMD.objects.filter(
        filiere__libelle__icontains="Sciences de Gestion",
        niveau="L3"
    ).order_by(
        "nom",
        "prenoms"
    )

    return render(
        request,
        "lmd/l3/gestion/etudiants.html",
        {
            "etudiants": etudiants
        }
    )


from django.http import HttpResponse



def imprimer_bulletin_l3_droit_prive(request, pk):

    etudiant = get_object_or_404(
        EtudiantLMD,
        id=pk
    )

    # dossier temporaire PDF
    pdf_dir = os.path.join(
        settings.MEDIA_ROOT,
        "bulletins"
    )

    os.makedirs(
        pdf_dir,
        exist_ok=True
    )

    file_path = os.path.join(
        pdf_dir,
        f"bulletin_{etudiant.matricule}.pdf"
    )


    generer_bulletin_droit_prive_pdf(
        etudiant,
        file_path
    )


    return FileResponse(
        open(file_path, "rb"),
        content_type="application/pdf"
    )


def liste_bulletins_l3_droit_prive(request):

    filiere = get_object_or_404(
        FiliereLMD,
        libelle="Droit Privé"
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau="L3"
    ).order_by(
        "nom",
        "prenoms"
    )

    return render(
        request,
        "lmd/l3/droit/bulletins.html",
        {
            "etudiants": etudiants,
            "filiere": filiere
        }
    )


def l3_gestion_etudiant_list(request):

    etudiants = EtudiantLMD.objects.filter(
        filiere__libelle__icontains="Sciences de Gestion",
        niveau="L3"
    ).order_by(
        "nom",
        "prenoms"
    )


    return render(
        request,
        "lmd/l3/gestion/list.html",
        {
            "etudiants": etudiants
        }
    )


def l3_gestion_etudiant_add(request):

    if request.method == "POST":

        form = EtudiantGestionForm(request.POST)

        print("=== POST RECU ===")
        print(request.POST)

        if form.is_valid():

            print("=== FORMULAIRE VALIDE ===")

            etudiant = form.save(commit=False)

            etudiant.niveau = "L3"

            etudiant.filiere = FiliereLMD.objects.get(
                libelle__icontains="Sciences de Gestion"
            )

            etudiant.save()

            print("=== ETUDIANT ENREGISTRE ===")

            return redirect(
                "l3_gestion_etudiant_list"
            )

        else:

            print("=== ERREURS FORMULAIRE ===")
            print(form.errors)

    else:

        form = EtudiantGestionForm()


    return render(
        request,
        "lmd/l3/gestion/etud_form.html",
        {
            "form": form
        }
    )

def l3_gestion_etudiant_edit(request, pk):

    etudiant = get_object_or_404(
        EtudiantLMD,
        pk=pk
    )


    form = EtudiantGestionForm(
        request.POST or None,
        instance=etudiant
    )


    if form.is_valid():

        form.save()

        return redirect(
            "l3_gestion_etudiant_list"
        )


    return render(
        request,
        "lmd/l3/gestion/etud_form.html",
        {
            "form":form
        }
    )

def l3_gestion_etudiant_delete(request, pk):

    etudiant = get_object_or_404(
        EtudiantLMD,
        pk=pk
    )


    if request.method == "POST":

        etudiant.delete()

        return redirect(
            "l3_gestion_etudiant_list"
        )


    return render(
        request,
        "lmd/l3/gestion/delete.html",
        {
            "etudiant":etudiant
        }
    )

def l3_gestion_ue_list(request):

    ues = UE.objects.filter(
        filiere__libelle__icontains="Sciences de Gestion"
    ).order_by("code")

    return render(
        request,
        "lmd/l3/gestion/ue/list.html",
        {
            "ues": ues
        }
    )


def l3_gestion_ue_add(request):

    if request.method == "POST":

        form = UEForm(request.POST)

        if form.is_valid():

            ue = form.save(commit=False)

            ue.filiere = FiliereLMD.objects.get(
                libelle__icontains="Sciences de Gestion"
            )

            ue.save()

            return redirect("l3_gestion_ue")

    else:

        form = UEForm()

    return render(
        request,
        "lmd/l3/gestion/ue/form.html",
        {
            "form": form
        }
    )
    
def l3_gestion_ecue_list(request, ue_id):

    ue = get_object_or_404(UE, pk=ue_id)

    ecues = ue.ecues.all().order_by("code")

    return render(
        request,
        "lmd/l3/gestion/ecue/list.html",
        {
            "ue": ue,
            "ecues": ecues
        }
    )

def l3_gestion_ecue_add(request, ue_id):

    ue = get_object_or_404(UE, pk=ue_id)

    if request.method == "POST":

        form = ECUEForm(request.POST)

        if form.is_valid():

            ecue = form.save(commit=False)

            ecue.ue = ue

            ecue.save()

            return redirect(
                "l3_gestion_ecue_list",
                ue.id
            )

    else:

        form = ECUEForm()

    return render(
        request,
        "lmd/l3/gestion/ecue/form.html",
        {
            "form": form,
            "ue": ue
        }
    )


def l3_gestion_saisie_notes(request, ecue_id):

    ecue = get_object_or_404(
        ECUE,
        id=ecue_id
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere__libelle="Sciences de Gestion",
        niveau="L3"
    )


    if request.method == "POST":

        for etudiant in etudiants:

            cc = request.POST.get(
                f"cc_{etudiant.id}"
            )

            examen = request.POST.get(
                f"examen_{etudiant.id}"
            )


            NoteLMD.objects.update_or_create(
                etudiant=etudiant,
                ecue=ecue,
                defaults={
                    "cc": float(cc or 0),
                    "examen": float(examen or 0)
                }
            )


        return redirect(
            "l3_gestion_notes"
        )


    return render(
        request,
        "lmd/l3/gestion/notes/saisie.html",
        {
            "ecue": ecue,
            "etudiants": etudiants
        }
    )

def l3_gestion_ue_edit(request, pk):

    ue = get_object_or_404(
        UE,
        id=pk
    )

    if request.method == "POST":

        form = UEForm(
            request.POST,
            instance=ue
        )

        if form.is_valid():

            form.save()

            return redirect(
                "l3_gestion_ue"
            )

    else:

        form = UEForm(
            instance=ue
        )


    return render(
        request,
        "lmd/l3/gestion/ue/form.html",
        {
            "form": form
        }
    )

def l3_gestion_ue_delete(request, pk):

    ue = get_object_or_404(
        UE,
        id=pk
    )

    if request.method == "POST":

        ue.delete()

        return redirect(
            "l3_gestion_ue"
        )


    return render(
        request,
        "lmd/l3/gestion/ue/delete.html",
        {
            "ue": ue
        }
    )

def l3_gestion_ecue_add(request, ue_id):

    ue = get_object_or_404(
        UE,
        id=ue_id
    )


    if request.method == "POST":

        form = ECUEForm(request.POST)

        if form.is_valid():

            ecue = form.save(commit=False)

            ecue.ue = ue

            ecue.save()

            return redirect(
                "l3_gestion_ecue_list",
                ue.id
            )

    else:

        form = ECUEForm()


    return render(
        request,
        "lmd/l3/gestion/ecue/form.html",
        {
            "form": form,
            "ue": ue
        }
    )

from django.shortcuts import get_object_or_404, redirect, render
from .models import ECUE


def l3_gestion_ecue_edit(request, pk):

    ecue = get_object_or_404(
        ECUE,
        id=pk
    )


    if request.method == "POST":

        ecue.code = request.POST.get("code")
        ecue.libelle = request.POST.get("libelle")
        ecue.coefficient = request.POST.get("coefficient")
        ecue.credit = request.POST.get("credit")

        ecue.save()

        return redirect(
            "l3_gestion_ecue_list",
            ecue.ue.id
        )


    return render(
        request,
        "lmd/l3/gestion/ecue/edit.html",
        {
            "ecue": ecue
        }
    )

def l3_gestion_ecue_delete(request, pk):

    ecue = get_object_or_404(
        ECUE,
        id=pk
    )

    ue_id = ecue.ue.id


    if request.method == "POST":

        ecue.delete()

        return redirect(
            "l3_gestion_ecue_list",
            ue_id
        )


    return render(
        request,
        "lmd/l3/gestion/ecue/delete.html",
        {
            "ecue": ecue
        }
    )

def liste_bulletins_gestion(request):

    filiere = get_object_or_404(
        FiliereLMD,
        libelle="Sciences de Gestion"
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere
    ).order_by("nom", "prenoms")

    print("========== TEST ==========")
    print("Filière :", filiere.libelle)
    print("Nombre d'étudiants :", etudiants.count())

    for e in etudiants:
        print(e.matricule, e.nom, e.prenoms)

    return render(
        request,
        "lmd/l3/gestion/bulletins.html",
        {
            "etudiants": etudiants,
            "filiere": filiere
        }
    )

def bulletin_gestion_lmd_pdf(request, etudiant_id):

    etudiant = get_object_or_404(
        EtudiantLMD,
        id=etudiant_id
    )

    filename = f"bulletin_{etudiant.matricule}.pdf"

    filepath = os.path.join(
        settings.MEDIA_ROOT,
        "bulletins",
        filename
    )

    os.makedirs(
        os.path.dirname(filepath),
        exist_ok=True
    )


    generer_bulletin_gestion_pdf(
        etudiant,
        filepath
    )


    return FileResponse(
        open(filepath, "rb"),
        content_type="application/pdf"
    )

def liste_bulletins_tronc_commun(request):

    etudiants = EtudiantLMD.objects.filter(
        filiere__libelle="Gestion et Droit",
        niveau__in=["L1", "L2"]
    ).order_by(
        "niveau",
        "nom",
        "prenoms"
    )

    return render(
        request,
        "lmd/trom_commun/bulletins.html",
        {
            "etudiants": etudiants,
            "titre": "Bulletins Tronc Commun L1 - L2"
        }
    )


def imprimer_bulletin_tronc_commun(request, pk):

    etudiant = get_object_or_404(
        EtudiantLMD,
        pk=pk
    )


    pdf_dir = os.path.join(
        settings.MEDIA_ROOT,
        "bulletins"
    )


    os.makedirs(
        pdf_dir,
        exist_ok=True
    )


    file_path = os.path.join(
        pdf_dir,
        f"tronc_commun_{etudiant.matricule}.pdf"
    )


    generer_bulletin_tronc_commun_pdf(
        etudiant,
        semestre,
        file_path
    )


    return FileResponse(
        open(file_path,"rb"),
        content_type="application/pdf"
    )


def ajouter_etudiant_tronc_commun(request):

    if request.method == "POST":

        matricule = request.POST.get("matricule")
        nom = request.POST.get("nom")
        prenoms = request.POST.get("prenoms")
        niveau_id = request.POST.get("niveau")


        filiere = FiliereLMD.objects.get(
            code="TC-DG"
        )


        EtudiantLMD.objects.create(
            matricule=matricule,
            nom=nom,
            prenoms=prenoms,
            filiere=filiere,
            niveau_id=niveau_id
        )


        return redirect(
            "liste_etudiants_tronc_commun"
        )


    niveaux = NiveauLMD.objects.filter(
        code__in=["L1","L2"]
    )


    return render(
        request,
        "lmd/add_etudiant_tc.html",
        {
            "niveaux": niveaux
        }
    )

def tronc_commun_etudiants(request):

    etudiants = EtudiantLMD.objects.filter(
        niveau__in=["L1", "L2"],
        filiere__libelle__in=[
            "Droit",
            "Gestion"
        ]
    ).select_related(
        "filiere"
    ).order_by(
        "filiere__libelle",
        "niveau",
        "nom",
        "prenoms"
    )


    filiere = request.GET.get("filiere")
    niveau = request.GET.get("niveau")


    if filiere:
        etudiants = etudiants.filter(
            filiere_id=filiere
        )


    if niveau:
        etudiants = etudiants.filter(
            niveau=niveau
        )


    context = {

        "etudiants": etudiants,


        "filieres": [
            {
                "id": f.id,
                "libelle": f.libelle
            }
            for f in FiliereLMD.objects.filter(
                libelle__in=[
                    "Droit",
                    "Gestion"
                ]
            )
        ],


        "niveaux":[
            "L1",
            "L2"
        ]

    }


    return render(
        request,
        "lmd/tronc_commun_etudiants.html",
        context
    )

def tronc_commun_ue(request):

    ues = UE.objects.filter(
        filiere__libelle="Gestion et Droit"
    ).prefetch_related(
        "ecues"
    ).order_by(
        "code"
    )

    return render(
        request,
        "lmd/trom_commun/ue.html",
        {
            "ues": ues,
            "titre": "UE / ECUE Tronc Commun L1-L2 Droit & Gestion"
        }
    )

def tronc_commun_notes(request):

    filiere = get_object_or_404(
        FiliereLMD,
        Q(libelle="Gestion et Droit") |
        Q(libelle="Droit et Gestion")
    )

    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau__in=["L1", "L2"]
    )


    ecues = ECUE.objects.filter(
        ue__filiere=filiere
    ).order_by(
        "code"
    )


    notes = NoteLMD.objects.filter(
        etudiant__in=etudiants,
        ecue__in=ecues
    )


    # Indexation des notes existantes
    notes_existantes = {}

    for note in notes:

        notes_existantes[
            (
                note.etudiant_id,
                note.ecue_id
            )
        ] = note



    # Préparation affichage des notes
    for etudiant in etudiants:

        etudiant.notes_affichage = []

        for ecue in ecues:

            note = notes_existantes.get(
                (
                    etudiant.id,
                    ecue.id
                )
            )


            etudiant.notes_affichage.append(
                {
                    "ecue_id": ecue.id,
                    "cc": note.cc if note else "",
                    "examen": note.examen if note else "",
                }
            )


    return render(
        request,
        "lmd/trom_commun/notes.html",
        {
            "etudiants": etudiants,
            "ecues": ecues,
        }
    )

def tronc_commun_noteseeee(request):

    filiere = get_object_or_404(
        FiliereLMD,
        Q(libelle="Gestion et Droit") |
        Q(libelle="Droit et Gestion")
    )


    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau__in=["L1", "L2"]
    )


    ecues = ECUE.objects.filter(
        ue__filiere=filiere
    ).order_by(
        "code"
    )


    notes = NoteLMD.objects.filter(
        etudiant__in=etudiants,
        ecue__in=ecues
    )


    # Préparer les notes pour le template
    notes_existantes = {}

    for note in notes:

        key = (
            note.etudiant.id,
            note.ecue.id
        )

        notes_existantes[key] = note


    # Ajouter les notes dans les étudiants
    for etudiant in etudiants:

        etudiant.notes_affichage = {}

        for ecue in ecues:

            key = (
                etudiant.id,
                ecue.id
            )

            etudiant.notes_affichage[ecue.id] = notes_existantes.get(key)


    return render(
        request,
        "lmd/trom_commun/notes.html",
        {
            "etudiants": etudiants,
            "ecues": ecues,
        }
    )
# =====================================================
# TRONC COMMUN L1/L2 - DROIT + GESTION
# =====================================================
def liste_etudiants_tronc_commun(request):

    etudiants = EtudiantLMD.objects.filter(
        Q(filiere__libelle__icontains="Droit")
        |
        Q(filiere__libelle__icontains="Gestion"),
        niveau__in=[
            "L1",
            "L2",
            "Licence 1",
            "Licence 2"
        ]
    ).order_by(
        "niveau",
        "nom"
    )


    return render(
        request,
        "lmd/tronc_commun/etudiants.html",
        {
            "etudiants": etudiants,
            "titre":"Tronc Commun Droit & Gestion L1-L2"
        }
    )
# Vue spéciale Droit
def tronc_commun_droit(request):

    etudiants = EtudiantLMD.objects.filter(
        niveau__in=["L1","L2"],
        filiere__libelle__icontains="Droit"
    )

    return render(
        request,
        "lmd/tronc_commun/etudiants.html",
        {
            "etudiants":etudiants,
            "titre":"Tronc Commun Droit L1-L2"
        }
    )



# Vue spéciale Gestion
def tronc_commun_gestion(request):

    etudiants = EtudiantLMD.objects.filter(
        niveau__in=["L1","L2"],
        filiere__libelle__icontains="Gestion"
    )


    return render(
        request,
        "lmd/tronc_commun/etudiants.html",
        {
            "etudiants":etudiants,
            "titre":"Tronc Commun Gestion L1-L2"
        }
    )



# =====================================================
# UE TRONC COMMUN
# =====================================================

# =====================================================
# LISTE BULLETINS
# =====================================================

def bulletin_tronc_commun_list(request):

    etudiants = EtudiantLMD.objects.filter(
        niveau__in=["L1","L2"]
    )


    return render(
        request,
        "lmd/tronc_commun/bulletins.html",
        {
            "etudiants":etudiants
        }
    )    

def liste_etudiants_tronc_commun(request):

    etudiants = EtudiantLMD.objects.filter(
        filiere__libelle="Gestion et Droit",
        niveau__in=["L1", "L2"]
    ).order_by(
        "niveau",
        "nom",
        "prenoms"
    )


    return render(
        request,
        "lmd/trom_commun/etudiants.html",
        {
            "etudiants": etudiants,
            "titre": "Étudiants Tronc Commun Gestion et Droit L1-L2"
        }
    )

def bulletin_tronc_commun_pdfBBBB(request, id, semestre):

    etudiant = get_object_or_404(
        EtudiantLMD,
        id=id
    )

    # Accepte "1", "2", "S1" ou "S2"
    if not str(semestre).startswith("S"):
        semestre = f"S{semestre}"

    pdf_dir = os.path.join(
        settings.MEDIA_ROOT,
        "bulletins"
    )

    os.makedirs(
        pdf_dir,
        exist_ok=True
    )

    fichier = os.path.join(
        pdf_dir,
        f"bulletin_{etudiant.matricule}_{semestre}.pdf"
    )

    generer_bulletin_tronc_commun_pdf(
        etudiant,
        semestre,
        fichier
    )

    return FileResponse(
        open(fichier, "rb"),
        content_type="application/pdf"
    )

def bulletin_tronc_commun_pdf(request, id, semestre):

    etudiant = get_object_or_404(
        EtudiantLMD,
        id=id
    )

    pdf_dir = os.path.join(
        settings.MEDIA_ROOT,
        "bulletins"
    )

    os.makedirs(pdf_dir, exist_ok=True)

    file_path = os.path.join(
        pdf_dir,
        f"tronc_commun_{etudiant.matricule}_{semestre}.pdf"
    )

    generer_bulletin_tronc_commun_pdf(
        etudiant,
        file_path,
        semestre
        
    )
  

    return FileResponse(

        open(file_path, "rb"),
        content_type="application/pdf"
    )
 
from .forms import TroncCommunEtudiantForm



def tronc_commun_add(request):

    if request.method == "POST":

        form = TroncCommunEtudiantForm(request.POST)


        if form.is_valid():

            etudiant = form.save()

            messages.success(
                request,
                "Étudiant ajouté avec succès"
            )

            return redirect(
                "liste_bulletins_tronc_commun"
            )


    else:

        form = TroncCommunEtudiantForm()



    return render(
        request,
        "lmd/trom_commun/form.html",
        {
            "form":form,
            "titre":"Ajouter étudiant tronc commun"
        }
    )




def tronc_commun_update(request, pk):

    etudiant = get_object_or_404(
        EtudiantLMD,
        pk=pk
    )

    if request.method == "POST":

        form = TroncCommunEtudiantForm(
            request.POST,
            request.FILES,
            instance=etudiant
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Modification de l'étudiant effectuée avec succès."
            )

            return redirect(
                "liste_bulletins_tronc_commun"
            )

    else:

        form = TroncCommunEtudiantForm(
            instance=etudiant
        )


    context = {
        "form": form,
        "titre": "Modifier étudiant"
    }


    return render(
        request,
        "lmd/trom_commun/form.html",
        context
    )





# =====================================================
# DASHBOARD QHSE L3
# =====================================================

def l3_qhse_dashboard(request):

    filiere = FiliereLMD.objects.filter(
        code="QHSE"
    ).first()


    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau="L3"
    ).count()


    ues = UE.objects.filter(
        filiere=filiere
    ).count()



    context = {

        "filiere": filiere,

        "nb_etudiants": etudiants,

        "nb_ues": ues,

    }


    return render(
        request,
        "lmd/l3_qhse/dashboard.html",
        context
    )



# =====================================================
# ETUDIANTS QHSE
# =====================================================

def l3_qhse_etudiants1(request):

    filiere = FiliereLMD.objects.get(code="QHSE-L3")

    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau="L3"
    )

    print("Nombre =", etudiants.count())

    return render(
        request,
        "lmd/l3_qhse/etudiants.html",
        {
            "etudiants": etudiants,
            "filiere": filiere,
        }
    )

def l3_qhse_etudiants(request):

    filiere = FiliereLMD.objects.get(code="QHSE-L3")

    etudiants = EtudiantLMD.objects.filter(
         filiere=filiere,
        niveau="L3"
    )

    print("Nombre =", etudiants.count())

    for e in etudiants:
        print(e.id, e.matricule, e.nom, e.prenoms)

    return render(
        request,
        "lmd/l3_qhse/etudiants.html",
        {
            "etudiants": etudiants,
            "filiere": filiere,
        }
    )

def l3_qhse_etudiant_add(request):

    filiere = FiliereLMD.objects.get(
        code="QHSE-L3"
    )

    if request.method == "POST":

        form = QHSEEtudiantForm(request.POST)

        if form.is_valid():

            etudiant = form.save(commit=False)

            etudiant.filiere = filiere
            etudiant.niveau = "L3"

            etudiant.save()

            return redirect(
                "l3_qhse_etudiants"
            )

    else:

        form = QHSEEtudiantForm()


    return render(
        request,
        "lmd/l3_qhse/etudiant_form.html",
        {
            "form": form,
            "filiere": filiere
        }
    )
def l3_qhse_etudiant_addSS(request):

    filiere = FiliereLMD.objects.get(
        libelle="Management de la Qualité, Hygiène, Sécurité et Environnement"
    )


    if request.method=="POST":

        form = QHSEEtudiantForm(request.POST)


        if form.is_valid():

            etudiant=form.save(commit=False)

            etudiant.filiere=filiere
            etudiant.niveau="L3"

            etudiant.save()


            messages.success(
                request,
                "Étudiant QHSE ajouté"
            )


            return redirect(
                "l3_qhse_etudiants"
            )


    else:

        form=QHSEEtudiantForm()



    return render(
        request,
        "lmd/qhse/etudiant_form.html",
        {
            "form":form,
            "titre":"Ajouter étudiant L3 QHSE"
        }
    )

def l3_qhse_etudiant_update(request,pk):

    etudiant=get_object_or_404(
        EtudiantLMD,
        pk=pk
    )


    if request.method=="POST":

        form=QHSEEtudiantForm(
            request.POST,
            instance=etudiant
        )


        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Modification effectuée"
            )

            return redirect(
                "l3_qhse_etudiants"
            )


    else:

        form=QHSEEtudiantForm(
            instance=etudiant
        )


    return render(
        request,
        "lmd/l3_qhse/etudiant_form.html",
        {
            "form":form,
            "titre":"Modifier étudiant QHSE"
        }
    )

def l3_qhse_etudiant_delete(request,pk):

    etudiant=get_object_or_404(
        EtudiantLMD,
        pk=pk
    )


    if request.method=="POST":

        etudiant.delete()

        messages.success(
            request,
            "Étudiant supprimé"
        )


        return redirect(
            "l3_qhse_etudiants"
        )


    return render(
        request,
        "lmd/l3_qhse/etudiant_delete.html",
        {
            "etudiant":etudiant
        }
    )
# =====================================================
# UE / ECUE QHSE
# =====================================================

def l3_qhse_ue(request):

    filiere = FiliereLMD.objects.filter(
        code="QHSE"
    ).first()


    ues = UE.objects.filter(
        # filiere=filiere
        filiere__code__in=["QHSE", "QHSE-L3"]
    ).prefetch_related(
        "ecues"
    ).order_by("code")


    return render(
        request,
        "lmd/l3_qhse/ue.html",
        {
            "ues": ues,
            "filiere": filiere
        }
    )



# =====================================================
# SAISIE NOTES QHSE
# =====================================================

def l3_qhse_notes(request):

    filiere = FiliereLMD.objects.filter(
        code="QHSE"
    ).first()


    notes = NoteLMD.objects.filter(
        etudiant__filiere=filiere
    ).select_related(
        "etudiant",
        "ecue"
    )


    return render(
        request,
        "lmd/l3_qhse/notes.html",
        {
            "notes": notes,
            "filiere": filiere
        }
    )



# =====================================================
# BULLETINS QHSE
# =====================================================

def l3_qhse_bulletins(request):

    filiere = FiliereLMD.objects.get(
        code="QHSE-L3"
    )


    etudiants = EtudiantLMD.objects.filter(
        filiere=filiere,
        niveau="L3"
    ).select_related(
        "filiere"
    )


    print("Filière :", filiere)
    print("Nombre étudiants :", etudiants.count())


    for e in etudiants:
        print(
            e.id,
            e.matricule,
            e.nom,
            e.prenoms
        )


    return render(
        request,
        "lmd/l3_qhse/bulletins.html",
        {
            "etudiants": etudiants,
            "filiere": filiere
        }
    )



def l3_qhse_ecue_add(request, ue_id):

    ue = get_object_or_404(
        UE,
        id=ue_id
    )


    if request.method == "POST":

        form = QHSEECUEForm(request.POST)


        if form.is_valid():

            ecue = form.save(commit=False)

            # rattachement automatique
            ecue.ue = ue

            ecue.save()


            messages.success(
                request,
                "ECUE ajouté avec succès"
            )


            return redirect(
                "l3_qhse_ue"
            )


    else:

        form = QHSEECUEForm()



    return render(
        request,
        "lmd/l3_qhse/ecue_form.html",
        {
            "form":form,
            "ue":ue,
            "titre":"Ajouter un ECUE"
        }
    )


def l3_qhse_ecue_update(request, pk):

    ecue = get_object_or_404(ECUE, pk=pk)


    if request.method == "POST":

        ecue.code = request.POST.get("code")
        ecue.libelle = request.POST.get("libelle")
        ecue.coefficient = request.POST.get("coefficient")
        ecue.credit = request.POST.get("credit")

        ecue.save()

        return redirect("l3_qhse_ue")


    return render(
        request,
        "lmd/l3_qhse/ecue_update.html",
        {
            "ecue": ecue
        }
    )



def l3_qhse_ecue_delete(request, pk):

    ecue = get_object_or_404(
        ECUE,
        pk=pk
    )


    if request.method == "POST":

        ue = ecue.ue

        ecue.delete()

        return redirect(
            "l3_qhse_ue"
        )


    return redirect(
        "l3_qhse_ue"
    )




def l3_qhse_ue_add(request):

    filiere = FiliereLMD.objects.get(
        libelle="Management de la Qualité, Hygiène, Sécurité et Environnement"
    )


    if request.method == "POST":

        UE.objects.create(

            code=request.POST.get("code"),

            libelle=request.POST.get("libelle"),

            credit=request.POST.get("credit"),

            filiere=filiere
        )


        return redirect(
            "l3_qhse_ue"
        )


    return render(
        request,
        "lmd/l3_qhse/ue_add.html"
    )

def l3_qhse_ue_update(request, pk):

    ue = get_object_or_404(
        UE,
        pk=pk
    )


    if request.method == "POST":

        ue.code = request.POST.get("code")
        ue.libelle = request.POST.get("libelle")
        ue.credit = request.POST.get("credit")

        ue.save()

        return redirect(
            "l3_qhse_ue"
        )


    return render(
        request,
        "lmd/l3_qhse/ue_update.html",
        {
            "ue": ue
        }
    )

def l3_qhse_ue_delete(request, pk):

    ue = get_object_or_404(
        UE,
        pk=pk
    )


    if request.method == "POST":

        ue.delete()

        return redirect(
            "l3_qhse_ue"
        )


    return redirect(
        "l3_qhse_ue"
    )

def master_uePAS(request, id):

    programme = get_object_or_404(
        MasterProgramme,
        id=id
    )

    ues = MasterUE.objects.filter(
        programme=programme
    )

    return render(
        request,
        "lmd/master/ue_list.html",
        {
            "programme": programme,
            "ues": ues,
        }
    )
def master_ue(request, id):

    programme = get_object_or_404(
        MasterProgramme,
        id=id
    )


    ues = MasterUE.objects.filter(
        programme=programme
    ).prefetch_related(
        "ecues"
    )



    return render(
        request,
        "lmd/master/ue_list.html",
        {
            "programme": programme,
            "ues": ues
        }
    )
 
def master_ue_add(request,id):

    programme = get_object_or_404(
        MasterProgramme,
        id=id
    )


    if request.method=="POST":


        MasterUE.objects.create(

            programme=programme,

            code=request.POST["code"],

            libelle=request.POST["libelle"],

            credit=request.POST["credit"],

            semestre=request.POST["semestre"]

        )


        messages.success(
            request,
            "UE ajoutée avec succès"
        )


        return redirect(
            "master_ue",
            id=id
        )



    return render(
        request,
        "lmd/master/ue_form.html",
        {
            "programme":programme
        }
    )


def master_ue_edit(request,id):

    ue = get_object_or_404(
        MasterUE,
        id=id
    )


    if request.method=="POST":

        form = MasterUEForm(
            request.POST,
            instance=ue
        )


        if form.is_valid():

            form.save()

            return redirect(
                "master_ue",
                ue.programme.id
            )


    else:

        form = MasterUEForm(
            instance=ue
        )


    return render(
        request,
        "lmd/master/ue_form.html",
        {
            "form":form,
            "titre":"Modifier UE Master"
        }
    )

def master_ue_delete(request,id):

    ue = get_object_or_404(
        MasterUE,
        id=id
    )

    programme_id = ue.programme.id


    ue.delete()


    return redirect(
        "master_ue",
        programme_id
    )

def master_ecue(request, id):

    ue = get_object_or_404(
        MasterUE,
        id=id
    )


    ecues = ue.ecues.all()


    return render(
        request,
        "lmd/master/ecue_list.html",
        {
            "ue": ue,
            "ecues": ecues
        }
    )
    
def master_ecue_add(request, id):

    ue = get_object_or_404(
        MasterUE,
        id=id
    )


    if request.method == "POST":


        form = MasterECUEForm(
            request.POST
        )


        if form.is_valid():


            ecue = form.save(
                commit=False
            )


            ecue.ue = ue


            ecue.save()


            return redirect(
                "master_ecue",
                ue.id
            )


    else:


        form = MasterECUEForm()



    return render(
        request,
        "lmd/master/ecue_form.html",
        {
            "form":form,
            "titre":"Ajouter ECUE",
            "ue":ue
        }
    ) 
    
def master_programme_list(request):
    programmes = MasterProgramme.objects.all()

    return render(
        request,
        "lmd/master/programmes/master_programme_list.html",
        {
            "programmes": programmes
        }
    )
    
    
def imprimer_bulletin_licence_qhse1(request, pk):

    etudiant = get_object_or_404(
        EtudiantLMD,
        pk=pk
    )

    pdf_dir = os.path.join(
        settings.MEDIA_ROOT,
        "bulletins_licence_qhse"
    )

    os.makedirs(
        pdf_dir,
        exist_ok=True
    )

    fichier = os.path.join(
        pdf_dir,
        f"bulletin_{etudiant.matricule}.pdf"
    )

    generer_bulletin_licence_qhse_pdf(
        etudiant,
        fichier
    )

    return FileResponse(
        open(fichier, "rb"),
        content_type="application/pdf",
        filename=f"Bulletin_{etudiant.matricule}.pdf"
    )

def imprimer_bulletin_licence_qhse(request, pk, semestre):

    etudiant = get_object_or_404(
        EtudiantLMD,
        pk=pk
    )


    pdf_dir = os.path.join(
        settings.MEDIA_ROOT,
        "bulletins_licence_qhse"
    )


    os.makedirs(
        pdf_dir,
        exist_ok=True
    )


    fichier = os.path.join(
        pdf_dir,
        f"bulletin_{etudiant.matricule}_{semestre}.pdf"
    )


    generer_bulletin_licence_qhse_pdf(
        etudiant,
        fichier,
        semestre
    )


    return FileResponse(
        open(fichier, "rb"),
        content_type="application/pdf",
        filename=f"Bulletin_{etudiant.matricule}_{semestre}.pdf"
    )


def l3_tc_ue_list(request):

    filiere = get_object_or_404(
        FiliereLMD,
        libelle="Droit et Gestion"
    )


    ues = (
        UE.objects
        .filter(
            filiere=filiere
        )
        .prefetch_related(
            "ecues"
        )
    )


    return render(
        request,
        "lmd/trom_commun/ue.html",
        {
            "ues": ues,
        },
    )
    
def l3_tc_ue_add(request):

    filiere = (
        FiliereLMD.objects
        .filter(
            Q(libelle="Gestion et Droit") |
            Q(libelle="Droit et Gestion")
        )
        .first()
    )


    if not filiere:

        messages.warning(
            request,
            "La filière Tronc Commun n'existe pas. "
            "Veuillez d'abord créer la filière 'Gestion et Droit' "
            "ou 'Droit et Gestion'."
        )

        return redirect("filiere_lmd_list")   # adapte avec ton nom d'URL


    if request.method == "POST":

        form = UEForm(request.POST)

        if form.is_valid():

            ue = form.save(commit=False)
            ue.filiere = filiere
            ue.save()

            messages.success(
                request,
                "UE ajoutée avec succès."
            )

            return redirect("l3_tc_ue_list")


    else:

        form = UEForm()


    return render(
        request,
        "lmd/trom_commun/eu_form.html",
        {
            "form": form,
            "titre": "Ajouter une UE Tronc Commun",
            "filiere": filiere
        }
    )
    
def l3_tc_ue_update(request, pk):

    ue = get_object_or_404(
        UE,
        pk=pk
    )


    if request.method == "POST":

        form = UEForm(
            request.POST,
            instance=ue
        )


        if form.is_valid():

            form.save()

            return redirect(
                "l3_tc_ue_list"
            )


    else:

        form = UEForm(
            instance=ue
        )


    return render(
        request,
        "lmd/trom_commun/eu_form.html",
        {
            "form": form,
            "titre": "Modifier une UE"
        }
    )
    
def l3_tc_ue_delete(request, pk):

    ue = get_object_or_404(
        UE,
        pk=pk
    )


    if request.method == "POST":

        ue.delete()

        return redirect(
            "l3_tc_ue_list"
        )


    return render(
        request,
        "lmd/trom_commun/ue_delete.html",
        {
            "objet": ue
        }
    )

def l3_tc_ecue_add(request, ue_id):

    ue = get_object_or_404(
        UE,
        id=ue_id
    )


    if request.method == "POST":

        form = ECUEForm(request.POST)


        if form.is_valid():

            ecue = form.save(commit=False)

            ecue.ue = ue

            ecue.save()


            return redirect(
                "l3_tc_ue_list"
            )


    else:

        form = ECUEForm()


    return render(
        request,
        "lmd/trom_commun/ecue_form.html",
        {
            "form": form,
            "ue": ue,
            "titre": "Ajouter un ECUE"
        }
    )

def l3_tc_ecue_update(request, pk):

    ecue = get_object_or_404(
        ECUE,
        id=pk
    )


    if request.method == "POST":

        form = ECUEForm(
            request.POST,
            instance=ecue
        )


        if form.is_valid():

            form.save()

            return redirect(
                "l3_tc_ue_list"
            )


    else:

        form = ECUEForm(
            instance=ecue
        )


    return render(
        request,
        "lmd/trom_commun/ecue_form.html",
        {
            "form": form,
            "titre": "Modifier ECUE"
        }
    )
def l3_tc_ecue_delete(request, pk):

    ecue = get_object_or_404(
        ECUE,
        id=pk
    )


    if request.method == "POST":

        ecue.delete()

        return redirect(
            "l3_tc_ue_list"
        )


    return render(
        request,
        "lmd/trom_commun/ecue_delete.html",
        {
            "objet": ecue
        }
    )