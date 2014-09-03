from monitoring import api
from monitoring.util.decorators import memoize

_METRICS_CACHE = {}

@memoize(_METRICS_CACHE, 60 * 60, 0)
def metrics_list(request):
    return api.monitor.metrics_list(request)

