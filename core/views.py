# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_protect
from .forms import EtudiantForm,ClasseForm,MatiereForm,AffectationForm,NoteForm
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Filiere
import os
from .services import calcul_moyenne_etudiant
from django.conf import settings
from django.views.generic import ListView
from .models import Filierebts
from django.contrib import messages
from .models import Salle
from .models import SaisieNotesBTS
from .models import (
    Classe,
    Niveau
)
from lmd.models import EtudiantLMD
# from .models import NoteBTS
from lmd.models import EtudiantLMD, FiliereLMD

from .models import (
    Etudiant, Professeur, Classe, Matiere, Note,
    AffectationMatiere, Inscription, Profile
)

from .forms import UserRegisterForm
from .utils import generate_matricule
from .services import (
    calcul_moyenne_etudiant,
    classement_classe,
    mention,
    moyenne_classe
)
from .pdf_service import generate_bulletin_pdf


# =========================
# 🔐 LOGIN
# =========================
@csrf_protect
def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            profile = Profile.objects.filter(user=user).first()

            if not profile:
                return render(request, "login.html", {
                    "error": "Profil utilisateur introuvable"
                })

            if profile.role == "ADMIN":
                return redirect("dashboard_admin")

            elif profile.role == "PROF":
                return redirect("dashboard_prof")

            else:
                return redirect("dashboard_etudiant")

        return render(request, "login.html", {
            "error": "Identifiants incorrects"
        })

    return render(request, "login.html")


# =========================
# 🚪 LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):

    filieres_l3 = FiliereLMD.objects.filter(
        niveau_formation="L3"
    )

    filieres_master = FiliereLMD.objects.filter(
        niveau_formation="M1-M2"
    )

    context = {

        # =====================
        # BTS
        # =====================
        "etudiants_count": Etudiant.objects.count(),
        "professeurs_count": Professeur.objects.count(),
        "classes_count": Classe.objects.count(),
        "matieres_count": Matiere.objects.count(),
        "notes_count": Note.objects.count(),


        # =====================
        # LMD
        # =====================
        "l1_count": EtudiantLMD.objects.filter(
            niveau="L1"
        ).count(),

        "l2_count": EtudiantLMD.objects.filter(
            niveau="L2"
        ).count(),

        "l3_count": EtudiantLMD.objects.filter(
            niveau="L3"
        ).count(),

        "master_count": EtudiantLMD.objects.filter(
            niveau__in=["M1", "M2"]
        ).count(),


        # =====================
        # MENU DYNAMIQUE
        # =====================
        "filieres_l3": filieres_l3,

        "filieres_master": filieres_master,

    }


    return render(
        request,
        "dashboard.html",
        context
    )

# =========================
# 🧑‍💼 ADMIN
# =========================
@login_required
def dashboard_admin(request):

    return render(request, "admin_dashboard.html", {
        "etudiants": Etudiant.objects.count(),
        "professeurs": Professeur.objects.count(),
        "classes": Classe.objects.count(),
    })


# =========================
# 👨‍🏫 PROF
# =========================
@login_required
def dashboard_prof(request):

    prof = Professeur.objects.filter(user=request.user).first()

    if not prof:
        return HttpResponse("❌ Profil professeur introuvable")

    matieres = AffectationMatiere.objects.filter(professeur=prof)

    return render(request, "prof_dashboard.html", {
        "matieres": matieres,
    })


# =========================
# 🎓 ETUDIANT
# =========================
@login_required
def dashboard_etudiant(request):

    etudiant = Etudiant.objects.filter(user=request.user).first()

    if not etudiant:
        return HttpResponse("❌ Aucun profil étudiant trouvé")

    notes = Note.objects.filter(etudiant=etudiant)

    return render(request, "etudiant_dashboard.html", {
        "etudiant": etudiant,
        "notes": notes,
    })


