import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EliteVetAbout(models.Model):
    """Obsah stranky /o-nas.

    Zamerne je to jediny zaznam, ne seznam sekci jako u ceniku — stranka je
    jeden text o klinice. Nabidka proto vede rovnou do formulare a klinika
    nemusi nic vybirat ze seznamu.
    """

    _name = "elite.vet.about"
    _description = "Elite Vet - stránka O nás"

    badge = fields.Char(
        "Štítek", translate=True,
        help="Malý nápis v rámečku nad nadpisem, například „O KLINICE“. "
             "Nechat prázdné je v pořádku.")
    name = fields.Char("Nadpis", required=True, translate=True,
                       default="O nás")
    body = fields.Html(
        "Text", translate=True, sanitize=False,
        help="Odstavce pod nadpisem. Může být tučné, odrážky i odkaz.")
    image = fields.Image(
        "Obrázek", max_width=1600, max_height=1200,
        help="Nepovinná fotka pod textem. Bez ní se nic nevykreslí.")
    image_alt = fields.Char(
        "Popis obrázku", translate=True,
        help="Co je na fotce. Čte to Google a hlasové čtečky.")

    # Odkaz se zadava tak, jak ho clovek zkopiruje z YouTube — at uz je to
    # youtu.be/..., watch?v=... nebo /embed/... Prehravac se sklada az v sablone.
    video_url = fields.Char(
        "Odkaz na video (YouTube)",
        help="Zkopíruj adresu z YouTube. Funguje youtu.be/… i youtube.com/watch?v=…")
    video_id = fields.Char("Kód videa", compute="_compute_video_id", store=True,
                           help="Vytažený kód z odkazu. Nevyplňuje se ručně.")

    # youtu.be/KOD | watch?v=KOD | embed/KOD | shorts/KOD
    VZORY = (
        r"youtu\.be/([A-Za-z0-9_-]{6,})",
        r"[?&]v=([A-Za-z0-9_-]{6,})",
        r"/embed/([A-Za-z0-9_-]{6,})",
        r"/shorts/([A-Za-z0-9_-]{6,})",
    )

    @api.depends("video_url")
    def _compute_video_id(self):
        for zaznam in self:
            adresa = (zaznam.video_url or "").strip()
            kod = False
            for vzor in self.VZORY:
                nalez = re.search(vzor, adresa)
                if nalez:
                    kod = nalez.group(1)
                    break
            # Kdyz nekdo vlozi rovnou samotny kod, bereme ho taky.
            if not kod and adresa and re.fullmatch(r"[A-Za-z0-9_-]{6,}", adresa):
                kod = adresa
            zaznam.video_id = kod

    @api.constrains("video_url")
    def _zkontroluj_video(self):
        """Radsi to rekneme hned, nez aby na strance zustalo prazdne misto."""
        for zaznam in self:
            if zaznam.video_url and not zaznam.video_id:
                raise ValidationError(
                    "Z odkazu %s se nepodařilo vytáhnout kód videa. "
                    "Zkopíruj adresu přímo z YouTube — například "
                    "https://www.youtube.com/watch?v=xxxxxxxxxxx nebo "
                    "https://youtu.be/xxxxxxxxxxx." % zaznam.video_url)

    @api.model
    def stranka(self):
        """Vrati jediny zaznam; kdyz zadny neni, zalozi ho."""
        zaznam = self.sudo().search([], limit=1)
        if not zaznam:
            zaznam = self.sudo().create({})
        return zaznam

    @api.model
    def otevrit(self):
        """Nabidka vede rovnou do formulare, ne do seznamu o jednom radku."""
        return {
            "type": "ir.actions.act_window",
            "name": "O nás",
            "res_model": "elite.vet.about",
            "res_id": self.stranka().id,
            "view_mode": "form",
            "target": "current",
        }
