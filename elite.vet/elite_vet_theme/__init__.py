from . import jazyky
from . import stranky
from . import web


def _pri_instalaci(env):
    """Bezi po instalaci zakladniho modulu projektu.

    Jazyky se nastavuji tady, protoze tenhle modul se z celeho projektu
    instaluje jako prvni. Ostatni moduly pri instalaci zapisuji preklady
    a do jazyka, ktery jeste neni zapnuty, zapsat nejdou.
    """
    jazyky.nastav(env)