# =========================
# 📝 INSCRIPTION UTILISATEUR
# =========================
def register_user(request):

    if request.method == "POST":

        form = UserRegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            # 🎓 ETUDIANT
            if user.role == "ETUD":

                etudiant = Etudiant.objects.create(
                    user=user,
                    matricule=generate_matricule("ETU"),
                    date_naissance="2000-01-01",
                    sexe="M",
                    telephone="00000000",
                    classe=Classe.objects.first()
                )

                Inscription.objects.create(
                    etudiant=etudiant,
                    classe=etudiant.classe,
                    annee="2025-2026"
                )

            # 👨‍🏫 PROF
            elif user.role == "PROF":

                Professeur.objects.create(
                    user=user,
                    matricule=generate_matricule("PROF"),
                    specialite="Non définie",
                    telephone="00000000"
                )

            return redirect('login')

    else:
        form = UserRegisterForm()

    return render(request, 'register.html', {'form': form})

# =========================
# 📊 BULLETIN ETUDIANT
# =========================
@login_required
def bulletin_etudiant(request):

    etudiant = Etudiant.objects.first()  # ou filtre propre

    if not etudiant:
        return HttpResponse("Aucun étudiant trouvé")

    moyenne = calcul_moyenne_etudiant(etudiant)

    return render(request, "bulletin.html", {
        "etudiant": etudiant,
        "moyenne": moyenne,
        "mention": mention(moyenne),
    })


# =========================
# 📄 PDF BULLETIN
# =========================


def etudiant_list(request):

    query = request.GET.get("q")
    classe_id = request.GET.get("classe")
    filiere_bts_id = request.GET.get("filiere_bts")

    etudiants = Etudiant.objects.select_related(
        "classe",
        "filiere_bts"
    ).all()

    # Recherche
    if query:
        etudiants = etudiants.filter(
            Q(matricule__icontains=query) |
            Q(user__username__icontains=query) |
            Q(prenoms__icontains=query) |
            Q(nom__icontains=query)
        )

    # Filtre classe
    if classe_id:
        etudiants = etudiants.filter(classe_id=classe_id)

    # Filtre filière BTS
    if filiere_bts_id:
        etudiants = etudiants.filter(
            filiere_bts_id=filiere_bts_id
        )

    paginator = Paginator(etudiants, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "etudiants/list.html",
        {
            "page_obj": page_obj,
            "classes": Classe.objects.all(),
            "filieres_bts": Filierebts.objects.all(),
        }
    )


def etudiant_createENC(request):
    form = EtudiantForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("etudiant_list")
    return render(request, "etudiants/form.html", {"form": form})

from .models import Filierebts



def etudiant_create(request):

    if request.method == "POST":

        form = EtudiantForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('etudiant_list')

    else:
        form = EtudiantForm()

    filieres_bts = Filierebts.objects.all()

    return render(request, 'etudiants/form.html', {
        'form': form,
        'filieres_bts': filieres_bts
    })


def etudiants_par_salle(request):

    salles = Salle.objects.prefetch_related(
        'classe_set__etudiants'
    )

    return render(
        request,
        'etudiants/par_salle.html',
        {
            'salles': salles
        }
    )

def etudiant_updateBBBB(request, id):

    etudiant = get_object_or_404(Etudiant, id=id)

    if request.method == "POST":

        etudiant.matricule = request.POST.get('matricule')
        etudiant.nom = request.POST.get('nom')
        etudiant.prenoms = request.POST.get('prenoms')

        filiere_bts_id = request.POST.get('filiere_bts')

        if filiere_bts_id:
            etudiant.filiere_bts = Filierebts.objects.get(
                id=filiere_bts_id
            )
        else:
            etudiant.filiere_bts = None

        etudiant.save()

        return redirect('etudiant_list')

    filieres_bts = Filierebts.objects.all()

    return render(
        request,
        'etudiants/form.html',
        {
            'etudiant': etudiant,
            'filieres_bts': filieres_bts
        }
    )

def etudiant_update(request, id):

    etudiant = get_object_or_404(Etudiant, id=id)

    if request.method == "POST":

        form = EtudiantForm(request.POST, instance=etudiant)

        if form.is_valid():
            form.save()
            return redirect('etudiant_list')

    else:

        form = EtudiantForm(instance=etudiant)

    return render(request, 'etudiants/form.html', {
        'form': form
    })


def etudiant_delete(request, id):
    Etudiant.objects.get(id=id).delete()
    return redirect("etudiant_list")


