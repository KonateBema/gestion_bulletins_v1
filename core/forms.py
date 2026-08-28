from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GrandeUnite
from .models import (
    Etudiant,
    Classe,
    Matiere,
    Note,
    AffectationMatiere
)

# =========================
# USER REGISTER FORM
# =========================
class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


# =========================
# CLASSE FORM
# =========================
class ClasseFormHHH(forms.ModelForm):
    class Meta:
        model = Classe
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })

class ClasseForm(forms.ModelForm):

    class Meta:
        model = Classe
        fields = [
            'nom',
            'filiere_bts',  # ✅ ici
            'niveau',
            'salle'
        ]

        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'filiere_bts': forms.Select(attrs={'class': 'form-select'}),
            'niveau': forms.Select(attrs={'class': 'form-select'}),
            'salle': forms.Select(attrs={'class': 'form-select'}),
        }
# =========================
# MATIERE FORM
# =========================
class MatiereFormAA(forms.ModelForm):
    class Meta:
        model = Matiere
        fields = [
            'code',
            'libelle',
            'coefficient',
            'volume_horaire',
            'filiere_bts'
        ]

from django import forms
from .models import Matiere, GrandeUnite

class MatiereForm(forms.ModelForm):
    class Meta:
        model = Matiere
        fields = [
            "code",
            "libelle",
            "coefficient",
            "volume_horaire",
            "filiere_bts",
            "categorie",
            "grande_unite",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "libelle": forms.TextInput(attrs={"class": "form-control"}),
            "coefficient": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "volume_horaire": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "filiere_bts": forms.Select(attrs={"class": "form-select", "id": "id_filiere_bts"}),
            "categorie": forms.Select(attrs={"class": "form-select"}),
            "grande_unite": forms.Select(attrs={"class": "form-select", "id": "id_grande_unite"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Au chargement (édition), on ne montre que les grandes unités
        # de la filière déjà rattachée à la matière.
        if self.instance and self.instance.pk and self.instance.filiere_bts_id:
            self.fields["grande_unite"].queryset = GrandeUnite.objects.filter(
                filiere_bts_id=self.instance.filiere_bts_id
            ).order_by("ordre")
        elif self.data.get("filiere_bts"):
            # Si le formulaire est soumis (POST), on filtre selon la filière postée
            self.fields["grande_unite"].queryset = GrandeUnite.objects.filter(
                filiere_bts_id=self.data.get("filiere_bts")
            ).order_by("ordre")
        else:
            self.fields["grande_unite"].queryset = GrandeUnite.objects.none()

        self.fields["grande_unite"].required = False
        self.fields["grande_unite"].empty_label = "-- Aucune grande unité --"


# =========================
# ETUDIANT FORM
# =========================
class EtudiantFormOOO(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = [
            "matricule",
            "nom",
            "prenoms",
            "date_naissance",
            "lieu_naissance",
            "sexe",
            "telephone",
            "email",
            "classe",
            'filiere_bts',
        ]
from django import forms
from .models import Etudiant

class EtudiantForm(forms.ModelForm):

    class Meta:
        model = Etudiant

        fields = [
            'matricule',
            'nom',
            'prenoms',
            'date_naissance',
            "lieu_naissance",
            'sexe',
            'telephone',
            'email',
            'classe',
            'filiere_bts',
        ]

        widgets = {

            'matricule': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'nom': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'prenoms': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'date_naissance': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'sexe': forms.Select(attrs={
                'class': 'form-select'
            }),

            'telephone': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),

            'classe': forms.Select(attrs={
                'class': 'form-select'
            }),

            'filiere_bts': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

# =========================
# AFFECTATION FORM
# =========================
class AffectationForm(forms.ModelForm):
    class Meta:
        model = AffectationMatiere
        fields = "__all__"


# =========================
# NOTE FORM
# =========================
from django import forms
from .models import Note

from django import forms
from .models import Note


class NoteForm(forms.ModelForm):

    class Meta:
        model = Note

        fields = [
            "etudiant",
            "matiere",
            "devoir",
            "examen",
            "cc",
            "semestre",
        ]

        widgets = {

            "etudiant": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "matiere": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "devoir": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Note devoir"
                }
            ),

            "examen": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Note examen"
                }
            ),

            "cc": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Note CC"
                }
            ),

            "semestre": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),
        }
        
class GrandeUniteForm(forms.ModelForm):
    class Meta:
        model = GrandeUnite
        fields = ["code", "libelle", "ordre", "filiere_bts", "description"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: GU01"}),
            "libelle": forms.TextInput(attrs={"class": "form-control"}),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "filiere_bts": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }