from django.db import models
from django.contrib.auth.models import User

from core.models import Classe, Filiere, Niveau, Etudiant


# =====================
# UE (Unité d’Enseignement)
# =====================

class UE(models.Model):
    code = models.CharField(max_length=20)
    libelle = models.CharField(max_length=200)
    credit = models.IntegerField()

    filiere = models.ForeignKey(
    "FiliereLMD",
    null=True,
    blank=True,
    on_delete=models.CASCADE
    )

    grande_unite = models.ForeignKey(
    "GrandeUnite",
    on_delete=models.PROTECT,
    related_name="ues",
    null=True,
    blank=True
    )
  
    semestre = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.code} - {self.libelle}"


# =====================
# ECUE (Élément Constitutif d’UE)
# =====================
class ECUE(models.Model):
    ue = models.ForeignKey(
        UE,
        on_delete=models.CASCADE,
        related_name='ecues'
    )

    code = models.CharField(max_length=20)
    libelle = models.CharField(max_length=200)
    coefficient = models.IntegerField(default=1)
    credit = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.code} - {self.libelle}"


# =====================
class NoteLMD(models.Model):

    SESSION_CHOICES = (
        ("1", "Session 1"),
        ("2", "Session 2 (Rattrapage)"),
    )

    SEMESTRE_CHOICES = (
        ("S1", "Semestre 1"),
        ("S2", "Semestre 2"),
        ("S3", "Semestre 3"),
        ("S4", "Semestre 4"),
        ("S5", "Semestre 5"),
        ("S6", "Semestre 6"),
    )

    etudiant = models.ForeignKey(
        "EtudiantLMD",
        on_delete=models.CASCADE,
        related_name="notes_lmd"
    )

    ecue = models.ForeignKey(
        "ECUE",
        on_delete=models.CASCADE,
        related_name="notes"
    )

    semestre = models.CharField(
        max_length=2,
        choices=SEMESTRE_CHOICES
    )

    session = models.CharField(
        max_length=1,
        choices=SESSION_CHOICES,
        default="1"
    )

    cc = models.FloatField(default=0)
    examen = models.FloatField(default=0)

    moyenne = models.FloatField(blank=True, null=True, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "etudiant",
                    "ecue",
                    "semestre",
                    "session",
                ],
                name="unique_note_par_session",
            )
        ]

    def save(self, *args, **kwargs):
        cc = float(self.cc or 0)
        examen = float(self.examen or 0)
        self.moyenne = round(
            self.cc * 0.4 + self.examen * 0.6,
            2
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.etudiant} - {self.ecue} - {self.semestre} Session {self.session}"

# =====================
# ÉTUDIANT LMD (structure académique)
# =====================
class EtudiantLMD(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    matricule = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=150)
    ues = models.ManyToManyField("UE", blank=True)
    ecues = models.ManyToManyField("ECUE", blank=True)

    sexe = models.CharField(
        max_length=1,
        choices=(
            ('M', 'Masculin'),
            ('F', 'Féminin'),
        )
    )

    STATUTS = [
        ("AF", "Affecté"),
        ("NF", "Non Affecté"),
    ]
    statut = models.CharField(
         max_length=2,
         choices=STATUTS,
         default="NF"
    )
    
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    # 🎓 Structure LMD
    NIVEAUX = [
        ("L1", "Licence 1"),
        ("L2", "Licence 2"),
        ("L3", "Licence 3"),
        ("M1", "Master 1"),
        ("M2", "Master 2"),
        ("DOC", "Doctorat"),
    ]

    niveau = models.CharField(
        max_length=10,
        choices=NIVEAUX
    )

    # filiere = models.ForeignKey(
    #     FiliereLMD,
    #     on_delete=models.CASCADE,
    #     related_name="etudiants_lmd"
    # )
    filiere = models.ForeignKey(
    "FiliereLMD",
    on_delete=models.CASCADE
    )

    annee_academique = models.CharField(max_length=20)

    date_inscription = models.DateTimeField(auto_now_add=True)

    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenoms}"

from django.db import models


class NiveauLMD(models.Model):
    code = models.CharField(
        max_length=10,
        unique=True
    )

    libelle = models.CharField(
        max_length=100
    )

    ordre = models.PositiveIntegerField(
        default=1
    )

    class Meta:
        ordering = ["ordre"]

    def __str__(self):
        return self.libelle

from django.db import models


class ClasseLMD(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True
    )

    libelle = models.CharField(
        max_length=100
    )

    niveau = models.ForeignKey(
        "NiveauLMD",
        on_delete=models.PROTECT,
        related_name="ClasseLMD"
    )

    filiere = models.ForeignKey(
        "FiliereLMD",
        on_delete=models.PROTECT,
        related_name="ClasseLMD"
    )

    class Meta:
        ordering = ["libelle"]

    def __str__(self):
        return self.libelle

class FiliereLMD(models.Model):
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=100)

    def __str__(self):
        return self.libelle



class GrandeUnite(models.Model):
    nom = models.CharField(max_length=150)
    filiere = models.ForeignKey("FiliereLMD", on_delete=models.CASCADE)
    semestre = models.CharField(max_length=2)

    def __str__(self):
        filiere = getattr(self.filiere, "libelle", "Sans filière")
        return f"{self.nom} - {filiere} ({self.semestre})"

class SaisieNoteLMD(models.Model):

    filiere = models.ForeignKey("FiliereLMD", on_delete=models.CASCADE)
    niveau = models.CharField(max_length=10)
    ecue = models.ForeignKey("ECUE", on_delete=models.CASCADE)

    semestre = models.CharField(max_length=2)
    session = models.CharField(max_length=1, default="1")

    date_creation = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.filiere} - {self.niveau} - {self.ecue}"

class SaisieNoteLMDItem(models.Model):

    saisie = models.ForeignKey(
        "SaisieNoteLMD",
        on_delete=models.CASCADE,
        related_name="items"
    )

    etudiant = models.ForeignKey("EtudiantLMD", on_delete=models.CASCADE)

    cc = models.FloatField(default=0)
    examen = models.FloatField(default=0)

    moyenne = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ("saisie", "etudiant")

    def save(self, *args, **kwargs):
        self.moyenne = round(self.cc * 0.4 + self.examen * 0.6, 2)
        super().save(*args, **kwargs)