def classe_listAR(request):

    # 🟢 CREATE
    if request.method == "POST":
        form = ClasseForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("classe_list")
        else:
            print(form.errors)

    else:
        form = ClasseForm()

    # 🟢 FILTERS
    query = request.GET.get("q")
    filiere_bts = request.GET.get("filiere_bts")
    niveau = request.GET.get("niveau")

    # 🟢 QUERYSET OPTIMISÉ
    classes = Classe.objects.select_related(
        "filiere_bts",
        "niveau",
        "salle"
    ).order_by("-id")

    # 🟢 SEARCH
    if query:
        classes = classes.filter(nom__icontains=query)

    # 🟢 FILTER FILIERE BTS
    if filiere_bts:
        classes = classes.filter(filiere_bts__id=filiere_bts)

    # 🟢 FILTER NIVEAU
    if niveau:
        classes = classes.filter(niveau__nom__icontains=niveau)

    # 🟢 PAGINATION
    paginator = Paginator(classes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "classes/list.html", {
        "page_obj": page_obj,
        "form": form
    })


def classe_list(request):

    # ==========================
    # CREATION CLASSE
    # ==========================
    if request.method == "POST":

        form = ClasseForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("classe_list")

        else:
            print(form.errors)

    else:
        form = ClasseForm()



    # ==========================
    # FILTRES
    # ==========================
    query = request.GET.get("q", "")
    filiere_bts = request.GET.get("filiere_bts", "")
    niveau = request.GET.get("niveau", "")



    # ==========================
    # LISTE DES CLASSES
    # ==========================
    classes = Classe.objects.select_related(
        "filiere_bts",
        "niveau",
        "salle"
    ).order_by("-id")



    # Recherche par nom
    if query:
        classes = classes.filter(
            nom__icontains=query
        )


    # Filtre filière BTS
    if filiere_bts:
        classes = classes.filter(
            filiere_bts_id=filiere_bts
        )


    # Filtre niveau
    if niveau:
        classes = classes.filter(
            niveau_id=niveau
        )



    # ==========================
    # PAGINATION
    # ==========================
    paginator = Paginator(
        classes,
        10
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )



    # ==========================
    # DONNEES POUR SELECTS
    # ==========================
    filieres = Filierebts.objects.all()

    niveaux = Niveau.objects.all()  # noqa: F821



    return render(
        request,
        "classes/list.html",
        {
            "page_obj": page_obj,
            "form": form,
            "filieres": filieres,
            "niveaux": niveaux,
            "query": query,
            "filiere_selected": filiere_bts,
            "niveau_selected": niveau,
        }
    )

def classe_create(request):
    if request.method == "POST":
        form = ClasseForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('classe_list')
    else:
        form = ClasseForm()

    return render(request, 'classes/form.html', {
        'form': form
    })


def matiere_list(request):
    query = request.GET.get("q")
    filiere_bts = request.GET.get("filiere_bts")

    matieres = Matiere.objects.select_related("filiere_bts").order_by("-id")

    # 🔎 SEARCH
    if query:
        matieres = matieres.filter(
            Q(code__icontains=query) |
            Q(libelle__icontains=query)
        )

    # 🎯 FILTER BTS
    if filiere_bts:
        matieres = matieres.filter(filiere_bts_id=filiere_bts)

    paginator = Paginator(matieres, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "matieres/list.html", {
        "page_obj": page_obj,
        "filiere_list": Filierebts.objects.all()
    })
    

def matiere_create(request):
    form = MatiereForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("matiere_list")
    return render(request, "matieres/form.html", {"form": form})


from .models import AffectationMatiere

from .forms import AffectationForm


def affectation_list(request):
    return render(request, "affectations/list.html", {
        "affectations": Affectation.objects.select_related(  # noqa: F821
            "professeur", "matiere", "classe"
        )
    })


def affectation_create(request):
    form = AffectationForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect("affectation_list")

    return render(request, "affectations/form.html", {
        "form": form,
        "title": "Affecter professeur"
    })


def affectation_delete(request, id):
    Affectation.objects.get(id=id).delete()  # noqa: F821
    return redirect("affectation_list")

from .models import Note
from .forms import NoteForm


