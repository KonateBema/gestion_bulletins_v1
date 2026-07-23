from django.urls import path
from . import views

urlpatterns = [

    # =====================
    # NIVEAUX
    # =====================
    path('niveaux/', views.niveau_list, name='niveau_lmd_list'),
    path('niveaux/add/', views.niveau_add, name='niveau_lmd_add'),

    # =====================
    # FILIERES
    # =====================
    path('filieres/', views.filiere_list, name='filiere_lmd_list'),
    # path('filieres/add/', views.filiere_add, name='filiere_lmd_add'),
    path('filieres/edit/<int:pk>/', views.filiere_edit, name='filiere_lmd_edit'),
    path('filieres/delete/<int:pk>/', views.filiere_delete, name='filiere_lmd_delete'),

    # =====================
    # CLASSES LMD
    # =====================
    path('classes/', views.classe_list, name='classe_lmd_list'),
    path('classes/add/', views.classe_add, name='classe_lmd_add'),

    # UE
    path('ue/', views.ue_list, name='ue_list'),
    path('ue/add/', views.ue_add, name='ue_add'),
    path('ue/edit/<int:pk>/', views.ue_edit, name='ue_edit'),
    path('ue/delete/<int:pk>/', views.ue_delete, name='ue_delete'),

    # =====================
    # ECUE
    # =====================
    # path('ecue/', views.ecue_list, name='ecue_list'),
    # path('ecue/add/', views.ecue_add, name='ecue_add'),


    path('ecue/', views.ecue_list, name='ecue_list'),
    path('ecue/add/', views.ecue_add, name='ecue_add'),
    path('ecue/edit/<int:pk>/', views.ecue_edit, name='ecue_edit'),
    path('ecue/delete/<int:pk>/', views.ecue_delete, name='ecue_delete'),

    # =====================
    # NOTES LMD
    # =====================
    # path('notes/', views.note_lmd_list, name='note_lmd_list'),
    path('notes/add/', views.note_lmd_add, name='note_lmd_add'),

    # =====================
    # BULLETINS LMD
    # =====================
    # path('bulletins/', views.bulletin_lmd_list, name='bulletin_lmd_list'),
    
    path('bulletins-lmd/',views.bulletin_lmd_list,name='bulletin_lmd_list'),
     

    # =====================
    # ETUDIANTS LMD
    # =====================
    path('etudiants/', views.etudiant_lmd_list, name='etudiant_lmd_list'),
    path('etudiants/add/', views.etudiant_lmd_add, name='etudiant_lmd_add'),
    path("etudiants/<int:pk>/edit/", views.etudiant_lmd_update, name="etudiant_lmd_update"),
    path("etudiants/<int:pk>/delete/", views.etudiant_lmd_delete, name="etudiant_lmd_delete"),
    path("etudiants/<int:pk>/edit/", views.etudiant_lmd_update, name="etudiant_lmd_edit"),


    path('bulletin-lmd/<int:etudiant_id>/',views.bulletin_lmd_pdf,name='bulletin_lmd_pdf'),
    path('bulletins/<int:etudiant_id>/', views.bulletin_lmd_pdf, name='bulletin_lmd_pdf'),

    path('notes-lmd/', views.note_lmd_list, name='note_lmd_list'),
    path('notes-lmd/add/', views.note_lmd_add, name='note_lmd_add'),
    path('notes-lmd/edit/<int:pk>/', views.note_lmd_edit, name='note_lmd_edit'),
    path('notes-lmd/delete/<int:pk>/', views.note_lmd_delete, name='note_lmd_delete'),

    # path("notes/add/", note_ecue_lmd_add, name="note_ecue_lmd_add"),
    # path("notes/save/", note_lmd_save_batch, name="note_lmd_save_batch"),
     path("notes-lmd/saisie/",views.note_lmdecue_add,name="note_lmdecue_add",),
    # Enregistrement des notes
    path("notes-lmd/save/",views.note_lmd_save_batch,name="note_lmd_save_batch",),
    path("notes/",views.note_lmd_listecue,name="note_lmd_listecue",),
      # LISTE
    path("saisies/", views.saisie_list, name="saisie_list"),
    # CREATE
    path("saisies/add/", views.saisie_add, name="saisie_add"),
    # UPDATE
    path("saisies/<int:pk>/edit/", views.saisie_edit, name="saisie_edit"),
    # DELETE
    path("saisies/<int:pk>/delete/", views.saisie_delete, name="saisie_delete"),
    # DETAIL (voir notes des étudiants)
    path("saisies/<int:pk>/", views.saisie_detail, name="saisie_detail"),

    
    path("filieresLMD/", views.filiereLMD_list, name="filiereLMD_list"),
    path("filieresLMD/add/", views.filiereLMD_add, name="filiereLMD_add"),
    path("filieres/", views.filiereLMD_list, name="filiere_list"),
    path("filieres/add/", views.filiereLMD_add, name="filiere_add"),
    path("filieres/", views.filiereLMD_list, name="filiereLMD_list"),

    path("filieres/<int:pk>/edit/", views.filiere_edit, name="filiereLMD_edit"),
    path("filieres/<int:pk>/delete/", views.filiere_delete, name="filiereLMD_delete"),

  # =====================
# FILIERES LMD (CLEAN)
# =====================

    path("filieres/<int:pk>/edit/", views.filiere_edit, name="filiere_edit"),
    path("filieres/<int:pk>/delete/", views.filiere_delete, name="filiere_delete"),
    path("filieres/add/", views.filiere_add, name="filiere_add"),
    path("filieres/", views.filiere_list, name="filiere_list"),

    path("saisies/<int:pk>/etudiants/",views.saisie_note_etudiant,name="saisie_note_etudiant"),
    path("saisies/<int:pk>/notes/",views.saisie_note_etudiant,name="saisie_note_etudiant"),
    # path("saisies/<int:pk>/notes/", views.saisie_note_etudiant, name="saisie_note_etudiant")
    path("lmd/saisies/<int:pk>/notes/",views.enregistrer_notes,name="saisie_note_etudiant"),
    path("saisie/<int:saisie_id>/ajouter-etudiants/",views.ajouter_etudiants_saisie,name="ajouter_etudiants_saisie"),
    path("master/<int:id>/",views.filiere_master_detail,name="filiere_master_detail"),
    
    path("rattrapage/",views.liste_rattrapage,name="rattrapage_liste"),
    path("rattrapage/saisie/",views.saisie_rattrapage,name="saisie_rattrapage"),
    path("rattrapage/",views.liste_rattrapage,name="liste_rattrapage"),
    path("rattrapage/deliberation/",views.deliberation_rattrapage,name="deliberation_rattrapage"),
    path("rattrapage/bulletins/",views.bulletin_rattrapage_list,name="bulletin_rattrapage_list"),

    path("l3/droit/",views.l3_droit_dashboard,name="l3_droit_dashboard"),
    path("l3/gestion/",views.l3_gestion_dashboard,name="l3_gestion_dashboard"),
  
    path("l3/droit/ue/",views.l3_droit_ue,name="l3_droit_ue"),
    path("l3/droit/notes/",views.l3_droit_notes,name="l3_droit_notes"),

    path("l3/droit/bulletins/",views.l3_droit_bulletins,name="l3_droit_bulletins"),

    path("l3/gestion/etudiants/",views.l3_gestion_etudiants,name="l3_gestion_etudiants"),
    path("l3/gestion/ue/",views.l3_gestion_ue,name="l3_gestion_ue"),
    # path("l3/gestion/notes/",views.l3_gestion_notes,name="l3_gestion_notes"),


    path("l3/gestion/notes/<int:ecue_id>/",views.l3_gestion_notes,name="l3_gestion_notes"),
    path(
    "l3/gestion/notes/",
    views.l3_gestion_notes_selection,
    name="l3_gestion_notes"
    ),

    path(
    "l3/gestion/notes/<int:ecue_id>/",
    views.l3_gestion_saisie_notes,
    name="l3_gestion_saisie_notes"
    ),


    path("l3/gestion/bulletins/",views.l3_gestion_bulletins,name="l3_gestion_bulletins"),

    # ================= MASTER =================


   path("master/",views.master_dashboard, name="master_dashboard"),
   path("master/filieres/",views.master_filiere_list,name="master_filiere_list"),
   path("master/etudiants/",views.master_etudiant_list,name="master_etudiant_list"),
   path("master/ue/",views.master_ue_list,name="master_ue_list"),
   path("master/<int:id>/ue/",views.master_ue, name="master_ue",),

   
   path("master/bulletins/",views.master_bulletin_list,name="master_bulletin_list"),


 
   path("l3/droit/etudiants/",views.l3_droit_etudiants,name="l3_droit_etudiants"),
   path("l3/droit/etudiants/add/",views.l3_droit_etudiant_add,name="l3_droit_etudiant_add"),
   path("l3/droit/etudiants/<int:pk>/edit/",views.l3_droit_etudiant_update,name="l3_droit_etudiant_update"),
   path("l3/droit/etudiants/<int:pk>/delete/",views.l3_droit_etudiant_delete,name="l3_droit_etudiant_delete"),

   path("l3/droit/ue/",views.l3_droit_ue,name="l3_droit_ue"),
   path("l3/droit/ue/add/",views.l3_droit_ue_add,name="l3_droit_ue_add"),
   path("l3/droit/ue/<int:pk>/edit/",views.l3_droit_ue_update,name="l3_droit_ue_update"),
   path("l3/droit/ue/<int:pk>/delete/",views.l3_droit_ue_delete,name="l3_droit_ue_delete"),

   path("l3/droit/ue/",views.l3_droit_ue,name="l3_droit_ue"),
   path("l3/droit/ue/add/",views.l3_droit_ue_add,name="l3_droit_ue_add"),
   path("l3/droit/ue/<int:pk>/edit/",views.l3_droit_ue_update,name="l3_droit_ue_update"),
   path("l3/droit/ue/<int:pk>/delete/",views.l3_droit_ue_delete,name="l3_droit_ue_delete"),
   path("l3/droit/ue/<int:pk>/ecues/",views.l3_droit_ecue,name="l3_droit_ecue"),
   path("l3/droit/ue/<int:pk>/ecue/add/",views.l3_droit_ecue_add,name="l3_droit_ecue_add"),
   path("l3/droit/ecue/<int:pk>/update/",views.l3_droit_ecue_update,name="l3_droit_ecue_update"),
   path("l3/droit/ecue/<int:pk>/delete/",views.l3_droit_ecue_delete,name="l3_droit_ecue_delete"),

   path("l3/droit/saisie-notes/<int:ecue_id>/",views.l3_droit_saisie_notes,name="l3_droit_saisie_notes"),
   path("l3/droit/notes/",views.l3_droit_notes,name="l3_droit_notes"),

   path("l3/droit-prive/notes/detail/",views.l3_droit_prive_notes_detail,name="l3_droit_prive_notes_detail"),
    # path("l3/droit-prive/bulletins/",views.bulletin_l3_droit_prive,name="bulletin_l3_droit_prive"),
   path("l3/droit-prive/bulletins/",views.liste_bulletins_l3_droit_prive,name="bulletin_l3_droit_prive"),


   path("l3/droit/ecue/delete/<int:pk>/",views.l3_droit_ecue_delete,name="l3_droit_ecue_delete"),

    # path("l3/droit-prive/bulletin/<int:pk>/",views.imprimer_bulletin_l3_droit_prive,name="imprimer_bulletin_l3_droit_prive"),
  #  path("l3/droit-prive/bulletin/<int:pk>/",views.imprimer_bulletin_l3_droit_prive, name="imprimer_bulletin_l3_droit_prive"),
   
   path(
    "l3-droit-prive/bulletin/<int:id>/<str:semestre>/",
    views.imprimer_bulletin_l3_droit_prive,
    name="imprimer_bulletin_l3_droit_prive",
    ),
   
   
   path("l3/sciences-gestion/etudiants/",views.l3_sciences_gestion_etudiants,name="l3_sciences_gestion_etudiants"),

   path("l3/sciences-gestion/etudiants/",views.l3_gestion_etudiant_list,name="l3_gestion_etudiant_list"),

   path("l3/sciences-gestion/etudiant/add/",views.l3_gestion_etudiant_add,name="l3_gestion_etudiant_add"),

   path("l3/sciences-gestion/etudiant/<int:pk>/edit/",views.l3_gestion_etudiant_edit,name="l3_gestion_etudiant_edit"),

   path("l3/sciences-gestion/etudiant/<int:pk>/delete/",views.l3_gestion_etudiant_delete,name="l3_gestion_etudiant_delete"),
   path("l3/gestion/ue/add/",views.l3_gestion_ue_add, name="l3_gestion_ue_add"),

    # path( "l3/gestion/ue/",views.l3_gestion_ue,name="l3_gestion_ue_list"),
   path("l3/gestion/ue/",views.l3_gestion_ue_list, name="l3_gestion_ue_list"),
   path( "l3/gestion/ecue/<int:ecue_id>/notes/",views.l3_gestion_saisie_notes, name="l3_gestion_saisie_notes"),
   path("l3/gestion/ue/<int:ue_id>/ecues/",views.l3_gestion_ecue_list,name="l3_gestion_ecue_list"),

    # ===============================
# L3 SCIENCES DE GESTION - UE
# ===============================
   path("l3/gestion/ue/",views.l3_gestion_ue, name="l3_gestion_ue"),
   path("l3/gestion/ue/add/", views.l3_gestion_ue_add,name="l3_gestion_ue_add"),
   path("l3/gestion/ue/<int:pk>/edit/",views.l3_gestion_ue_edit,name="l3_gestion_ue_edit"),

   path("l3/gestion/ue/<int:pk>/delete/", views.l3_gestion_ue_delete,name="l3_gestion_ue_delete"),

      # ===============================
# L3 SCIENCES DE GESTION - ECUE
# ===============================

   path("l3/gestion/ue/<int:ue_id>/ecues/",views.l3_gestion_ecue_list, name="l3_gestion_ecue_list"),
   path("l3/gestion/ue/<int:ue_id>/ecue/add/",views.l3_gestion_ecue_add,name="l3_gestion_ecue_add"),
   # ==========================
# ECUE L3 SCIENCES GESTION
# ==========================

   path("l3/gestion/ecue/<int:pk>/edit/",views.l3_gestion_ecue_edit, name="l3_gestion_ecue_edit"),
   path("l3/gestion/ecue/<int:pk>/delete/",views.l3_gestion_ecue_delete,name="l3_gestion_ecue_delete"),
   path("gestion/bulletins/",views.liste_bulletins_gestion,name="liste_bulletins_gestion"),
  #  path("gestion/bulletin/<int:etudiant_id>/pdf/",views.bulletin_gestion_lmd_pdf,name="bulletin_gestion_lmd_pdf"),
   
   path("l3-gestion/bulletin/<int:id>/<str:semestre>/",views.bulletin_gestion_lmd_pdf,name="bulletin_gestion_lmd_pdf"),
   
   path("tronc-commun/bulletins/",views.liste_bulletins_tronc_commun,name="liste_bulletins_tronc_commun"),
   path("tronc-commun/bulletin/<int:pk>/",views.imprimer_bulletin_tronc_commun,name="imprimer_bulletin_tronc_commun"),
   # trom commun
   path("tronc-commun/etudiants/",views.liste_etudiants_tronc_commun,name="liste_etudiants_tronc_commun"),
   path("tronc-commun/etudiant/add/",views.ajouter_etudiant_tronc_commun,name="ajouter_etudiant_tronc_commun"),

  # ===============================
# TRONC COMMUN L1-L2
# ===============================
  path("tronc-commun/etudiants/",views.tronc_commun_etudiants,name="tronc_commun_etudiants"),

  path("tronc-commun/ue/",views.tronc_commun_ue,name="tronc_commun_ue"),
  # path("tronc-commun/notes/",views.tronc_commun_notes, name="tronc_commun_notes"),
  path("tronc-commun/bulletins/",views.bulletin_tronc_commun_list,name="bulletin_tronc_commun_list"),
  path("tronc-commun/droit/", views.tronc_commun_droit,name="tronc_commun_droit"),
  path("tronc-commun/gestion/", views.tronc_commun_gestion,name="tronc_commun_gestion"),
  path("tronc-commun/notes/",views.tronc_commun_notes,name="tronc_commun_notes"),
  # path("tronc-commun/bulletin/<int:pk>/",views.bulletin_tronc_commun_pdf,name="bulletin_tronc_commun_pdf"),
  path("bulletin/tronc-commun/<int:id>/<str:semestre>/",views.bulletin_tronc_commun_pdf, name="bulletin_tronc_commun_pdf"),
  
  path("tronc-commun/bulletin/<int:pk>/",views.imprimer_bulletin_tronc_commun,name="bulletin_tronc_commun_pdf"),
  path("tronc-commun/bulletin/imprimer/<int:pk>/",views.imprimer_bulletin_tronc_commun,name="bulletin_tronc_commun_pdf"),
  path("tronc-commun/add/",views.tronc_commun_add,name="tronc_commun_add"),
  path("tronc-commun/update/<int:pk>/",views.tronc_commun_update,name="tronc_commun_update"),
  path("l3/qhse/dashboard/",views.l3_qhse_dashboard,name="l3_qhse_dashboard"),

  path("l3/qhse/etudiants/",views.l3_qhse_etudiants,name="l3_qhse_etudiants"),
  path("l3/qhse/ue/",views.l3_qhse_ue,name="l3_qhse_ue"),
  path("l3/qhse/notes/",views.l3_qhse_notes,name="l3_qhse_notes"),
  path("l3/qhse/bulletins/",views.l3_qhse_bulletins,name="l3_qhse_bulletins"),
  # path("l3/qhse/etudiants/",views.l3_qhse_etudiants,name="l3_qhse_etudiants"),
  path("l3/qhse/etudiants/add/",views.l3_qhse_etudiant_add,name="l3_qhse_etudiant_add"),
  path("l3/qhse/etudiants/<int:pk>/update/",views.l3_qhse_etudiant_update,name="l3_qhse_etudiant_update"),
  path("l3/qhse/etudiants/<int:pk>/delete/",views.l3_qhse_etudiant_delete,name="l3_qhse_etudiant_delete"),
  path("l3/qhse/ecue/add/<int:ue_id>/",views.l3_qhse_ecue_add,name="l3_qhse_ecue_add"),
  path("l3/qhse/ecue/update/<int:pk>/", views.l3_qhse_ecue_update,name="l3_qhse_ecue_update"),
  path("l3/qhse/ecue/delete/<int:pk>/", views.l3_qhse_ecue_delete, name="l3_qhse_ecue_delete"),
   # QHSE UE CRUD
  path("l3/qhse/ue/",views.l3_qhse_ue,name="l3_qhse_ue"),
  path("l3/qhse/ue/update/<int:pk>/",views.l3_qhse_ue_update,name="l3_qhse_ue_update"),
  path("l3/qhse/ue/add/",views.l3_qhse_ue_add,name="l3_qhse_ue_add"),
  path("l3/qhse/ue/delete/<int:pk>/",views.l3_qhse_ue_delete,name="l3_qhse_ue_delete"),
  
  path("master/",views.master_dashboard,name="master_dashboard"),
  path("master/<int:id>/ue/",views.master_ue,name="master_ue"),
  path("master/ue/<int:id>/ecue/",views.master_ecue,name="master_ecue"),
#   path("master/ecue/<int:id>/notes/",views.master_saisie_notes,name="master_saisie_notes"),
path(
    "master/ecue/<int:id>/notes/",
    views.master_saisie_notes_ecue,
    name="master_saisie_notes_ecue"
),
path(
    "master/notes/",
    views.master_saisie_notes,
    name="master_saisie_notes"
),
  # ==========================
# MASTER NOTES
# ==========================

path(
    "master/ecue/<int:id>/notes/",
    views.master_saisie_notes,
    name="master_saisie_notes"
),
  # ==========================
# MASTER ETUDIANTS
# ==========================
   path(
    "master/notes/",
    views.master_saisie_notes,
    name="master_saisie_notes"
),
   path(
    "master/ecue/<int:id>/notes/",
    views.master_saisie_notes_ecue,
    name="master_saisie_notes_ecue"
),


  path("master/etudiants/",views.master_etudiant_list,name="master_etudiant_list"),
  path("master/etudiant/add/",views.master_etudiant_add,name="master_etudiant_add"),
  path("master/etudiant/<int:id>/edit/",views.master_etudiant_edit,name="master_etudiant_edit"),
  path("master/etudiant/<int:id>/delete/",views.master_etudiant_delete,name="master_etudiant_delete"),
  
  path("master/programmes/add/",views.master_programme_add,name="master_programme_add"),
  
#   path("master/ue/add/",views.master_ue_add,name="master_ue_add"),
  path(
    "master/<int:id>/ue/add/",
    views.master_ue_add,
    name="master_ue_add"
),
  path("master/<int:id>/ue/add/",views.master_ue_add,name="master_ue_add"),
  path("master/ue/edit/<int:id>/",views.master_ue_edit,name="master_ue_edit"),
  path("master/ue/delete/<int:id>/",views.master_ue_delete,name="master_ue_delete"),
  path("master/ecue/add/",views.master_ecue_add,name="master_ecue_add"),
  path("master/<int:id>/ue/add/",views.master_ue_add,name="master_ue_add"),
  path("master/ue/<int:id>/ecue/",views.master_ecue,name="master_ecue"),
  path("master/ue/<int:id>/ecue/add/",views.master_ecue_add,name="master_ecue_add"),
  
  path("master/programmes/",views.master_programme_list,name="master_programme_list",),
  path("master/programmes/add/",views.master_programme_add,name="master_programme_add"),

  path("master/programmes/<int:id>/edit/",views.master_programme_edit,name="master_programme_edit"),

  path("master/programmes/<int:id>/delete/",views.master_programme_delete,name="master_programme_delete"),
  
  # path("master/bulletins/<int:id>/pdf/",views.master_bulletin_pdf, name="master_bulletin_pdf"),
  path(
    "master/bulletin/<int:id>/<str:semestre>/",
    views.master_bulletin_pdf,
    name="master_bulletin_pdf"
),
  # path("licence/qhse/bulletin/<int:pk>/",views.imprimer_bulletin_licence_qhse,name="imprimer_bulletin_licence_qhse"),
  # path("bulletin/qhse/<int:pk>/<str:semestre>/",views.imprimer_bulletin_licence_qhse,name="imprimer_bulletin_licence_qhse"),
  path(
    "bulletin/qhse/<int:pk>/<str:semestre>/",
    views.imprimer_bulletin_licence_qhse,
    name="imprimer_bulletin_licence_qhse"
),
  
  path(
    "l3/qhse/etudiants/<int:pk>/update/",
    views.l3_qhse_etudiant_update,
    name="l3_qhse_etudiant_update"),
  path(
    "tronc-commun/ue/add/",
    views.l3_tc_ue_add,
    name="l3_tc_ue_add",
    ),
  path(
    "tronc-commun/ecue/add/<int:ue_id>/",
    views.l3_tc_ecue_add,
    name="l3_tc_ecue_add"
  ),


  path(
    "tronc-commun/ecue/<int:pk>/update/",
    views.l3_tc_ecue_update,
    name="l3_tc_ecue_update"
   ),
  path(
    "tronc-commun/ue/<int:pk>/update/",
    views.l3_tc_ue_update,
    name="l3_tc_ue_update"
),


path(
    "tronc-commun/ue/<int:pk>/delete/",
    views.l3_tc_ue_delete,
    name="l3_tc_ue_delete"
),


  path(
    "tronc-commun/ecue/<int:pk>/delete/",
    views.l3_tc_ecue_delete,
    name="l3_tc_ecue_delete"
  ),
  path(
    "tronc-commun/ue/",
    views.tronc_commun_ue,
    name="l3_tc_ue_list"
   ),
  path(
"rattrapage/",
views.rattrapage_liste,
name="rattrapage_liste"
),


path(
"rattrapage/saisie/<int:id>/",
views.saisie_rattrapage,
name="saisie_rattrapage"
),
path(
    "rattrapage/",
    views.rattrapage_liste,
    name="rattrapage_liste"
),
  
 path(
    "bulletin-rattrapage/pdf/<int:id>/",
    views.bulletin_rattrapage_pdf,
    name="bulletin_rattrapage_pdf"
),
 path(
    "bulletin-rattrapage/pdf/<int:id>/<str:semestre>/",
    views.bulletin_rattrapage_pdf,
    name="bulletin_rattrapage_pdf"
),

]