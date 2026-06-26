from django import forms
from .models import EtudiantLMD


class EtudiantLMDForm(forms.ModelForm):
    class Meta:
        model = EtudiantLMD
        fields = [
            'matricule',
            'nom',
            'prenoms',
            'sexe',
            'date_naissance',
            'lieu_naissance',
            'telephone',
            'email',
            'statut',
            'niveau',
            'filiere',
            'annee_academique',
        ]