def note_listAAA(request):
    notes = Note.objects.select_related("etudiant", "matiere").all()

    return render(request, "notes/list.html", {
        "notes": notes
    })

def note_listTO(request):
    notes = Note.objects.select_related(
        "etudiant",
        "matiere"
    ).all()

    etudiant_id = request.GET.get("etudiant")
    matiere_id = request.GET.get("matiere")
    semestre = request.GET.get("semestre")

    if etudiant_id:
        notes = notes.filter(etudiant_id=etudiant_id)

    if matiere_id:
        notes = notes.filter(matiere_id=matiere_id)

    if semestre:
        notes = notes.filter(semestre=semestre)

    return render(request, "notes/list.html", {
        "notes": notes,
        "etudiants": Etudiant.objects.all(),
        "matieres": Matiere.objects.all(),
        
    })

from django.core.paginator import Paginator

def note_list(request):

    notes = Note.objects.select_related(
        "etudiant",
        "matiere"
    ).all().order_by("-id")

    etudiant_id = request.GET.get("etudiant")
    matiere_id = request.GET.get("matiere")
    semestre = request.GET.get("semestre")

    if etudiant_id:
        notes = notes.filter(etudiant_id=etudiant_id)

    if matiere_id:
        notes = notes.filter(matiere_id=matiere_id)

    if semestre:
        notes = notes.filter(semestre=semestre)

    paginator = Paginator(notes, 10)  # 10 lignes par page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "notes/list.html", {
        "notes": page_obj,
        "page_obj": page_obj,
        "etudiants": Etudiant.objects.all(),
        "matieres": Matiere.objects.all(),
    })

def note_create(request):

    form = NoteForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():
            note = form.save(commit=False)

            # DEBUG OPTIONNEL
            print("✔ Note enregistrée")

            note.save()
            return redirect("note_list")

        else:
            print(form.errors)

    return render(request, "notes/form.html", {
        "form": form,
        "title": "Ajouter note"
    })
    
def note_update(request, id):
    note = Note.objects.get(id=id)
    form = NoteForm(request.POST or None, instance=note)

    if form.is_valid():
        form.save()
        return redirect("note_list")

    return render(request, "notes/form.html", {
        "form": form,
        "title": "Modifier note"
    })


def note_delete(request, id):
    Note.objects.get(id=id).delete()
    return redirect("note_list")

def moyenne_etudiant(etudiant):
    notes = Note.objects.filter(etudiant=etudiant)

    if not notes:
        return 0

    total = sum(n.moyenne for n in notes)
    return total / notes.count()

def mention(moyenne):
    if moyenne >= 16:
        return "Très Bien"
    elif moyenne >= 14:
        return "Bien"
    elif moyenne >= 12:
        return "Assez Bien"
    elif moyenne >= 10:
        return "Passable"
    else:
        return "Insuffisant"


def classe_edit(request, pk):
    classe = Classe.objects.get(pk=pk)
    form = ClasseForm(request.POST or None, instance=classe)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect('classe_list')

    return render(request, 'classes/form.html', {
        'form': form
    })

def classe_delete(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    classe.delete()
    return redirect('classe_list')

def matiere_update(request, id):
    matiere = get_object_or_404(Matiere, id=id)
    form = MatiereForm(request.POST or None, instance=matiere)

    if form.is_valid():
        form.save()
        return redirect('matiere_list')

    return render(request, 'matieres/form.html', {'form': form})

def matiere_delete(request, id):
    matiere = get_object_or_404(Matiere, id=id)
    matiere.delete()
    return redirect('matiere_list')

from .pdf_service import generate_bulletin_pdf

from django.http import FileResponse, HttpResponse

from .models import Etudiant



def download_bulletin_pdfOOOO(request):

    # Récupérer un étudiant
    etudiant = Etudiant.objects.first()

    if not etudiant:
        return HttpResponse("Aucun étudiant trouvé.")

    # Génération du PDF
    file_path = generate_bulletin_pdf(etudiant)

    # Téléchargement du PDF
    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=f"bulletin_{etudiant.matricule}.pdf"
    )



