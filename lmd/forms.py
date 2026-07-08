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