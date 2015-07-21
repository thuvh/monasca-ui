from django.utils.translation import ugettext_lazy as _

# Services being monitored
MONITORING_SERVICES = [
    {'name': _('OpenStack Services'),
     'groupBy': 'service'},
    {'name': _('Servers'),
     'groupBy': 'hostname'}
]

# Grafana button titles/file names
GRAFANA_LINKS = [
    {'title': 'Dashboard', 'fileName': 'openstack.json'},
    {'title': 'Monasca Health', 'fileName': 'monasca.json'}
]

#
# Per project grafana button titles/file names.  If this is set, it
# will override GRAFANA_LINKS setting, to maintain backward compatibility.
# Not specifying a project will result in the default links
#
#PROJECT_GRAFANA_LINKS = [
#    {'admin': [{'title': 'Admin Dashboard', 'fileName': 'admin.json'},
#               {'title': 'Monasca Health', 'fileName': 'monasca.json'}]
#    }
#]
