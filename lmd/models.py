from django.db import models
from django.contrib.auth.models import User

from core.models import Classe, Filiere, Niveau, Etudiant


# =====================
# UE (Unité d’Enseignement)
# =====================

class UE(models.Model):

    SEMESTRE_CHOICES = (
        ("S1", "Semestre 1"),
        ("S2", "Semestre 2"),
        ("S3", "Semestre 3"),
        ("S4", "Semestre 4"),
        ("S5", "Semestre 5"),
        ("S6", "Semestre 6"),
    )

    code = models.CharField(
        max_length=20
    )

    libelle = models.CharField(
        max_length=200
    )

    credit = models.PositiveIntegerField(
        default=0
    )

    filiere = models.ForeignKey(
        "FiliereLMD",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ues"
    )

    grande_unite = models.ForeignKey(
        "GrandeUnite",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ues"
    )

    semestre = models.CharField(
        max_length=2,
        choices=SEMESTRE_CHOICES,
        default="S1"
    )

    def __str__(self):
        return f"{self.code} - {self.libelle}"
# =====================
# ECUE (Élément Constitutif d’UE)
# =====================

class ECUE(models.Model):

    ue = models.ForeignKey(
        UE,
        on_delete=models.CASCADE,
        related_name="ecues"
    )

    code = models.CharField(max_length=20)
    libelle = models.CharField(max_length=200)
    coefficient = models.IntegerField(default=1)
    credit = models.IntegerField(default=1)

    semestre = models.CharField(
        max_length=5,
        choices=[
            ("S1", "Semestre 1"),
            ("S2", "Semestre 2"),
        ],
        default="S1"
    )
    
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
        choices=SEMESTRE_CHOICES,
        default="S1"
    )


    session = models.CharField(
        max_length=1,
        choices=SESSION_CHOICES,
        default="1"
    )


    cc = models.FloatField(
        default=0
    )


    examen = models.FloatField(
        default=0
    )


    moyenne = models.FloatField(
        blank=True,
        null=True,
        editable=False
    )



    class Meta:

        constraints = [

            models.UniqueConstraint(

                fields=[
                    "etudiant",
                    "ecue",
                    "semestre",
                    "session"
                ],

                name="unique_note_par_session"

            )

        ]



    def save(self, *args, **kwargs):

        try:

            cc = float(self.cc or 0)

        except (ValueError, TypeError):

            cc = 0



        try:

            examen = float(self.examen or 0)

        except (ValueError, TypeError):

            examen = 0



        self.cc = cc
        self.examen = examen


        self.moyenne = round(
            (cc * 0.4) + (examen * 0.6),
            2
        )


        super().save(*args, **kwargs)



    def __str__(self):

        return (
            f"{self.etudiant.nom} "
            f"{self.etudiant.prenoms} - "
            f"{self.ecue.libelle} - "
            f"{self.semestre}"
        )

class NoteLMDEN(models.Model):

    etudiant = models.ForeignKey(
        "EtudiantLMD",
        on_delete=models.CASCADE,
        related_name="notes_lmd_en"
    )


    ecue = models.ForeignKey(
        "ECUE",
        on_delete=models.CASCADE,
        related_name="notes_en"
    )
    
