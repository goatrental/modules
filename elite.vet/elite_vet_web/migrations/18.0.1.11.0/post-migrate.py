# -*- coding: utf-8 -*-
"""Uklid zbytku po strankach, ktere se drive psaly rucne do archu.

Na devu elite-dev.varyshop.eu se ukazaly dve veci, ktere modul nedokaze
prepsat sam od sebe, protoze vznikly v databazi mimo nej:

1. Dedici pohledy `gen_key.*` po starem prepinaci jazyku miri pres `xpath`
   na `div.ev-lang-panel`. Novy header takovy prvek nema, takze Odoo
   rodicovsky pohled vubec nevykresli a stranka vraci 500. Takhle padal
   `/rozpis-lekaru` ve vsech ctyrech jazycich.

2. Pohled se stejnym klicem a stejnym webem mohl v databazi vzniknout
   dvakrat. Editor pak pri otevreni spadne na
   `Expected singleton: ir.ui.view(2773, 2785)` a nejde ulozit zadna uprava.

Uklid sahne jen na pohledy naseho projektu. Cizi pohled se nikdy nemaze,
`gen_key.*` se jen vypne -- a jen kdyz jeho `xpath` v rodici opravdu nic
nenajde. Stranky se nechavaji byt: odpublikovat "dvojnika" na `/` znamena
rozbit domovskou stranku, kdyz na ni web ukazuje prave tou druhou.
"""
import logging

from lxml import etree

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

PREDPONA = "elite_vet"
# Klice pohledu, ktere po sobe zanechal rucne psany web pred moduly.
ZBYTKY = "gen_key."


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _vypni_zbytky_s_mrtvym_xpath(env)
    _smaz_dvojniky_pohledu(env)


def _nas(pohled):
    """Pozna pohled, ktery pochazi z nektereho modulu projektu."""
    return (pohled.key or "").startswith(PREDPONA)


def _strom(pohled):
    """Arch pohledu jako strom, nebo None kdyz se neda precist."""
    arch = pohled.arch_db
    if isinstance(arch, dict):
        arch = arch.get("en_US") or next(iter(arch.values()), None)
    if not arch:
        return None
    try:
        return etree.fromstring(arch)
    except etree.XMLSyntaxError:
        return None


# ---------------------------------------------------------------------------
# 1. zbytky stareho webu, jejichz xpath uz v rodici nic nenajde
# ---------------------------------------------------------------------------
def _vypni_zbytky_s_mrtvym_xpath(env):
    Pohled = env["ir.ui.view"]
    zbytky = Pohled.search([
        ("key", "=like", ZBYTKY + "%"),
        ("active", "=", True),
    ])

    vypnuto = 0
    for dedic in zbytky:
        rodic = dedic.inherit_id
        if not rodic or not _nas(rodic):
            # Dedic visi na cizim pohledu, do toho nam nic neni.
            continue

        rodicovsky_strom = _strom(rodic)
        dedicuv_strom = _strom(dedic)
        if rodicovsky_strom is None or dedicuv_strom is None:
            continue

        vyrazy = [uzel.get("expr")
                  for uzel in dedicuv_strom.iter("xpath")
                  if uzel.get("expr")]
        if not vyrazy:
            continue

        mrtve = []
        for vyraz in vyrazy:
            try:
                if not rodicovsky_strom.xpath(vyraz):
                    mrtve.append(vyraz)
            except etree.XPathEvalError:
                mrtve.append(vyraz)

        if len(mrtve) != len(vyrazy):
            # Aspon neco jeste sedi, radeji necháme byt.
            continue

        dedic.active = False
        vypnuto += 1
        _logger.warning(
            "Vypnut zbytek stareho webu '%s' (id %s): zadny z jeho xpath "
            "uz v pohledu '%s' nic nenajde (%s).",
            dedic.key, dedic.id, rodic.key, mrtve[0])

    _logger.info("Zbytku s mrtvym xpath vypnuto: %s", vypnuto)


# ---------------------------------------------------------------------------
# 2. dva pohledy stejneho klice na stejnem webu
# ---------------------------------------------------------------------------
def _smaz_dvojniky_pohledu(env):
    Pohled = env["ir.ui.view"]
    vsechny = Pohled.with_context(active_test=False).search([
        ("key", "=like", PREDPONA + "%"),
    ])

    # Seskupuje se podle klice A webu. Modulovy pohled bez webu vedle vlastni
    # kopie webu je uplne v poradku -- tak si Odoo drzi upravy z editoru.
    # Chyba je az tehdy, kdyz stejnou dvojici (klic, web) maji dva pohledy.
    podle_klice = {}
    for pohled in vsechny:
        klic = (pohled.key, pohled.website_id.id)
        podle_klice[klic] = podle_klice.get(klic, Pohled) + pohled

    smazano = 0
    for (klic, _web), skupina in podle_klice.items():
        if len(skupina) < 2:
            continue

        s_id = env["ir.model.data"].search([
            ("model", "=", "ir.ui.view"),
            ("res_id", "in", skupina.ids),
        ]).mapped("res_id")
        se_strankou = env["website.page"].search(
            [("view_id", "in", skupina.ids)]).mapped("view_id").ids

        # Jeden pohled musi zustat vzdy: nejradeji ten modulovy (ma externi
        # ID), jinak ten, na kterem visi stranka, jinak naposled upraveny.
        zustava = (
            skupina.filtered(lambda v: v.id in s_id)[:1]
            or skupina.filtered(lambda v: v.id in se_strankou)[:1]
            or skupina.sorted("write_date", reverse=True)[:1]
        )

        for pohled in skupina - zustava:
            # Sirotek smi pryc jen kdyz na nem nevisi stranka ani dedic.
            ma_dedice = Pohled.with_context(active_test=False).search_count(
                [("inherit_id", "=", pohled.id)])
            if pohled.id in se_strankou or ma_dedice:
                _logger.warning(
                    "Dvojnik pohledu '%s' (id %s) zustava: visi na nem "
                    "stranka nebo dedic.", klic, pohled.id)
                continue
            _logger.warning(
                "Mazu dvojnika pohledu '%s' (id %s), ponechavam %s.",
                klic, pohled.id, zustava.id)
            pohled.unlink()
            smazano += 1

    _logger.info("Dvojniku pohledu smazano: %s", smazano)
