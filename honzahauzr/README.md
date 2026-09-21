# Honza Hauzr

Osobni web honzahauzr.cz - osobni rozvoj, koucink a mentoring.
Jedna landing page, ktera ma navstevnika dovest k rezervaci uvodniho hovoru.

## Moduly

| Modul | Co dela |
|---|---|
| `theme_honzahauzr` | Tema a obsah webu: landing page, WIP stranka, styly, snippety |

Zavisi na `website` a `website_crm`. Zadne dalsi moduly projekt nema.

## Struktura stranky

Poradi sekci je dane zadanim klienta:

1. Navigace - O mne, Jak pracuji, Domluvit uvodni hovor
2. Uvodni obrazovka - komu pomaham a s cim
3. Problemy - autopilot, respekt k sobe, hranice, smer
4. Muj pribeh - kontrast DRIV / DNES plus galerie cesty
5. Jak pracuji - pristup, odpovednost, konkretni kroky
6. Uvodni hovor - pozvani a rezervacni formular
7. PDF zdarma - mene vyrazna alternativa pro ty, kdo zatim nechteji mluvit
8. Paticka - kontakt a socialni site

## Na co si dat pozor

**Formulare musi mit obal `s_website_form_field`.** Odoo validuje jen
policka uvnitr nej. Bez obalu projde i uplne prazdny formular a v CRM
pristane lead bez e-mailu.

**Rolovani na kotvy resi vlastni animace v `honzahauzr.js`.** Odoo ma na
`a[href^="#"]` vlastni JS navesny na `#wrapwrap`. Kdyz se k tomu prida
jeste CSS `scroll-behavior: smooth`, oba mechanismy se peraji a rolovani
nedojede k cili. Proto se klik bere uz v capture fazi.

**Fotky v heru a v sekci uvodniho hovoru jsou na pozadi sekce**
(`oe_img_bg`), aby sly vymenit v editoru pres volbu Pozadi. Jako `<img>`
by lezely pod textem a neslo by na ne kliknout.

**Po zmene `pages.xml` nestaci upgrade modulu.** Tema kopiruje
`theme.website.page` do `website.page` jen pri prvni aplikaci. Kopie se
musi smazat a nechat vyrobit znovu - viz DOCKER.md v korenu repa.

**Trida `form-control` je nutna kvuli validaci**, ale Bootstrap na ni pri
zaostreni nasadi bile pozadi. Je prebita v `honzahauzr.scss`.

## Kontakty na webu

Prevzate z WIP stranky, nic vymysleneho:
honzahauzr@gmail.com, Instagram, Facebook, YouTube, TikTok.
LinkedIn Honza nema.

## Co zbyva doresit

- PDF pro sekci "PDF zdarma" - formular e-maily sbira, soubor chybi
- Pravni stranky (ochrana osobnich udaju, obchodni podminky) neexistuji,
  proto v paticce nejsou
- Snippety `s_hh_offer`, `s_hh_process`, `s_hh_testimonials` a
  `s_hh_vision_strip` zustavaji v manifestu, ale zadani je ze stranky
  vyradilo a jejich styly jsou smazane. Kdyz je nekdo pretahne v editoru,
  vysypou se neostylovane.