def download_bulletin_pdfVERI(request, etudiant_id, classe_id):

    etudiant = Etudiant.objects.get(id=etudiant_id)
    classe = Classe.objects.get(id=classe_id)

    file_path = generate_bulletin_pdf(
        etudiant,
        classe
    )

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=f"bulletin_{etudiant.matricule}.pdf"
    )

def download_bulletin_pdf(request, etudiant_id, classe_id, semestre):

    etudiant = get_object_or_404(
        Etudiant,
        id=etudiant_id
    )

    classe = get_object_or_404(
        Classe,
        id=classe_id
    )

    file_path = generate_bulletin_pdf(
        etudiant=etudiant,
        classe=classe,
        semestre=semestre
    )

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=f"bulletin_S{semestre}_{etudiant.matricule}.pdf"
    )

def bulletin_classe(request, classe_id):

    classe = Classe.objects.get(id=classe_id)

    data = classement(classe)  # noqa: F821

    return render(request, "bulletin_classe.html", {
        "classe": classe,
        "data": data
    })

from .models import Etudiant

def bulletin_listQQ(request):
    etudiants = Etudiant.objects.select_related("classe").all()
    return render(request, "bulletins/list.html", {
        "etudiants": etudiants
    })



from django.core.paginator import Paginator
from .models import Etudiant, Classe

def bulletin_list(request):

    etudiants = Etudiant.objects.select_related("classe").all()

    # 🔎 Filtres GET
    matricule = request.GET.get("matricule")
    telephone = request.GET.get("telephone")
    filiere = request.GET.get("filiere")
    classe = request.GET.get("classe")

    # 🔽 Filtrage dynamique
    if matricule:
        etudiants = etudiants.filter(matricule__icontains=matricule)

    if telephone:
        etudiants = etudiants.filter(telephone__icontains=telephone)

    if filiere:
        etudiants = etudiants.filter(filiere__icontains=filiere)

    if classe:
        etudiants = etudiants.filter(classe_id=classe)

    # 📄 PAGINATION
    paginator = Paginator(etudiants, 10)  # 10 étudiants par page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "bulletins/list.html", {
        "etudiants": page_obj,
        "page_obj": page_obj,
        "classes": Classe.objects.all(),
    })
 


def liste_filieres_bts(request):
    filieres = Filierebts.objects.all().order_by('nom')

    return render(request, 'bts/liste_filieres_bts.html', {
        'filieres': filieres
    })

def ajouter_filiere_btsGGG(request):
    if request.method == "POST":
        nom = request.POST.get("nom")

        Filierebts.objects.create(
            nom=nom
        )

        messages.success(request, "Filière BTS ajoutée avec succès.")
        return redirect('liste_filieres_bts')

    return render(request, 'bts/ajouter_filiere_bts.html')


from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Filierebts, Niveau


def ajouter_filiere_bts(request):

    if request.method == "POST":

        nom = request.POST.get("nom")
        niveaux_ids = request.POST.getlist("niveaux")

        # Création de la filière
        filiere = Filierebts.objects.create(
            nom=nom
        )

        # Association des niveaux sélectionnés
        filiere.niveaux.set(niveaux_ids)

        messages.success(
            request,
            "Filière BTS ajoutée avec succès."
        )

        return redirect("liste_filieres_bts")

    niveaux = Niveau.objects.all()

    return render(
        request,
        "bts/ajouter_filiere_bts.html",
        {
            "niveaux": niveaux
        }
    )

def modifier_filiere_btsFFF(request, pk):
    filiere = get_object_or_404(Filierebts, pk=pk)

    if request.method == "POST":
        filiere.nom = request.POST.get("nom")
        filiere.save()

        messages.success(request, "Filière BTS modifiée avec succès.")
        return redirect('liste_filieres_bts')

    return render(request, 'bts/modifier_filiere_bts.html', {
        'filiere': filiere
    })
    
def modifier_filiere_bts(request, pk):

    filiere = get_object_or_404(Filierebts, pk=pk)
    niveau = filiere.niveaux.first()

    if request.method == "POST":

        filiere.nom = request.POST.get("nom")
        filiere.save()

        nom_niveau = request.POST.get("niveau")

        niveau, _ = Niveau.objects.get_or_create(
            nom=nom_niveau
        )

        filiere.niveaux.set([niveau])

        messages.success(request, "Filière modifiée avec succès.")
        return redirect("liste_filieres_bts")

    return render(
        request,
        "bts/modifier_filiere_bts.html",
        {
            "filiere": filiere,
            "niveau": niveau,
        }
    )


