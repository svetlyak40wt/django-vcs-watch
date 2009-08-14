from django.conf import settings

__all__ = [
    'VCS_ONLY_PUBLIC_REPS',
    'VCS_URL_REWRITER',
]

VCS_ONLY_PUBLIC_REPS = getattr(settings, 'VCS_ONLY_PUBLIC_REPS', False)
VCS_URL_REWRITER = getattr(settings, 'VCS_URL_REWRITER', lambda x: x)

