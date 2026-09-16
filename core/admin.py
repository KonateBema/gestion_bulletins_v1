
from django.contrib import admin
from .models import (
    Niveau,
    Filiere,
    Filierebts,
    Salle,
    Classe,
    Categorie,
    GrandeUnite,
    Matiere,
    Professeur,
    Etudiant,
    AffectationMatiere,
    Inscription,
    SaisieNotesBTS,
    Note,
    Bulletin,
    Profile,
)


# ============================================================
# UIC — PERSONNALISATION DJANGO ADMIN
# ============================================================

admin.site.site_header = "UIC — Administration"
admin.site.site_title = "UIC — Gestion Scolaire"
admin.site.index_title = "Tableau de bord UIC"


# ============================================================
# 1. NIVEAU
# ============================================================

@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nom",
    )

    search_fields = (
        "nom",
    )

    ordering = (
        "nom",
    )


# ============================================================
# 2. FILIÈRE
# ============================================================

@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nom",
    )

    search_fields = (
        "nom",
    )

    ordering = (
        "nom",
    )


# ============================================================
# 3. FILIÈRE BTS
# ============================================================

@admin.register(Filierebts)
class FilierebtsAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nom",
        "afficher_niveaux",
    )

    search_fields = (
        "nom",
        "niveaux__nom",
    )

    filter_horizontal = (
        "niveaux",
    )

    ordering = (
        "nom",
    )

    @admin.display(
        description="Niveaux",
        ordering="niveaux__nom",
    )
    def afficher_niveaux(self, obj):
        return ", ".join(
            niveau.nom
            for niveau in obj.niveaux.all()
        )


# ============================================================
# 4. SALLE
# ============================================================

@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "code",
        "nom",
        "capacite",
        "afficher_effectif",
    )

    search_fields = (
        "code",
        "nom",
    )

    list_filter = (
        "capacite",
    )

    ordering = (
        "code",
    )

    @admin.display(
        description="Effectif",
        ordering="id",
    )
    def afficher_effectif(self, obj):
        return obj.effectif()


# ============================================================
# 5. CLASSE
# ============================================================

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nom",
        "niveau",
        "filiere_bts",
        "salle",
        "annee_academique",
        "afficher_effectif",
    )

    search_fields = (
        "nom",
        "niveau__nom",
        "filiere_bts__nom",
        "salle__code",
        "salle__nom",
    )

    list_filter = (
        "niveau",
        "filiere_bts",
        "salle",
        "annee_academique",
    )

    autocomplete_fields = (
        "niveau",
        "filiere_bts",
        "salle",
    )

    ordering = (
        "niveau",
        "nom",
    )

    @admin.display(
        description="Effectif",
    )
    def afficher_effectif(self, obj):
        return obj.effectif()


# ============================================================
# 6. CATÉGORIE
# ============================================================

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nom",
    )

    search_fields = (
        "nom",
    )

    ordering = (
        "nom",
    )


# ============================================================
# 7. GRANDE UNITÉ
# ============================================================

@admin.register(GrandeUnite)
class GrandeUniteAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "code",
        "libelle",
        "filiere_bts",
        "niveau",
        "ordre",
        "afficher_nombre_matieres",
    )

    search_fields = (
        "code",
        "libelle",
        "filiere_bts__nom",
        "niveau__nom",
    )

    list_filter = (
        "filiere_bts",
        "niveau",
    )

    autocomplete_fields = (
        "filiere_bts",
        "niveau",
    )

    ordering = (
        "ordre",
        "id",
    )

    @admin.display(
        description="Matières",
    )
    def afficher_nombre_matieres(self, obj):
        return obj.matieres.count()


# ============================================================
# 8. MATIÈRE
# ============================================================

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "code",
        "libelle",
        "coefficient",
        "volume_horaire",
        "filiere_bts",
        "categorie",
        "grande_unite",
    )

    search_fields = (
        "code",
        "libelle",
        "filiere_bts__nom",
        "categorie__nom",
        "grande_unite__code",
        "grande_unite__libelle",
    )

    list_filter = (
        "filiere_bts",
        "categorie",
        "grande_unite",
    )

    autocomplete_fields = (
        "filiere_bts",
        "categorie",
        "grande_unite",
    )

    ordering = (
        "filiere_bts",
        "libelle",
    )


# ============================================================
# 9. PROFESSEUR
# ============================================================

@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "matricule",
        "nom",
        "prenoms",
        "telephone",
        "email",
        "specialite",
    )

    search_fields = (
        "matricule",
        "nom",
        "prenoms",
        "telephone",
        "email",
        "specialite",
    )

    list_filter = (
        "specialite",
    )

    ordering = (
        "nom",
        "prenoms",
    )


# ============================================================
# 10. ÉTUDIANT
# ============================================================

