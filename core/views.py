# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_protect
from .forms import EtudiantForm,ClasseForm,MatiereForm,AffectationForm,NoteForm
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .services import calcul_moyenne_etudiant
from openpyxl import load_workbook
from .models import Filierebts
from django.contrib import messages
from .models import Salle
from .models import SaisieNotesBTS
from .models import ( Classe,Niveau)
from lmd.models import EtudiantLMD,FiliereLMD
# from .models import NoteBTS
from .models import (Etudiant, Professeur, Matiere, Note,AffectationMatiere, Inscription, Profile)
from .forms import UserRegisterForm
from .utils import generate_matricule
from .services import (mention,)
from .pdf_service import generate_bulletin_pdf
from datetime import datetime
from core.decorators import role_required

# =========================
# 🔐 LOGIN
# =========================
@csrf_protect
def login_viewAAAA(request):

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

from django.views.decorators.csrf import csrf_protect


# ==========================================================
# 🔐 LOGIN
# ==========================================================

@csrf_protect
def login_view(request):

    # ==========================================================
    # UTILISATEUR DÉJÀ CONNECTÉ
    # ==========================================================

    if request.user.is_authenticated:

        profile = Profile.objects.filter(
            user=request.user
        ).first()

        if not profile:

            logout(request)

            return render(
                request,
                "login.html",
                {
                    "error": "Profil utilisateur introuvable."
                }
            )

        # Redirection selon le rôle
        if profile.role == "ADMIN":

            return redirect("dashboard_admin")

        elif profile.role == "GESTIONNAIRE":

            return redirect("dashboard_gestionnaire")

        elif profile.role == "PROF":

            return redirect("dashboard_prof")

        elif profile.role == "ETUDIANT":

            return redirect("dashboard_etudiant")

        else:

            logout(request)

            return render(
                request,
                "login.html",
                {
                    "error": "Rôle utilisateur non reconnu."
                }
            )

    # ==========================================================
    # FORMULAIRE DE CONNEXION
    # ==========================================================

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        # Vérification des champs
        if not username or not password:

            return render(
                request,
                "login.html",
                {
                    "error":
                    "Veuillez renseigner votre identifiant "
                    "et votre mot de passe."
                }
            )

        # ======================================================
        # AUTHENTIFICATION DJANGO
        # ======================================================

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:

            return render(
                request,
                "login.html",
                {
                    "error":
                    "Identifiant ou mot de passe incorrect."
                }
            )

        # ======================================================
        # CONNEXION
        # ======================================================

        login(
            request,
            user
        )

        # ======================================================
        # RÉCUPÉRATION DU PROFIL
        # ======================================================

        profile = Profile.objects.filter(
            user=user
        ).first()

        # Aucun profil
        if not profile:

            logout(request)

            return render(
                request,
                "login.html",
                {
                    "error":
                    "Profil utilisateur introuvable."
                }
            )

        # ======================================================
        # REDIRECTION SELON LE RÔLE
        # ======================================================

        if profile.role == "ADMIN":

            return redirect(
                "dashboard_admin"
            )

        elif profile.role == "GESTIONNAIRE":

            return redirect(
                "dashboard_gestionnaire"
            )

        elif profile.role == "PROF":

            return redirect(
                "dashboard_prof"
            )

        elif profile.role == "ETUDIANT":

            return redirect(
                "dashboard_etudiant"
            )

        # ======================================================
        # RÔLE INCONNU
        # ======================================================

        logout(request)

        return render(
            request,
            "login.html",
            {
                "error":
                "Rôle utilisateur non reconnu."
            }
        )

    # ==========================================================
    # AFFICHAGE PAGE LOGIN
    # ==========================================================

    return render(
        request,
        "login.html"
    )


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


# ==========================================================
# 👨‍💼 DASHBOARD GESTIONNAIRE
# ==========================================================

