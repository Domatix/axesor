from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    axesor_server = fields.Char(
        string='Server'
    )

    axesor_username = fields.Char(
        string='Username'
    )

    axesor_password = fields.Char(
        string='Password'
    )

    axesor_port = fields.Integer(
        string='Port'
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()

        IrDefault = self.env["ir.default"].sudo()

        IrDefault.set("res.config.settings", "axesor_server", self.axesor_server)
        IrDefault.set("res.config.settings", "axesor_port", self.axesor_port)
        IrDefault.set("res.config.settings", "axesor_username", self.axesor_username)
        IrDefault.set("res.config.settings", "axesor_password", self.axesor_password)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env["ir.default"].sudo()
        res.update(
            {
                "axesor_server": IrDefault.get("res.config.settings", "axesor_server"),
                "axesor_port": IrDefault.get("res.config.settings", "axesor_port"),
                "axesor_username": IrDefault.get("res.config.settings", "axesor_username"),
                "axesor_password": IrDefault.get("res.config.settings", "axesor_password")
            }
        )
        return res