@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "matricule",
        "nom",
        "prenoms",
        "sexe",
        "classe",
        "filiere_bts",
        "telephone",
        "email",
    )

    search_fields = (
        "matricule",
        "nom",
        "prenoms",
        "telephone",
        "email",
        "classe__nom",
        "filiere_bts__nom",
    )

    list_filter = (
        "sexe",
        "classe",
        "classe__niveau",
        "filiere_bts",
    )

    autocomplete_fields = (
        "user",
        "classe",
        "filiere_bts",
    )

    ordering = (
        "nom",
        "prenoms",
    )

    fieldsets = (
        (
            "Compte utilisateur",
            {
                "fields": (
                    "user",
                )
            },
        ),
        (
            "Identité",
            {
                "fields": (
                    "matricule",
                    "nom",
                    "prenoms",
                    "date_naissance",
                    "lieu_naissance",
                    "sexe",
                )
            },
        ),
        (
            "Coordonnées",
            {
                "fields": (
                    "telephone",
                    "email",
                )
            },
        ),
        (
            "Scolarité",
            {
                "fields": (
                    "classe",
                    "filiere_bts",
                )
            },
        ),
    )


# ============================================================
# 11. AFFECTATION MATIÈRE / CLASSE / PROFESSEUR
# ============================================================

@admin.register(AffectationMatiere)
class AffectationMatiereAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "classe",
        "matiere",
        "professeur",
    )

    search_fields = (
        "classe__nom",
        "matiere__code",
        "matiere__libelle",
        "professeur__matricule",
        "professeur__nom",
        "professeur__prenoms",
    )

    list_filter = (
        "classe",
        "matiere__filiere_bts",
        "professeur",
    )

    autocomplete_fields = (
        "classe",
        "matiere",
        "professeur",
    )

    ordering = (
        "classe",
        "matiere",
    )


# ============================================================
# 12. INSCRIPTION
# ============================================================

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "etudiant",
        "classe",
        "date",
    )

    search_fields = (
        "etudiant__matricule",
        "etudiant__nom",
        "etudiant__prenoms",
        "classe__nom",
    )

    list_filter = (
        "classe",
        "date",
    )

    autocomplete_fields = (
        "etudiant",
        "classe",
    )

    date_hierarchy = "date"

    ordering = (
        "-date",
    )


# ============================================================
# 13. SAISIE DES NOTES BTS
# ============================================================

@admin.register(SaisieNotesBTS)
class SaisieNotesBTSAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "classe",
        "matiere",
        "annee_academique",
        "semestre",
        "date_saisie",
        "afficher_nombre_notes",
    )

    search_fields = (
        "classe__nom",
        "matiere__code",
        "matiere__libelle",
        "annee_academique",
    )

    list_filter = (
        "annee_academique",
        "semestre",
        "classe",
        "matiere",
    )

    autocomplete_fields = (
        "classe",
        "matiere",
    )

    readonly_fields = (
        "date_saisie",
    )

    date_hierarchy = "date_saisie"

    ordering = (
        "-date_saisie",
    )

    @admin.display(
        description="Nombre de notes",
    )
    def afficher_nombre_notes(self, obj):
        return obj.notes.count()


# ============================================================
# 14. NOTES
# ============================================================

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "etudiant",
        "matiere",
        "semestre",
        "cc",
        "devoir",
        "examen",
        "moyenne",
    )

    search_fields = (
        "etudiant__matricule",
        "etudiant__nom",
        "etudiant__prenoms",
        "matiere__code",
        "matiere__libelle",
    )

    list_filter = (
        "semestre",
        "matiere__filiere_bts",
        "matiere",
    )

    autocomplete_fields = (
        "saisie",
        "etudiant",
        "matiere",
    )

    readonly_fields = (
        "moyenne",
    )

    ordering = (
        "etudiant__nom",
        "matiere__libelle",
    )

    fieldsets = (
        (
            "Étudiant et matière",
            {
                "fields": (
                    "etudiant",
                    "matiere",
                    "saisie",
                    "semestre",
                )
            },
        ),
        (
            "Évaluation",
            {
                "fields": (
                    "cc",
                    "devoir",
                    "examen",
                    "moyenne",
                )
            },
        ),
    )


# ============================================================
# 15. BULLETIN
# ============================================================

@admin.register(Bulletin)
class BulletinAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "etudiant",
        "semestre",
        "annee_academique",
        "moyenne_generale",
        "rang",
        "mention",
        "decision_jury",
    )

    search_fields = (
        "etudiant__matricule",
        "etudiant__nom",
        "etudiant__prenoms",
        "annee_academique",
        "mention",
        "decision_jury",
    )

    list_filter = (
        "semestre",
        "annee_academique",
        "mention",
        "decision_jury",
    )

    autocomplete_fields = (
        "etudiant",
    )

    ordering = (
        "-annee_academique",
        "etudiant__nom",
    )

    fieldsets = (
        (
            "Étudiant",
            {
                "fields": (
                    "etudiant",
                    "semestre",
                    "annee_academique",
                )
            },
        ),
        (
            "Résultats",
            {
                "fields": (
                    "moyenne_generale",
                    "rang",
                    "mention",
                    "decision_jury",
                )
            },
        ),
    )


# ============================================================
# 16. PROFIL UTILISATEUR
# ============================================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "afficher_nom",
        "afficher_email",
        "role",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )

    list_filter = (
        "role",
    )

    autocomplete_fields = (
        "user",
    )

    ordering = (
        "user__username",
    )

    @admin.display(
        description="Nom complet",
    )
    def afficher_nom(self, obj):
        return obj.user.get_full_name()

    @admin.display(
        description="Email",
    )
    def afficher_email(self, obj):
        return obj.user.email

