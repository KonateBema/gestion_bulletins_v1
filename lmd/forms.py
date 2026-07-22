from django import forms
from .models import EtudiantLMD, UE, ECUE, MasterUE, MasterECUE
from .models import EtudiantMaster
from .models import MasterProgramme


class EtudiantLMDForm(forms.ModelForm):
    ues = forms.ModelMultipleChoiceField(
        queryset=UE.objects.all(), required=False, widget=forms.CheckboxSelectMultiple
    )

    ecues = forms.ModelMultipleChoiceField(
        queryset=ECUE.objects.all(), required=False, widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = EtudiantLMD
        fields = [
            "matricule",
            "nom",
            "prenoms",
            "sexe",
            "date_naissance",
            "lieu_naissance",
            "telephone",
            "email",
            "niveau",
            "filiere",
            "statut",
            "annee_academique",
            "ues",
            "ecues",
        ]


class EtudiantDroitForm(forms.ModelForm):
    class Meta:
        model = EtudiantLMD

        fields = [
            "matricule",
            "nom",
            "prenoms",
            "sexe",
            "date_naissance",
            "lieu_naissance",
            "telephone",
            "email",
            "annee_academique",
        ]

        widgets = {
            "date_naissance": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "matricule": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenoms": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class UEDroitForm(forms.ModelForm):
    class Meta:
        model = UE

        fields = [
            "code",
            "libelle",
            "credit",
            "semestre",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


from django import forms
from .models import ECUE


class ECUEForm(forms.ModelForm):
    class Meta:
        model = ECUE

        fields = [
            "code",
            "libelle",
            "coefficient",
            "credit",
            
        ]

        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "libelle": forms.TextInput(attrs={"class": "form-control"}),
            "coefficient": forms.NumberInput(attrs={"class": "form-control"}),
            "credit": forms.NumberInput(attrs={"class": "form-control"}),
        }


from .models import EtudiantLMD


class EtudiantGestionForm(forms.ModelForm):
    class Meta:
        model = EtudiantLMD

        fields = [
            "matricule",
            "nom",
            "prenoms",
            "sexe",
            "telephone",
            "email",
        ]

        widgets = {
            "matricule": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenoms": forms.TextInput(attrs={"class": "form-control"}),
            "sexe": forms.Select(attrs={"class": "form-select"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


from django import forms
from .models import UE


class UEForm(forms.ModelForm):

    class Meta:
        model = UE

        fields = [
            "code",
            "libelle",
            "credit",
            "semestre",
        ]

        widgets = {

            "code": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "libelle": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "credit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1
                }
            ),

            "semestre": forms.Select(
                choices=[
                    ("S1", "Semestre 1"),
                    ("S2", "Semestre 2"),
                ],
                attrs={
                    "class": "form-select"
                }
            ),
        }


from django import forms
from .models import EtudiantLMD


class TroncCommunEtudiantForm(forms.ModelForm):
    class Meta:
        model = EtudiantLMD

        fields = [
            "matricule",
            "nom",
            "prenoms",
            "sexe",
            "date_naissance",
            "filiere",
            "niveau",
            "statut",
            "annee_academique",
        ]

        widgets = {
            "date_naissance": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})


class QHSEEtudiantFormerrrr(forms.ModelForm):
    class Meta:
        model = EtudiantLMD

        fields = [
            "matricule",
            "nom",
            "prenoms",
            "sexe",
            "date_naissance",
            "lieu_naissance",
            "telephone",
            "email",
            "statut",
        ]

        widgets = {
            "date_naissance": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "matricule": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenoms": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

class QHSEEtudiantForm(forms.ModelForm):

    class Meta:

        model = EtudiantLMD


        fields = [
            "matricule",
            "nom",
            "prenoms",
            "sexe",
            "date_naissance",
            "lieu_naissance",
            "telephone",
            "email",
            "statut",
        ]


        widgets = {


            "matricule": forms.TextInput(
                attrs={
                    "class":"form-control",
                    "placeholder":"Matricule"
                }
            ),



            "nom": forms.TextInput(
                attrs={
                    "class":"form-control",
                    "placeholder":"Nom"
                }
            ),



            "prenoms": forms.TextInput(
                attrs={
                    "class":"form-control",
                    "placeholder":"Prénoms"
                }
            ),



            "sexe": forms.Select(
                attrs={
                    "class":"form-select"
                }
            ),



            "date_naissance": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),



            "lieu_naissance": forms.TextInput(
                attrs={
                    "class":"form-control",
                    "placeholder":"Lieu de naissance"
                }
            ),



            "telephone": forms.TextInput(
                attrs={
                    "class":"form-control",
                    "placeholder":"Téléphone"
                }
            ),



            "email": forms.EmailInput(
                attrs={
                    "class":"form-control",
                    "placeholder":"Email"
                }
            ),



            "statut": forms.Select(
                attrs={
                    "class":"form-select"
                }
            ),

        }
from .models import ECUE


class QHSEECUEForm(forms.ModelForm):
    class Meta:
        model = ECUE

        fields = [
            "code",
            "libelle",
            "coefficient",
            "credit",
        ]

        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "libelle": forms.TextInput(attrs={"class": "form-control"}),
            "coefficient": forms.NumberInput(attrs={"class": "form-control"}),
            "credit": forms.NumberInput(attrs={"class": "form-control"}),
        }


class MasterEtudiantForm(forms.ModelForm):
    class Meta:
        model = EtudiantMaster

        fields = ["matricule", "nom", "prenoms", "sexe", "programme", "niveau"]

        widgets = {
            "matricule": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenoms": forms.TextInput(attrs={"class": "form-control"}),
            "sexe": forms.Select(attrs={"class": "form-select"}),
            "programme": forms.Select(attrs={"class": "form-select"}),
            "niveau": forms.Select(attrs={"class": "form-select"}),
        }


class MasterProgrammeForm(forms.ModelForm):
    class Meta:
        model = MasterProgramme

        fields = ["niveau", "specialite", "filiere", "annee_academique"]

        widgets = {
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "specialite": forms.Select(attrs={"class": "form-select"}),
            "filiere": forms.Select(attrs={"class": "form-select"}),
            "annee_academique": forms.TextInput(attrs={"class": "form-control"}),
        }


class MasterUEForm(forms.ModelForm):
    class Meta:
        model = MasterUE

        fields = [
            "code",
            "libelle",
            "credit",
            "semestre",
        ]

        widgets = {
            "code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: UE-MQ01"}
            ),
            "libelle": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nom de l'UE"}
            ),
            "credit": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "semestre": forms.Select(attrs={"class": "form-select"}),
        }


class MasterECUEForm(forms.ModelForm):
    class Meta:
        model = MasterECUE

        fields = ["code", "libelle", "coefficient", "credit"]

        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "libelle": forms.TextInput(attrs={"class": "form-control"}),
            "coefficient": forms.NumberInput(attrs={"class": "form-control"}),
            "credit": forms.NumberInput(attrs={"class": "form-control"}),
        }


class MasterProgrammeForm(forms.ModelForm):
    class Meta:
        model = MasterProgramme

        fields = ["niveau", "specialite", "filiere", "annee_academique"]

        widgets = {
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "specialite": forms.Select(attrs={"class": "form-select"}),
            "filiere": forms.Select(attrs={"class": "form-select"}),
            "annee_academique": forms.TextInput(attrs={"class": "form-control"}),
        }