@login_required(login_url="login")
@role_required("GESTIONNAIRE")
def dashboard_gestionnaire(request):

    return render(
        request,
        "gestionnaire_dashboard.html",
        {
            "etudiants": Etudiant.objects.count(),
            "classes": Classe.objects.count(),
            "filieres": Filierebts.objects.count(),
            "matieres": Matiere.objects.count(),
        }
    )



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
@role_required("ADMIN")
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
@role_required("ADMIN", "GESTIONNAIRE")
@login_required(login_url="login")
def etudiant_listPRO(request):

    query = request.GET.get("q", "")
    classe_id = request.GET.get("classe", "")
    filiere_bts_id = request.GET.get("filiere_bts", "")
    niveau = request.GET.get("niveau", "")


    # =========================
    # LISTE ETUDIANTS
    # =========================

    etudiants = Etudiant.objects.select_related(
        "classe",
        "filiere_bts"
    ).order_by("nom", "prenoms")



    # =========================
    # RECHERCHE
    # =========================

    if query:

        etudiants = etudiants.filter(

            Q(matricule__icontains=query) |

            Q(nom__icontains=query) |

            Q(prenoms__icontains=query)

        )



    # =========================
    # FILTRE CLASSE
    # =========================

    if classe_id:

        etudiants = etudiants.filter(
            classe_id=classe_id
        )



    # =========================
    # FILTRE NIVEAU BTS
    # =========================

    if niveau:

        etudiants = etudiants.filter(

            filiere_bts__niveaux__nom=niveau

        ).distinct()



    # =========================
    # FILTRE FILIERE BTS
    # =========================

    if filiere_bts_id:

        etudiants = etudiants.filter(

            filiere_bts_id=filiere_bts_id

        )



    # =========================
    # PAGINATION
    # =========================

    paginator = Paginator(
        etudiants,
        10
    )


    page_number = request.GET.get("page")


    page_obj = paginator.get_page(
        page_number
    )



    return render(
        request,
        "etudiants/list.html",
        {

            "page_obj": page_obj,


            # données filtres

            "classes": Classe.objects.all().order_by("nom"),


            "filieres_bts": Filierebts.objects.all().order_by("nom"),


            "niveau": niveau,


            "classe_selected": classe_id,


            "filiere_selected": filiere_bts_id,


            "query": query,

        }
    )

def etudiant_list(request):

    etudiants = Etudiant.objects.select_related(
        "filiere_bts",
        "classe"
    ).all()

    q = request.GET.get("q", "").strip()
    niveau = request.GET.get("niveau", "").strip()
    filiere_bts = request.GET.get("filiere_bts", "").strip()

    # Recherche
    if q:
        etudiants = etudiants.filter(
            Q(nom__icontains=q) |
            Q(prenoms__icontains=q) |
            Q(matricule__icontains=q)
        )

    # Filtre BTS 1 / BTS 2
    if niveau:
        etudiants = etudiants.filter(
            classe__niveau__nom=niveau
        )

    # Filtre filière
    if filiere_bts:
        etudiants = etudiants.filter(
            filiere_bts_id=filiere_bts
        )

    filieres_bts = Filierebts.objects.all().order_by("nom")

    paginator = Paginator(etudiants, 20)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "filieres_bts": filieres_bts,
    }

    return render(
        request,
        "etudiants/list.html",
        context
    )


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

@login_required(login_url="login")
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
import unicodedata
    

import re



# ==============================================================
# NORMALISATION GÉNÉRALE
# ==============================================================

def normaliser_texte(texte):
    """
    Normalise un texte pour les comparaisons :

    - minuscules
    - suppression des accents
    - apostrophes uniformisées
    - espaces multiples supprimés
    """

    if texte is None:
        return ""

    texte = str(texte).strip().lower()

    # Uniformiser les apostrophes
    texte = texte.replace("’", "'")
    texte = texte.replace("`", "'")
    texte = texte.replace("´", "'")

    # Supprimer les accents
    texte = unicodedata.normalize(
        "NFD",
        texte
    )

    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    # Remplacer les espaces multiples par un seul espace
    texte = " ".join(texte.split())

    return texte


# ==============================================================
# NORMALISATION FILIÈRE
# ==============================================================

def normaliser_filiere(texte):
    """
    Normalise une filière pour permettre les comparaisons
    même si le fichier Excel ne contient pas le code (IDA), (AD), etc.
    """

    texte = normaliser_texte(texte)

    # Supprimer les codes entre parenthèses
    # Exemple :
    # INFORMATIQUE ET DEVELOPPEMENT D'APPLICATIONS (IDA)
    # devient :
    # INFORMATIQUE ET DEVELOPPEMENT D'APPLICATIONS
    texte = re.sub(
        r"\s*\([^)]*\)",
        "",
        texte
    )

    # Uniformiser les apostrophes restantes
    texte = texte.replace("'", "")

    # Supprimer les espaces multiples
    texte = " ".join(texte.split())

    return texte


# ==============================================================
# IMPORT DES ÉTUDIANTS EXCEL
# ==============================================================


def import_etudiants_excel(request):

    if request.method != "POST":
        return render(
            request,
            "import_etudiants_excel.html"
        )

    fichier = request.FILES.get("excel_file")

    # ==========================================================
    # 1. Vérification du fichier
    # ==========================================================

    if not fichier:
        messages.error(
            request,
            "Veuillez sélectionner un fichier Excel."
        )
        return redirect("import_etudiants_excel")

    if not fichier.name.lower().endswith(".xlsx"):
        messages.error(
            request,
            "Format incorrect. Veuillez importer uniquement un fichier .xlsx."
        )
        return redirect("import_etudiants_excel")

    # ==========================================================
    # 2. Lecture Excel
    # ==========================================================

    try:
        wb = load_workbook(
            fichier,
            data_only=True
        )

    except Exception as e:
        messages.error(
            request,
            f"Impossible de lire le fichier Excel : {e}"
        )
        return redirect("import_etudiants_excel")

    # ==========================================================
    # 3. Vérification de la feuille
    # ==========================================================

    if not wb.sheetnames:
        messages.error(
            request,
            "Le fichier Excel ne contient aucune feuille."
        )
        return redirect("import_etudiants_excel")

    ws = wb.active

    if ws.max_row < 2:
        messages.error(
            request,
            "Le fichier Excel ne contient aucune donnée étudiant."
        )
        return redirect("import_etudiants_excel")

    # ==========================================================
    # 4. Vérification des colonnes
    # ==========================================================

    entetes_attendues = [
        "Matricule",
        "Nom",
        "Prénoms",
        "Date naissance",
        "Lieu naissance",
        "Sexe",
        "Téléphone",
        "Email",
        "Classe",
        "Filière",
    ]

    entetes_excel = [
        str(cell.value).strip()
        if cell.value is not None
        else ""
        for cell in ws[1]
    ]

    entetes_excel = entetes_excel[:10]

    entetes_attendues_normalisees = [
        normaliser_texte(entete)
        for entete in entetes_attendues
    ]

    entetes_excel_normalisees = [
        normaliser_texte(entete)
        for entete in entetes_excel
    ]

    if entetes_excel_normalisees != entetes_attendues_normalisees:

        messages.error(
            request,
            "Le format du fichier Excel est incorrect."
        )

        messages.warning(
            request,
            "Colonnes attendues : "
            + " | ".join(entetes_attendues)
        )

        messages.warning(
            request,
            "Colonnes trouvées : "
            + " | ".join(entetes_excel)
        )

        return redirect("import_etudiants_excel")

    # ==========================================================
    # 5. Préparation
    # ==========================================================

    compteur_creation = 0
    compteur_modification = 0
    erreurs = []

    matricules_fichier = set()
    emails_fichier = set()

    # ==========================================================
    # 6. Parcours des étudiants
    # ==========================================================

    for ligne, row in enumerate(
        ws.iter_rows(
            min_row=2,
            values_only=True
        ),
        start=2
    ):

        try:

            # --------------------------------------------------
            # Ligne vide
            # --------------------------------------------------

            if not row or all(
                value is None
                or str(value).strip() == ""
                for value in row
            ):
                continue

            # --------------------------------------------------
            # Nombre de colonnes
            # --------------------------------------------------

            if len(row) < 10:

                erreurs.append(
                    f"Ligne {ligne}: "
                    f"nombre de colonnes insuffisant."
                )

                continue

            # ==================================================
            # 7. Lecture des données
            # ==================================================

            matricule = (
                str(row[0]).strip()
                if row[0] is not None
                else ""
            )

            nom = (
                str(row[1]).strip()
                if row[1] is not None
                else ""
            )

            prenoms = (
                str(row[2]).strip()
                if row[2] is not None
                else ""
            )

            date_naissance = row[3]

            lieu_naissance = (
                str(row[4]).strip()
                if row[4] is not None
                else ""
            )

            sexe = (
                str(row[5]).strip().upper()
                if row[5] is not None
                else ""
            )

            telephone = (
                str(row[6]).strip()
                if row[6] is not None
                else ""
            )

            email = (
                str(row[7]).strip().lower()
                if row[7] is not None
                else ""
            )

            classe_nom = (
                str(row[8]).strip()
                if row[8] is not None
                else ""
            )

            filiere_nom = (
                str(row[9]).strip()
                if row[9] is not None
                else ""
            )

            # ==================================================
            # 8. Champs obligatoires
            # ==================================================

            champs_obligatoires = {
                "Matricule": matricule,
                "Nom": nom,
                "Prénoms": prenoms,
                "Lieu naissance": lieu_naissance,
                "Sexe": sexe,
                "Classe": classe_nom,
                "Filière": filiere_nom,
            }

            champs_vides = [
                champ
                for champ, valeur
                in champs_obligatoires.items()
                if not valeur
            ]

            if champs_vides:

                erreurs.append(
                    f"Ligne {ligne}: "
                    f"champs obligatoires manquants : "
                    f"{', '.join(champs_vides)}."
                )

                continue

            # ==================================================
            # 9. Doublon matricule dans le fichier Excel
            # ==================================================

            matricule_normalise = normaliser_texte(
                matricule
            )

            if matricule_normalise in matricules_fichier:

                erreurs.append(
                    f"Ligne {ligne}: "
                    f"matricule '{matricule}' "
                    f"en doublon dans le fichier Excel."
                )

                continue

            matricules_fichier.add(
                matricule_normalise
            )

            # ==================================================
            # 10. Vérification du sexe
            # ==================================================

            if sexe not in ["M", "F"]:

                erreurs.append(
                    f"Ligne {ligne}: "
                    f"sexe '{sexe}' incorrect. "
                    f"Valeurs autorisées : M ou F."
                )

                continue

            # ==================================================
            # 11. Vérification date de naissance
            # ==================================================

            if not isinstance(
                date_naissance,
                datetime
            ):

                erreurs.append(
                    f"Ligne {ligne}: "
                    f"date de naissance invalide. "
                    f"Utilisez une vraie date Excel."
                )

                continue

            date_naissance = date_naissance.date()

            # ==================================================
            # 12. Recherche de la classe
            # ==================================================

            classe = None

            classe_normalisee = normaliser_texte(
                classe_nom
            )

            for c in Classe.objects.select_related(
                "filiere_bts"
            ):

                if normaliser_texte(
                    c.nom
                ) == classe_normalisee:

                    classe = c
                    break

            if classe is None:

                erreurs.append(
                    f"Ligne {ligne}: "
                    f"classe '{classe_nom}' introuvable."
                )

                continue

            # ==================================================
            # 13. Recherche de la filière
            # ==================================================

            filiere = None

            filiere_normalisee = normaliser_filiere(
                filiere_nom
            )

            for f in Filierebts.objects.all():

                if normaliser_filiere(
                    f.nom
                ) == filiere_normalisee:

                    filiere = f
                    break

            if filiere is None:

                erreurs.append(
                    f"Ligne {ligne}: "
                    f"filière '{filiere_nom}' introuvable."
                )

                continue

            # ==================================================
            # 14. Vérification classe / filière
            # ==================================================

            if classe.filiere_bts_id != filiere.id:

                erreurs.append(
                    f"Ligne {ligne}: "
                    f"la classe '{classe.nom}' "
                    f"n'appartient pas à la filière "
                    f"'{filiere.nom}'."
                )

                continue

            # ==================================================
            # 15. Vérification email dans le fichier
            # ==================================================

            if email:

                email_normalise = normaliser_texte(
                    email
                )

                if email_normalise in emails_fichier:

                    erreurs.append(
                        f"Ligne {ligne}: "
                        f"email '{email}' "
                        f"en doublon dans le fichier Excel."
                    )

                    continue

                emails_fichier.add(
                    email_normalise
                )

            # ==================================================
            # 16. Recherche de l'étudiant existant
            # ==================================================

            etudiant_existant = None

            for etudiant in Etudiant.objects.all():

                if normaliser_texte(
                    etudiant.matricule
                ) == matricule_normalise:

                    etudiant_existant = etudiant
                    break

            # ==================================================
            # 17. Vérification email en base
            # ==================================================

            if email:

                email_existant = False

                for etudiant in Etudiant.objects.exclude(
                    email__isnull=True
                ):

                    if (
                        etudiant_existant
                        and etudiant.id == etudiant_existant.id
                    ):
                        continue

                    if not etudiant.email:
                        continue

                    if normaliser_texte(
                        etudiant.email
                    ) == email_normalise:

                        email_existant = True
                        break

                if email_existant:

                    erreurs.append(
                        f"Ligne {ligne}: "
                        f"email '{email}' "
                        f"déjà utilisé par un autre étudiant."
                    )

                    continue

            # ==================================================
            # 18. Mise à jour de l'étudiant existant
            # ==================================================

            if etudiant_existant:

                etudiant_existant.nom = nom
                etudiant_existant.prenoms = prenoms
                etudiant_existant.date_naissance = date_naissance
                etudiant_existant.lieu_naissance = lieu_naissance
                etudiant_existant.sexe = sexe
                etudiant_existant.telephone = telephone
                etudiant_existant.email = email
                etudiant_existant.classe = classe
                etudiant_existant.filiere_bts = filiere

                etudiant_existant.save()

                compteur_modification += 1

                continue

            # ==================================================
            # 19. Création du nouvel étudiant
            # ==================================================

            Etudiant.objects.create(
                matricule=matricule,
                nom=nom,
                prenoms=prenoms,
                date_naissance=date_naissance,
                lieu_naissance=lieu_naissance,
                sexe=sexe,
                telephone=telephone,
                email=email,
                classe=classe,
                filiere_bts=filiere,
            )

            compteur_creation += 1

        except Exception as e:

            erreurs.append(
                f"Ligne {ligne}: "
                f"erreur inattendue : {str(e)}"
            )

    # ==========================================================
    # 20. Messages de résultat
    # ==========================================================

    if compteur_creation > 0:

        messages.success(
            request,
            f"{compteur_creation} étudiant(s) créé(s) avec succès."
        )

    if compteur_modification > 0:

        messages.success(
            request,
            f"{compteur_modification} étudiant(s) "
            f"mis à jour avec succès."
        )

    if erreurs:

        messages.warning(
            request,
            f"{len(erreurs)} ligne(s) n'ont pas été importée(s)."
        )

        for erreur in erreurs:

            messages.warning(
                request,
                erreur
            )

    if (
        compteur_creation == 0
        and compteur_modification == 0
        and not erreurs
    ):

        messages.warning(
            request,
            "Aucun étudiant n'a été trouvé dans le fichier."
        )

    return redirect(
        "etudiant_list"
    )



