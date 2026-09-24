# -*- coding: utf-8 -*-
"""Doplneni prekladu do stranek, ktere se upravovaly v editoru.

Co se deje: kdyz nekdo upravi stranku ve website editoru, Odoo ulozi jeji
podobu do vlastni kopie pohledu -- a cesky text zapise do VSECH jazyku
najednou. Na `/de` a `/ru` pak zustane cestina, prestoze modul preklady
ma. Prave takhle vypadala domovska stranka po nasazeni na ostro: 38 textu
zustalo cesky ve vsech jazycich.

PO soubory to nespravi. Ty prekladaji ze zdroje, jenze ve zdroji uz je
cestina, takze se klic netrefi.

Reseni je jit na to od cestiny. Slovnik `data/preklady_stranek.json` drzi
mapu cesky termin -> {en_US, de_DE, ru_RU}; slozil se z PO souboru modulu
pres anglictinu a doplnily se texty, ktere klinika dopsala sama.

Prekladaji se JEDNOTLIVE TERMINY tak, jak je deli samo Odoo (`xml_translate`),
ne cely arch najednou. Diky tomu:

  * spravne prelozeny termin zustava, kde je,
  * text, ktery ve slovniku neni, se nechava byt -- nic se neztrati,
  * jazyk se zapise jen tehdy, kdyz se opravdu neco zmenilo.

Modulovych pohledu se to nedotkne: v nich je ve zdroji anglictina, ktera
ve slovniku (klicovanem cesky) neni.
"""
import json
import logging
import os

_logger = logging.getLogger(__name__)

JAZYKY = ("en_US", "de_DE", "ru_RU")
SLOVNIK = os.path.join(os.path.dirname(__file__), "data", "preklady_stranek.json")


def _nacti_slovnik():
    if not os.path.exists(SLOVNIK):
        _logger.warning("Slovnik prekladu stranek nenalezen: %s", SLOVNIK)
        return {}
    with open(SLOVNIK, encoding="utf-8") as soubor:
        return json.load(soubor)


def _nase_pohledy(env):
    """Pohledy projektu vcetne kopii ulozenych z editoru."""
    Pohled = env["ir.ui.view"].sudo().with_context(active_test=False)
    return Pohled.search([("key", "=like", "elite_vet%")])


def prelozit(env, slovnik=None):
    """Doplni preklady do vsech pohledu projektu.

    Vraci pocet terminu, ktere se opravdu zmenily.
    """
    from odoo.tools.translate import xml_translate

    slovnik = _nacti_slovnik() if slovnik is None else slovnik
    if not slovnik:
        return 0

    jazyky_databaze = set(
        env["res.lang"].sudo().search([("active", "=", True)]).mapped("code"))

    pohledy = _nase_pohledy(env)
    zmeneno_celkem = 0
    dotcene = []

    for pohled in pohledy:
        for jazyk in JAZYKY:
            if jazyk not in jazyky_databaze:
                continue

            v_jazyce = pohled.with_context(lang=jazyk)
            arch = v_jazyce.arch_db
            if not arch:
                continue

            zmeneno = []

            def preloz(termin, _jazyk=jazyk, _zmeneno=zmeneno):
                zaznam = slovnik.get(termin)
                if not zaznam:
                    return termin
                novy = zaznam.get(_jazyk)
                if not novy or novy == termin:
                    return termin
                _zmeneno.append(termin)
                return novy

            novy_arch = xml_translate(preloz, arch)
            if not zmeneno:
                continue

            v_jazyce.arch_db = novy_arch
            zmeneno_celkem += len(zmeneno)
            dotcene.append("%s/%s (%s)" % (pohled.key, jazyk, len(zmeneno)))

    if dotcene:
        _logger.warning(
            "Do stranek doplneny chybejici preklady, %s terminu: %s",
            zmeneno_celkem, ", ".join(dotcene))
    else:
        _logger.info("Stranky: vsechny texty uz maji preklad, neni co doplnovat.")

    return zmeneno_celkem
