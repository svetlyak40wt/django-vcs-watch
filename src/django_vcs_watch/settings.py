from django.conf import settings

__all__ = ['VCS_ONLY_PUBLIC_REPS']

VCS_ONLY_PUBLIC_REPS = getattr(settings, 'VCS_ONLY_PUBLIC_REPS', False)

