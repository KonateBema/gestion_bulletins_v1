from django import forms
from .models import EtudiantLMD, UE, ECUE


class EtudiantLMDForm(forms.ModelForm):

    ues = forms.ModelMultipleChoiceField(
        queryset=UE.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    ecues = forms.ModelMultipleChoiceField(
        queryset=ECUE.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
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
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "matricule": forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "nom": forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "prenoms": forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "telephone": forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class":"form-control"
                }
            ),

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


    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

        for field in self.fields.values():

            field.widget.attrs.update({
                "class":"form-control"
            })

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

            "code":forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "libelle":forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "coefficient":forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "credit":forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

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

            "matricule": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "nom": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "prenoms": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "sexe": forms.Select(
                attrs={"class":"form-select"}
            ),

            "telephone": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "email": forms.EmailInput(
                attrs={"class":"form-control"}
            ),
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
                    "class": "form-control"
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
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

        }


    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

        for field in self.fields:

            self.fields[field].widget.attrs.update(
                {
                    "class":"form-control"
                }
            )




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

            "date_naissance": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "matricule": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "nom": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "prenoms": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "email": forms.EmailInput(
                attrs={"class":"form-control"}
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

            "code": forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "libelle": forms.TextInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "coefficient": forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

            "credit": forms.NumberInput(
                attrs={
                    "class":"form-control"
                }
            ),

        }