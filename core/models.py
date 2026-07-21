from django.db import models
from django.contrib.auth.models import User

# =========================
# 1. NIVEAU
# =========================
class Niveau(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


# =========================
# 2. FILIERE
# =========================
class Filiere(models.Model):
    nom = models.CharField(max_length=150)

    def __str__(self):
        return self.nom

class Filierebts(models.Model):
    nom = models.CharField(max_length=150)

    niveaux = models.ManyToManyField(
        Niveau,
        blank=True,
        related_name="filieres_bts"
    )

    def __str__(self):
        return self.nom

class Salle(models.Model):
    code = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    capacite = models.IntegerField(default=0)
     
    def effectif(self):
        return self.etudiant_set.count()

    def __str__(self):
        return f"{self.code} - {self.nom}"
# =========================
# 3. CLASSE
# =========================
class Classe(models.Model):
    nom = models.CharField(max_length=150)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE)

    filiere_bts = models.ForeignKey(
        Filierebts,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    salle = models.ForeignKey(
        Salle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    annee_academique = models.CharField(
    max_length=20,
    default="2025-2026"
    )

    def __str__(self):
        filiere = self.filiere_bts.nom if self.filiere_bts else "Sans filière"
        return f"{self.niveau.nom} {filiere} {self.nom}"

    def effectif(self):
        return self.etudiants.count()
# =========================
# 4. MATIERE
# =========================
class Categorie(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

class Matiere(models.Model):
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=150)
    coefficient = models.IntegerField(default=1)
    volume_horaire = models.IntegerField(default=0)
    filiere_bts = models.ForeignKey(
        Filierebts,
        on_delete=models.CASCADE
    )
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.libelle


# =========================
# 5. PROFESSEUR
# =========================
class Professeur(models.Model):
    matricule = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30)
    email = models.EmailField()
    specialite = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.nom} {self.prenoms}"


# =========================
# 6. ETUDIANT
# =========================
class Etudiant(models.Model):
    SEXE_CHOICES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    matricule = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=150)

    date_naissance = models.DateField(null=True, blank=True)
    # sexe = models.CharField(max_length=10)
    sexe = models.CharField(
        max_length=10,
        choices=SEXE_CHOICES
    )

    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name="etudiants")

    filiere_bts = models.ForeignKey(
        Filierebts,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Filière BTS"
    )

    def __str__(self):
        return f"{self.nom} {self.prenoms}"


# =========================
# 7. AFFECTATION MATIERE / CLASSE / PROF
# =========================
class AffectationMatiere(models.Model):
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.classe} - {self.matiere}"


# =========================
# 8. INSCRIPTION
# =========================
class Inscription(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)


# =========================
# 9. NOTE
# =========================
class SaisieNotesBTS(models.Model):
    classe = models.ForeignKey(
        Classe,
        on_delete=models.CASCADE,
        related_name="saisies_notes"
    )

    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE
    )
    annee_academique = models.CharField(
    max_length=20,
     default="2025-2026"
    )

    semestre = models.CharField(max_length=10)

    date_saisie = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.classe} - "
            f"{self.matiere.libelle} - "
            f"{self.semestre}"
        )

class Note(models.Model):

    SEMESTRE_CHOICES = [
        ("S1", "Semestre 1"),
        ("S2", "Semestre 2"),
    ]

    saisie = models.ForeignKey(
        SaisieNotesBTS,
        on_delete=models.CASCADE,
        related_name="notes",
        null=True,
        blank=True
    )

    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.CASCADE
    )

    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE
    )

    semestre = models.CharField(
        max_length=2,
        choices=SEMESTRE_CHOICES,
        default="S1"
    )

    cc = models.FloatField(
        default=0
    )  # Contrôle continu

    devoir = models.FloatField(
        default=0
    )

    examen = models.FloatField(
        default=0
    )

    moyenne = models.FloatField(
        null=True,
        blank=True
    )


    def save(self, *args, **kwargs):

        self.moyenne = round(
            (self.cc + self.devoir + self.examen) / 3,
            2
        )

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.etudiant} - {self.matiere} - {self.semestre}"

# =========================
# 10. BULLETIN
# =========================
class Bulletin(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    semestre = models.CharField(max_length=10)

    moyenne_generale = models.FloatField(default=0)
    rang = models.IntegerField(null=True, blank=True)
    mention = models.CharField(max_length=50, blank=True)
    annee_academique = models.CharField(max_length=20,default="2025-2026")

    decision_jury = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.etudiant} - {self.semestre}"



class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('prof', 'Professeur'),
        ('etudiant', 'Etudiant'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


