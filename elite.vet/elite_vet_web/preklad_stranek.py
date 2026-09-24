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

# Cestina tu MUSI byt taky. Ulozena stranka ma cestinu jen ve zdrojovem
# slotu en_US a ostatni jazyky na nej padaji zpatky. Kdyz se do zdroje zapise
# anglictina a cestina nedostane vlastni hodnotu, spadne na anglictinu cely
# web -- coz se pri prvnim pokusu presne stalo.
JAZYKY = ("cs_CZ", "de_DE", "ru_RU", "en_US")
SLOVNIK = os.path.join(os.path.dirname(__file__), "data", "preklady_stranek.json")


def _nacti_slovnik():
    """Vrati mapu termin -> preklady, hledatelnou cesky i anglicky.

    Zdroj byva cesky (stranka ulozena z editoru), ale kdyz uz se jednou
    prelozil, je anglicky. Aby se dal pustit i podruhe, zna slovnik obe
    podoby terminu.
    """
    if not os.path.exists(SLOVNIK):
        _logger.warning("Slovnik prekladu stranek nenalezen: %s", SLOVNIK)
        return {}
    with open(SLOVNIK, encoding="utf-8") as soubor:
        cesky = json.load(soubor)

    slovnik = {}
    for termin, preklady in cesky.items():
        zaznam = dict(preklady, cs_CZ=termin)
        slovnik[termin] = zaznam
        anglicky = preklady.get("en_US")
        if anglicky and anglicky not in slovnik:
            slovnik[anglicky] = zaznam
    return slovnik


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
        # Zdroj se precte JEDNOU a dopredu. Vsechny jazyky se pocitaji z nej,
        # protoze prepsani zdroje by tem dalsim podtrhlo zem pod nohama.
        zdroj = pohled.with_context(lang="en_US").arch_db
        if not zdroj:
            continue

        hotove = {}
        zmeneno_v_pohledu = 0

        for jazyk in JAZYKY:
            if jazyk not in jazyky_databaze:
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

            hotove[jazyk] = xml_translate(preloz, zdroj)
            if zmeneno:
                zmeneno_v_pohledu += len(zmeneno)
                dotcene.append("%s/%s (%s)" % (pohled.key, jazyk, len(zmeneno)))

        if not zmeneno_v_pohledu:
            continue

        # Zapisuje se az ted a do VSECH jazyku, cestinu nevyjimaje. Jazyk bez
        # vlastni hodnoty pada zpatky na zdroj, a v tom uz bude anglictina.
        for jazyk, arch in hotove.items():
            pohled.with_context(lang=jazyk).arch_db = arch
        zmeneno_celkem += zmeneno_v_pohledu

    if dotcene:
        _logger.warning(
            "Do stranek doplneny chybejici preklady, %s terminu: %s",
            zmeneno_celkem, ", ".join(dotcene))
    else:
        _logger.info("Stranky: vsechny texty uz maji preklad, neni co doplnovat.")

    return zmeneno_celkem