# =====================
# ÉTUDIANT LMD (structure académique)
# =====================
class EtudiantLMD(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="etudiant_lmd"
    )

    matricule = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )

    nom = models.CharField(
        max_length=100,
        db_index=True
    )

    prenoms = models.CharField(
        max_length=150
    )


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


    date_naissance = models.DateField(
        null=True,
        blank=True
    )

    lieu_naissance = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    telephone = models.CharField(
        max_length=30,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )


    # ======================
    # STRUCTURE LMD
    # ======================

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
        choices=NIVEAUX,
        db_index=True
    )


    filiere = models.ForeignKey(
        "FiliereLMD",
        on_delete=models.CASCADE,
        related_name="etudiants"
    )


    annee_academique = models.CharField(
        max_length=20,
        db_index=True
    )


    date_inscription = models.DateTimeField(
        auto_now_add=True
    )


    actif = models.BooleanField(
        default=True
    )


    class Meta:

        ordering = [
            "nom",
            "prenoms"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "matricule",
                    "annee_academique"
                ],
                name="unique_etudiant_annee"
            )
        ]


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

    NIVEAUX = [
        ("L1-L2", "Licence Fondamentale"),
        ("L3", "Licence Professionnelle"),
        ("M1-M2", "Master"),
    ]

    code = models.CharField(
        max_length=20,
        unique=True
    )

    libelle = models.CharField(
        max_length=100
    )

    niveau_formation = models.CharField(
        max_length=10,
        choices=NIVEAUX,
        default="L1-L2"
    )

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

    filiere = models.ForeignKey(
        "FiliereLMD",
        on_delete=models.CASCADE
    )

    niveau = models.CharField(
        max_length=10
    )

    ecue = models.ForeignKey(
        "ECUE",
        on_delete=models.CASCADE
    )

    semestre = models.CharField(
        max_length=2
    )

    session = models.CharField(
        max_length=1,
        default="1"
    )

    annee_academique = models.CharField(
        max_length=20,
        default="2025-2026"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
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
    moyenne = models.FloatField(editable=False,null=True)

    class Meta:
        unique_together = ("saisie", "etudiant")

    def save(self, *args, **kwargs):
        self.moyenne = round(self.cc * 0.4 + self.examen * 0.6, 2)
        super().save(*args, **kwargs)
        
class SessionAcademique(models.Model):

    TYPE_SESSION = [
        ("NORMALE", "Session normale"),
        ("RATTRAPAGE", "Session de rattrapage"),
    ]

    libelle = models.CharField(
        max_length=100
    )

    type_session = models.CharField(
        max_length=20,
        choices=TYPE_SESSION
    )

    semestre = models.CharField(
        max_length=2,
        choices=[
            ("S1","Semestre 1"),
            ("S2","Semestre 2"),
            ("S3","Semestre 3"),
            ("S4","Semestre 4"),
            ("S5","Semestre 5"),
            ("S6","Semestre 6"),
        ]
    )

    annee_academique = models.CharField(
        max_length=20
    )

    active = models.BooleanField(
        default=True
    )


    def __str__(self):
        return f"{self.libelle} - {self.semestre}"

# ======================================
# CANDIDATS SESSION DE RATTRAPAGE
# ======================================



class CandidatRattrapage(models.Model):

    STATUT_CHOICES = [
        ("EN_ATTENTE", "En attente"),
        ("VALIDE", "Validé"),
        ("ECHEC", "Échec"),
    ]


    etudiant = models.ForeignKey(
        "EtudiantLMD",
        on_delete=models.CASCADE,
        related_name="candidats_rattrapage"
    )


    ecue = models.ForeignKey(
        "ECUE",
        on_delete=models.CASCADE,
        related_name="candidats_rattrapage"
    )


    session = models.ForeignKey(
        "SessionAcademique",
        on_delete=models.CASCADE,
        related_name="candidats"
    )


    ancienne_note = models.FloatField(
        default=0
    )


    nouvelle_note = models.FloatField(
        null=True,
        blank=True
    )


    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="EN_ATTENTE"
    )


    annee_academique = models.CharField(
        max_length=20
    )


    date_creation = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        unique_together = (
            "etudiant",
            "ecue",
            "session",
            "annee_academique"
        )


    def __str__(self):

        return (
            f"{self.etudiant} - "
            f"{self.ecue} - "
            f"Rattrapage"
        )

class AnneeAcademique(models.Model):

    libelle = models.CharField(
        max_length=20
    )

    active = models.BooleanField(
        default=False
    )


    def __str__(self):
        return self.libelle

class InscriptionLMD(models.Model):

    etudiant = models.ForeignKey(
        EtudiantLMD,
        on_delete=models.CASCADE
    )


    annee = models.ForeignKey(
        AnneeAcademique,
        on_delete=models.CASCADE
    )


    niveau = models.CharField(
        max_length=10
    )


    filiere = models.ForeignKey(
        FiliereLMD,
        on_delete=models.CASCADE
    )


    statut = models.CharField(
        max_length=20,
        default="INSCRIT"
    )

class Semestre(models.Model):

    code = models.CharField(
        max_length=5,
        unique=True
    )

    libelle = models.CharField(
        max_length=50
    )

    ordre = models.IntegerField(
        default=1
    )

    niveau = models.CharField(
        max_length=10,
        choices=[
            ("L1","Licence 1"),
            ("L2","Licence 2"),
            ("L3","Licence 3"),
            ("M1","Master 1"),
            ("M2","Master 2"),
        ]
    )


    def __str__(self):
        return self.libelle

class ValidationUE(models.Model):

    etudiant=models.ForeignKey(
        EtudiantLMD,
        on_delete=models.CASCADE
    )

    ue=models.ForeignKey(
        UE,
        on_delete=models.CASCADE
    )

    moyenne=models.FloatField()

    valide=models.BooleanField()

class Deliberation(models.Model):

    etudiant=models.ForeignKey(
        EtudiantLMD,
        on_delete=models.CASCADE
    )


    moyenne_generale=models.FloatField()


    resultat=models.CharField(
        max_length=30
    )

class EnseignantLMD(models.Model):

    nom=models.CharField(max_length=100)

    prenoms=models.CharField(max_length=100)

    email=models.EmailField(blank=True)

    grade=models.CharField(
        max_length=100,
        blank=True
    )


class AffectationECUE(models.Model):

    enseignant=models.ForeignKey(
        EnseignantLMD,
        on_delete=models.CASCADE
    )


    ecue=models.ForeignKey(
        ECUE,
        on_delete=models.CASCADE
    )

