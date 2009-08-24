from django.conf import settings

__all__ = [
    'VCS_ONLY_PUBLIC_REPS',
    'VCS_URL_REWRITER',
    'CHECK_INTERVAL_MIN',
    'CHECK_INTERVAL_MAX',
    'REVISION_LIMIT',
    'DELAY_BETWEEN_UPDATE_CHECK',
    'MONGO_URL',
    'MONGO_DB',
]

VCS_ONLY_PUBLIC_REPS = getattr(settings, 'VCS_ONLY_PUBLIC_REPS', False)
VCS_URL_REWRITER = getattr(settings, 'VCS_URL_REWRITER', lambda x: x)

# Intervals in seconds
CHECK_INTERVAL_MIN = getattr(settings, 'VCS_CHECK_INTERVAL_MIN', 5 * 60)
CHECK_INTERVAL_MAX = getattr(settings, 'VCS_CHECK_INTERVAL_MAX', 5 * 60 * 60)

REVISION_LIMIT = getattr(settings, 'VCS_REVISION_LIMIT', 20)
DELAY_BETWEEN_UPDATE_CHECK = getattr(settings, 'VCS_DELAY_BETWEEN_UPDATE_CHECK', 30)

MONGO_URL = getattr(settings, 'MONGO_URL', 'localhost')
MONGO_DB = getattr(settings, 'MONGO_DB', 'vcs-watch')