def supprimer_filiere_bts(request, pk):
    filiere = get_object_or_404(Filierebts, pk=pk)

    filiere.delete()

    messages.success(request, "Filière BTS supprimée.")
    return redirect('liste_filieres_bts')

def salle_list(request):
    salles = Salle.objects.all()
    return render(request, 'salles/salle_list.html', {
        'salles': salles
    })

def salle_create(request):
    if request.method == "POST":
        code = request.POST.get("code")
        nom = request.POST.get("nom")
        capacite = request.POST.get("capacite")

        Salle.objects.create(
            code=code,
            nom=nom,
            capacite=capacite
        )

        messages.success(request, "Salle ajoutée avec succès")
        return redirect('salle_list')

    return render(request, 'salles/salle_form.html')

def salle_edit(request, pk):
    salle = get_object_or_404(Salle, pk=pk)

    if request.method == "POST":
        salle.code = request.POST.get("code")
        salle.nom = request.POST.get("nom")
        salle.capacite = request.POST.get("capacite")
        salle.save()

        messages.success(request, "Salle modifiée avec succès")
        return redirect('salle_list')

    return render(request, 'salles/salle_form.html', {
        'salle': salle
    })

def salle_delete(request, pk):
    salle = get_object_or_404(Salle, pk=pk)
    salle.delete()

    messages.success(request, "Salle supprimée")
    return redirect('salle_list')


def saisie_note_groupee(request):

    classes = Classe.objects.select_related(
        "filiere_bts",
        "niveau",
        "salle"
    )

    matieres = Matiere.objects.all()

    etudiants = []
    notes_existantes = {}

    classe_id = request.GET.get("classe")
    matiere_id = request.GET.get("matiere")
    semestre = request.GET.get("semestre")


    # ==========================
    # ENREGISTREMENT DES NOTES
    # ==========================
    if request.method == "POST":

        classe_id = request.POST.get("classe")
        matiere_id = request.POST.get("matiere")
        semestre = request.POST.get("semestre")


        classe = Classe.objects.get(id=classe_id)

        etudiants = Etudiant.objects.filter(
            classe=classe
        )


        # créer ou récupérer une saisie
        saisie, created = SaisieNotesBTS.objects.get_or_create(
            classe=classe,
            matiere_id=matiere_id,
            semestre=semestre
        )


        for etudiant in etudiants:

            cc = float(
                request.POST.get(f"cc_{etudiant.id}") or 0
            )
            
            devoir = float(
               request.POST.get(f"devoir_{etudiant.id}") or 0
            )

            examen = float(
                request.POST.get(f"examen_{etudiant.id}") or 0
            )


            Note.objects.update_or_create(
                etudiant=etudiant,
                matiere_id=matiere_id,
                semestre=semestre,
                defaults={
                    "saisie": saisie,
                    "cc": cc,
                    "devoir": devoir,
                    "examen": examen,
                }
            )


        messages.success(
            request,
            "Les notes ont été enregistrées avec succès."
        )


        return redirect(
            f"{request.path}?classe={classe_id}&matiere={matiere_id}&semestre={semestre}"
        )



    # ==========================
    # AFFICHAGE
    # ==========================

    if classe_id and matiere_id and semestre:


        classe = Classe.objects.get(
            id=classe_id
        )


        etudiants = Etudiant.objects.filter(
            classe=classe
        )


        notes = Note.objects.filter(
            etudiant__in=etudiants,
            matiere_id=matiere_id,
            semestre=semestre
        )


        for note in notes:

            notes_existantes[note.etudiant_id] = note



        # envoyer la note directement dans le template
        for etudiant in etudiants:

            etudiant.note_existante = notes_existantes.get(
                etudiant.id
            )



    context = {

        "classes": classes,

        "matieres": matieres,

        "etudiants": etudiants,

        "notes_existantes": notes_existantes,

    }


    return render(
        request,
        "notes/saisie_groupee.html",
        context
    )