class MasterProgramme(models.Model):

    NIVEAUX = (
        ("M1", "Master 1"),
        ("M2", "Master 2"),
    )


    SPECIALITES = (
        ("QHSE", "Management QHSE"),
        ("DROIT", "Droit Privé"),
        ("GESTION", "Sciences de Gestion"),
    )


    niveau = models.CharField(
        max_length=2,
        choices=NIVEAUX
    )


    specialite = models.CharField(
    max_length=20,
    choices=SPECIALITES,
    default="GESTION",
   )
    filiere = models.ForeignKey(
        FiliereLMD,
        on_delete=models.CASCADE,
        related_name="programmes_master",
        null=True,
        blank=True
    )


    annee_academique = models.CharField(
        max_length=20,
        default="2025-2026"
    )


    def __str__(self):

        return f"{self.get_niveau_display()} - {self.get_specialite_display()}"
    
class MasterUE(models.Model):

    programme = models.ForeignKey(
        MasterProgramme,
        on_delete=models.CASCADE,
        related_name="ues"
    )


    code = models.CharField(
        max_length=20
    )


    libelle = models.CharField(
        max_length=200
    )


    credit = models.IntegerField(
        default=0
    )


    semestre = models.CharField(
        max_length=2,
        choices=[
            ("S1","Semestre 1"),
            ("S2","Semestre 2"),
            ("S3","Semestre 3"),
            ("S4","Semestre 4"),
        ]
    )


    def __str__(self):
        return self.libelle

class MasterECUE(models.Model):

    ue = models.ForeignKey(
        MasterUE,
        on_delete=models.CASCADE,
        related_name="ecues"
    )


    code = models.CharField(
        max_length=20
    )


    libelle = models.CharField(
        max_length=200
    )


    coefficient = models.IntegerField(
        default=1
    )


    credit = models.IntegerField(
        default=0
    )


    def __str__(self):
        return self.libelle

class EtudiantMaster(models.Model):

    SEXE_CHOICES = (
        ("M", "Masculin"),
        ("F", "Féminin"),
    )


    NIVEAU_CHOICES = (
        ("M1", "Master 1"),
        ("M2", "Master 2"),
    )


    STATUT_CHOICES = (
        ("AF", "Admis Formation"),
        ("NF", "Non Formation"),
    )


    matricule = models.CharField(
        max_length=50,
        unique=True
    )


    nom = models.CharField(
        max_length=100
    )


    prenoms = models.CharField(
        max_length=150
    )


    sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES
    )


    programme = models.ForeignKey(
        MasterProgramme,
        on_delete=models.CASCADE,
        related_name="etudiants"
    )


    niveau = models.CharField(
        max_length=2,
        choices=NIVEAU_CHOICES
    )


    statut = models.CharField(
        max_length=2,
        choices=STATUT_CHOICES,
        default="NF"
    )


    telephone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )


    email = models.EmailField(
        blank=True,
        null=True
    )


    date_naissance = models.DateField(
        blank=True,
        null=True
    )


    lieu_naissance = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    def __str__(self):

        return f"{self.nom} {self.prenoms} - {self.niveau}"
    
class NoteMasterHH(models.Model):

    etudiant = models.ForeignKey(
        EtudiantMaster,
        on_delete=models.CASCADE
    )


    ecue = models.ForeignKey(
        MasterECUE,
        on_delete=models.CASCADE
    )


    cc = models.FloatField(
        default=0
    )


    examen = models.FloatField(
        default=0
    )


    @property
    def moyenne(self):

        return round(
            self.cc*0.4 + self.examen*0.6,
            2
        )

class NoteMaster(models.Model):

    etudiant = models.ForeignKey(
        EtudiantMaster,
        on_delete=models.CASCADE
    )

    ecue = models.ForeignKey(
        MasterECUE,
        on_delete=models.CASCADE
    )

    cc = models.FloatField(
        default=0
    )

    examen = models.FloatField(
        default=0
    )


    @property
    def moyenne(self):

        return round(
            (self.cc * 0.4) + (self.examen * 0.6),
            2
        )


    class Meta:

        unique_together = (
            "etudiant",
            "ecue",
        )
# =====================================
# MASTER FILIERE
# =====================================

class MasterFiliere(models.Model):

    libelle = models.CharField(
        max_length=150
    )


    def __str__(self):
        return self.libelle

class ResultatSemestreMaster(models.Model):

    etudiant = models.ForeignKey(
        EtudiantMaster,
        on_delete=models.CASCADE
    )


    semestre = models.CharField(
        max_length=10
    )


    moyenne = models.FloatField(
        default=0
    )


    credits_obtenus = models.IntegerField(
        default=0
    )


    resultat = models.CharField(
        max_length=20,
        default="RATTRAPAGE"
    )



    def __str__(self):

        return f"{self.etudiant} - {self.semestre}"
    