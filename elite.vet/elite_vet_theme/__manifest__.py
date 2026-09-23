# -*- coding: utf-8 -*-
{
    "name": "Elite Vet - vzhled webu",
    "version": "18.0.1.0.0",
    "summary": "Spolecna hlavicka a paticka webu kliniky",
    # Hlavicka a paticka byly drive v sesti kopiich, na kazde strance jedna.
    # Zmena menu se tak musela delat sestkrat a pokazde se na neco zapomnelo.
    # Tenhle modul je drzi na jednom miste; vsechny ostatni moduly kliniky
    # na nem stoji, proto nesmi zaviset na zadnem z nich.
    #
    # Zamerne to NENI modul s prefixem theme_: takovy modul si Odoo nacita
    # vlastni cestou (website.theme_id, _theme_load) a na produkci uz jeden
    # theme_elite_vet existuje.
    "category": "Website",
    "license": "LGPL-3",
    "author": "Michal Varys",
    "depends": ["website"],
    "data": [
        "views/layout.xml",
        "views/bloky.xml",
        "views/snippets.xml",
    ],
    # Styl bloku se nacita na vsech strankach. Inline <style> uvnitr
    # domovske stranky by se na blok pretazeny jinam nevztahoval.
    "assets": {
        "web.assets_frontend": [
            "elite_vet_theme/static/src/css/bloky.css",
        ],
    },
    "installable": True,
    "application": False,
}
