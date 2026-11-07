# Datos que necesitan TODAS las páginas (aquí, el menú). Django llama a esta
# función en cada página y añade lo que devuelve a su plantilla. Está
# registrada en config/settings.py, en TEMPLATES > context_processors.

from web.views import _empresas_disponibles


def menu(request):
    # Empresas para el selector rápido de la barra de navegación.
    return {"empresas_menu": _empresas_disponibles()}
