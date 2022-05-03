# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Export Axesor360 Files',
    'version': '12.0.1.2.0',
    'license': 'AGPL-3',
    'author': "Domatix",
    'website': 'https://domatix.com/',
    'category': 'Integrations',
    'depends': [
        'account',
    ],
    'data': [
        'views/res_config_settings_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
}
