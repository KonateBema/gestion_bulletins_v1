from functools import wraps

from django.shortcuts import redirect

from .models import Profile


def role_required(*roles):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Utilisateur non connecté
            if not request.user.is_authenticated:
                return redirect("login")

            # Recherche du profil
            profile = Profile.objects.filter(
                user=request.user
            ).first()

            # Profil inexistant
            if not profile:
                return redirect("login")

            # Vérification du rôle
            if profile.role not in roles:
                return redirect("login")

            return view_func(
                request,
                *args,
                **kwargs
            )

        return wrapper

    return decorator