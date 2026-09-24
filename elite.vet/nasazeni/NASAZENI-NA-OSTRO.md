# Nasazení Elite Vet na ostrý web

Postup na jedno spuštění. Všechno, co se dřív muselo doklikat ručně, dělá modul sám.

Ověřeno 24. 9. 2026 na databázi postavené tak, aby se podobala ostrému webu:
ruční stránky na všech adresách, zbylé dědící pohledy `gen_key.*` po starém
přepínači jazyků, položka nabídky mířící na kotvu odpočtu. Do toho se moduly
nainstalovaly a web naběhl správně.

## 1. Stáhnout

```bash
cd <klon repa goatrental/modules> && git pull
```

Moduly leží ve složce `elite.vet/`. Zkopírovat do addons tak, aby `__manifest__.py`
byl **přesně jednu úroveň** pod cestou v `addons-path`.

## 2. Spustit

Podle toho, jestli už moduly na webu jsou:

```bash
# poprvé
odoo -d <db> -i elite_vet_web --stop-after-init

# už nainstalované
odoo -d <db> -u elite_vet_theme,elite_vet_team,elite_vet_calendar,elite_vet_web --stop-after-init
```

Pak restart kontejneru.

Instalovat stačí `elite_vet_web` — zbylé tři si Odoo přitáhne samo.

## 3. Co má být v logu

```
Ceník: zalozeno 3 bloku.
Do nabidky pribyl Kontakt (id ...).
Na '/' je N stranek a Odoo si mezi nimi vybira nahodne, takze vsechny dostaly sablonu modulu
Starsi stranky na adresach projektu odsunuty: /o-nas -> /o-nas-puvodni, ...
Zbytku s mrtvym xpath vypnuto: N
Dvojniku pohledu smazano: N
```

Řádky se `0` jsou v pořádku — znamenají, že nebylo co uklízet.

## 4. Ověřit

```bash
for p in / /o-nas /cenik /nas-tym /rozpis-lekaru /rezervacni-system; do
  printf '%-22s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' https://www.elite-vet.cz$p)"
done
```

Všechno má vrátit `200`. Na domovské stránce má být mapa v kontaktech a v nabídce
položka **Kontakt**, která sjede ke kontaktní sekci.

## 5. Co musí být na webu nastavené předem

Moduly **nenastavují jazyky webu**. Musí být v Nastavení → Weby → *Jazyky*
přiřazené `cs_CZ`, `de_DE`, `en_US`, `ru_RU` a výchozí jazyk `cs_CZ`.

Na ostrém webu už to nastavené je (běží na něm `/de`, `/en`, `/ru`), takže tam
netřeba nic dělat. Kdyby ale jazyk webu přiřazený nebyl, moduly se nainstalují
bez chyby a čeština bude fungovat, jen `/de` a `/ru` budou vracet **404** —
vypadá to jako rozbité nasazení, ale je to jen tohle nastavení. Ověřeno při
generálce, kde jazyky byly nainstalované, ale webu nepřiřazené.

## 6. Čeho se nasazení nedotkne

`/aktualni-informace`, `/kariera-pro-lekare` a `/kariera-pro-absolventy` moduly
nedodávají, takže zůstanou přesně takové, jaké jsou.

## Co modul udělá se starými stránkami

Na adresách `/o-nas`, `/cenik`, `/rezervacni-system`, `/nas-tym` a `/rozpis-lekaru`
už na ostrém webu stránka je. Modul si vedle ní založí svoji, takže by na jedné
adrese byly dvě — a Odoo si mezi nimi vybírá **nahodile**:

```python
search(domain, order='website_id asc', limit=1)
```

Mezi stránkami téhož webu už žádné další řazení není. Jednou se proto ukáže nový
web, podruhé starý, a když padne na nezveřejněnou, vrátí 404.

Stará stránka se proto **přejmenuje na `<adresa>-puvodni` a odpublikuje**. Nic se
nemaže: obsah je pořád v databázi a dá se otevřít po zaškrtnutí *Zveřejněno*
v Nastavení → Technické → Web → Stránky.

Domovská stránka se přejmenovat nedá, tam to modul řeší opačně — všechny záznamy
na `/` dostanou šablonu modulu, takže je jedno, který si Odoo vybere.

## Když „Aktualizovat téma" hodí chybu

```
duplicate key value violates unique constraint "ir_config_parameter_key_uniq"
DETAIL:  Key (key)=(<nazev.parametru>) already exists
```

Ten parametr v databázi je, ale vznikl za běhu, takže mu chybí záznam, podle
kterého ho Odoo pozná jako svůj — a tak ho zkusí založit znovu. Blokuje to
aktualizaci tématu komukoliv v té databázi. Klíč je vždy vypsaný za `Key (key)=`.
Doplní se chybějící záznam, `noupdate` zajistí, že aktualizace nepřepíše
současnou hodnotu:

```sql
INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
SELECT '<modul>', '<nazev_zaznamu>', 'ir.config_parameter', id, true
FROM ir_config_parameter WHERE key = '<nazev.parametru>';
```

`<modul>` a `<nazev_zaznamu>` jsou na konci hlášky v cestě k souboru
(`.../<modul>/data/ir_config_parameter.xml`) a v `<record id="...">`.

## Když se něco nepovede

Nic se nemaže, takže zpátky vede:

1. staré stránky se vrátí přejmenováním z `<adresa>-puvodni` zpět a zaškrtnutím
   *Zveřejněno*,
2. moduly se dají odinstalovat v Aplikacích.

Zálohu databáze si přesto udělej předem.