def import_etudiants_excelAAAAA(request):

    if request.method == "POST":

        fichier = request.FILES.get("excel_file")

        if not fichier:
            messages.error(
                request,
                "Veuillez sélectionner un fichier Excel."
            )
            return redirect("import_etudiants_excel")


        # Vérification extension
        if not fichier.name.endswith(".xlsx"):

            messages.error(
                request,
                "Veuillez importer un fichier Excel .xlsx"
            )

            return redirect("import_etudiants_excel")



        try:

            wb = load_workbook(
                fichier,
                data_only=True
            )


            # Vérifier les feuilles

            if len(wb.sheetnames) == 0:

                messages.error(
                    request,
                    "Le fichier Excel ne contient aucune feuille."
                )

                return redirect("import_etudiants_excel")


            ws = wb.active



        except Exception as e:

            messages.error(
                request,
                f"Erreur lecture Excel : {e}"
            )

            return redirect("import_etudiants_excel")



        compteur = 0
        erreurs = []



        # Vérifier les lignes

        if ws.max_row < 2:

            messages.error(
                request,
                "Le fichier Excel ne contient aucune donnée étudiant."
            )

            return redirect("import_etudiants_excel")




        for ligne, row in enumerate(
            ws.iter_rows(
                min_row=2,
                values_only=True
            ),
            start=2
        ):


            try:


                if not row or row[0] is None:
                    continue



                matricule = str(row[0]).strip()

                nom = str(row[1]).strip()

                prenoms = str(row[2]).strip()

                date_naissance = row[3]

                lieu_naissance = str(row[4]).strip()

                sexe = str(row[5]).upper().strip()


                telephone = str(row[6]).strip()

                email = str(row[7]).strip()


                classe_nom = str(row[8]).strip()

                filiere_nom = str(row[9]).strip()



                # Recherche classe

                classe = Classe.objects.filter(
                    nom__iexact=classe_nom
                ).first()



                # Recherche filière

                filiere = Filierebts.objects.filter(
                    nom__iexact=filiere_nom
                ).first()



                if classe is None:

                    erreurs.append(
                        f"Ligne {ligne}: classe '{classe_nom}' introuvable"
                    )

                    continue



                if filiere is None:

                    erreurs.append(
                        f"Ligne {ligne}: filière '{filiere_nom}' introuvable"
                    )

                    continue




                Etudiant.objects.update_or_create(

                    matricule=matricule,

                    defaults={

                        "nom": nom,

                        "prenoms": prenoms,

                        "date_naissance": date_naissance,

                        "lieu_naissance": lieu_naissance,

                        "sexe": sexe,

                        "telephone": telephone,

                        "email": email,

                        "classe": classe,

                        "filiere_bts": filiere,

                    }

                )


                compteur += 1



            except Exception as e:

                erreurs.append(
                    f"Ligne {ligne}: {str(e)}"
                )




        if compteur > 0:

            messages.success(
                request,
                f"{compteur} étudiant(s) importé(s) avec succès."
            )



        for erreur in erreurs:

            messages.warning(
                request,
                erreur
            )



        return redirect(
            "etudiant_list"
        )



    return render(
        request,
        "import_etudiants_excel.html"
    )