from odoo import fields, models
import csv
from datetime import datetime
from dateutil.relativedelta import relativedelta
import paramiko
import os.path

ROOT_PATH = "/opt/odoo/data/axesor/"


def open_file(directory):
    f = open(directory, 'w+')
    writer = csv.writer(f, delimiter=';', quotechar='"', dialect='excel', quoting=csv.QUOTE_MINIMAL)
    return writer, f


def get_directory(name):
    if not os.path.exists('/opt/odoo/data/axesor'):
        os.makedirs('/opt/odoo/data/axesor')
    return "{}{}.csv".format(ROOT_PATH, name)


class ExportAxesor(models.Model):
    _name = "export.axesor"
    _description = "Cron to export Axesor360 files"

    # Obligatorio
    def export_sociedades(self, ftp, sociedades):
        directory = get_directory("sociedades")
        writer, f = open_file(directory)

        header = ['cod', 'razons', 'nif', 'codmoneda']
        writer.writerow(header)

        # Content
        for sociedad in sociedades:
            row = []
            row.append(str(sociedad.id))
            row.append(sociedad.street)
            row.append(sociedad.vat)
            row.append(str(sociedad.currency_id.id))
            writer.writerow(row)
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('sociedades'), ftp.getcwd() + '/sociedades.csv')
        ftp.chdir('/')
        ftp.put(get_directory('sociedades'), ftp.getcwd() + 'sociedades.csv')

    # Obligatorio
    def export_clasifcriterios(self, ftp, path):
        directory = get_directory("clasifcriterios")
        writer, f = open_file(directory)

        header = ['id', 'cod', 'desc']
        writer.writerow(header)
        # Content
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('clasifcriterios'), ftp.getcwd() + '/clasifcriterios.csv')

        ftp.chdir(path)
        ftp.put(get_directory('clasifcriterios'), ftp.getcwd() + '/clasifcriterios.csv')

    # Obligatorio
    def export_viaspago(self, ftp, sociedad, path):
        payment_mode_ids = self.env['account.payment.mode'].search([])

        directory = get_directory("viaspago")
        writer, f = open_file(directory)

        header = ['cod', 'desc', 'gencart', 'ind1', 'ind2', 'numdias']
        writer.writerow(header)

        # Content
        for payment_mode_id in payment_mode_ids:
            row = []
            row.append(str(payment_mode_id.id))  # cod
            row.append(payment_mode_id.name)  # desc
            row.append("")  # gencart
            row.append("")  # ind1
            row.append("")  # ind2
            row.append("")  # numdias
            writer.writerow(row)
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('viaspago'), ftp.getcwd() + '/viaspago.csv')

        ftp.chdir(path)
        ftp.put(get_directory('viaspago'), ftp.getcwd() + '/viaspago.csv')

    # Obligatorio
    def export_cndpago(self, ftp, sociedad, path):
        payment_term_ids = self.env['account.payment.term'].search([])

        directory = get_directory("cndpago")
        writer, f = open_file(directory)

        header = ['cod', 'desc', 'dscPlazo', 'dias', 'porc', 'codvia', 'codp']
        writer.writerow(header)

        # Content
        for payment_term_id in payment_term_ids:
            for line in payment_term_id.line_ids:
                row = []
                row.append(str(payment_term_id.id))  # cod
                row.append(payment_term_id.name)  # desc
                row.append(' '.join(payment_term_id.note.splitlines()))  # dscPlazo
                row.append(line.days + line.weeks * 7 + line.months * 30)  # dias
                if line.value == 'balance':
                    porc = 100.0
                elif line.value == 'percent':
                    porc = line.value_amount
                else:
                    porc = 0.0
                row.append(porc)  # porc
                row.append("")  # codvia
                row.append("")  # codp
                writer.writerow(row)
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('cndpago'), ftp.getcwd() + '/cndpago.csv')

        ftp.chdir(path)
        ftp.put(get_directory('cndpago'), ftp.getcwd() + '/cndpago.csv')

    # Obligatorio
    def export_clientes(self, ftp, sociedad, path):
        last_file = False
        last_file_lines = False
        if os.path.exists(get_directory('clientes')):
            last_file = open(get_directory("clientes"), 'r')
            last_file_lines = last_file.readlines()

        partner_ids = self.env['res.partner'].search([('customer', '=', True)])

        directory = get_directory("clientes")
        writer, f = open_file(directory)

        header = ['cod', 'nif', 'razons', 'codcondp', 'limitrg', 'prov', 'dims', 'lrcomp', 'viasp',
                  'clasifcontable', 'lsegcredito', 'fchcadsegcred',
                  'tipoentidad', 'sector', 'fchaltaerp', 'fchinitact', 'ind1', 'ind2', 'ind3', 'ind4', 'ind5',
                  'ind6', 'ind7', 'ind8', 'ind9']
        writer.writerow(header)

        # Content
        for partner_id in partner_ids:
            if partner_id.vat != False:
                row = []
                row.append(str(partner_id.id))  # cod
                row.append(partner_id.vat)  # nif
                row.append(partner_id.name)  # razons
                row.append(str(partner_id.property_payment_term_id.id))  # codcondp
                row.append(partner_id.credit_limit)  # limitrg
                row.append(partner_id.state_id.name)  # prov
                row.append("")  # dims
                row.append(1)  # lrcomp
                row.append(str(partner_id.customer_payment_mode_id.id))  # viasp
                if partner_id.country_id.code == 'ES':  # clasifcontable
                    row.append('nacional')
                else:
                    row.append('extranjero')
                row.append("")  # lsegcredito
                row.append("")  # fchcadsegcred
                if partner_id.company_type == 'company':  # tipoentidad
                    row.append("Compañía")
                else:
                    row.append("Individual")
                row.append("")  # sector
                row.append(partner_id.create_date.strftime("%Y-%m-%d"))  # fchaltaerp
                row.append("")  # fchinitact
                if partner_id.country_id:
                    row.append(partner_id.country_id.name)  # ind1 (país)
                else:
                    row.append("")  # ind1 (país)
                if partner_id.credit_limit:
                    row.append(partner_id.credit_limit)  # ind2 (cobertura)
                else:
                    row.append("")  # ind2 (cobertura)
                row.append("")  # ind3
                row.append("")  # ind4
                row.append("")  # ind5
                row.append("")  # ind6
                row.append("")  # ind7
                row.append("")  # ind8
                row.append("")  # ind9
                writer.writerow(row)
        f.close()

        current_file = open(get_directory("clientes"), 'r')
        current_file_lines = current_file.readlines()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('clientes'), ftp.getcwd() + '/clientes.csv')

        ftp.chdir(path)
        if not last_file:
            ftp.put(get_directory('clientes'), ftp.getcwd() + '/clientes.csv')
        else:
            remote_file = ftp.open('clientes.csv', 'w+')
            writer = csv.writer(remote_file, delimiter=';', quotechar='"', dialect='excel', quoting=csv.QUOTE_MINIMAL)

            header = ['cod', 'nif', 'razons', 'codcondp', 'limitrg', 'prov', 'dims', 'lrcomp', 'viasp',
                      'clasifcontable', 'lsegcredito', 'fchcadsegcred',
                      'tipoentidad', 'sector', 'fchaltaerp', 'fchinitact', 'ind1', 'ind2', 'ind3', 'ind4', 'ind5',
                      'ind6', 'ind7', 'ind8', 'ind9']
            writer.writerow(header)

            last_file_ids = []
            for last_file_line in last_file_lines:
                lfl = last_file_line.split(';')
                last_file_ids.append((lfl[0]))

            for last_file_line in last_file_lines:
                lfl = last_file_line.split(';')
                for current_file_line in current_file_lines:
                    cfl = current_file_line.split(';')
                    if cfl[0] not in last_file_ids:
                        row = cfl[:-1]
                        writer.writerow(row)
                        last_file_ids.append(cfl[0])
                    elif lfl[0] == cfl[0] and hash(tuple(lfl)) != hash(tuple(cfl)):
                        row = cfl[:-1]
                        writer.writerow(row)
            remote_file.close()
            last_file.close()
            current_file.close()

    # Obligatorio
    def export_direcciones(self, ftp, sociedad, path):
        partner_ids = self.env['res.partner'].search([('parent_id', '!=', False)])

        directory = get_directory("direcciones")
        writer, f = open_file(directory)

        header = ['codcliente', 'coddireccion', 'tdireccion', 'domicilio', 'ciudad', 'prov', 'cp', 'pais', 'ind1',
                  'ind2', 'ind3']
        writer.writerow(header)

        # Content
        for dir in partner_ids:
            row = []
            row.append(dir.id)
            row.append(dir.type)
            if dir.type == 'contact':  # tdireccion
                row.append(2)
            elif dir.type == 'invoice':
                row.append(0)
            elif dir.type == 'delivery':
                row.append(1)
            elif dir.type == 'other':
                row.append(4)
            else:
                row.append(3)
            row.append(dir.street)  # domicilio
            row.append(dir.city)  # ciudad
            row.append(dir.country_id.name)  # prov
            row.append(dir.zip)  # cp
            row.append(dir.country_id.name)  # pais
            row.append("")  # ind1
            row.append("")  # ind2
            row.append("")  # ind3
            writer.writerow(row)
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('direcciones'), ftp.getcwd() + '/direcciones.csv')

        ftp.chdir(path)
        ftp.put(get_directory('direcciones'), ftp.getcwd() + '/direcciones.csv')

    # Obligatorio
    def export_contactos(self, ftp, sociedad, path):
        partner_ids = self.env['res.partner'].search([('parent_id', '!=', False), ('type', '=', 'contact')])

        directory = get_directory("contactos")
        writer, f = open_file(directory)

        header = ['codcliente', 'codcontacto', 'nombre', 'nif', 'tcontacto', 'coddireccion', 'tlffijo', 'tlfmovil',
                  'fax', 'email', 'ind1', 'ind2', 'ind3']
        writer.writerow(header)

        # Content
        for contact in partner_ids:
            row = []
            row.append(str(contact.parent_id.id))  # codcliente
            row.append(str(contact.id))  # codcontacto
            row.append(contact.name)  # nombre
            row.append(contact.vat)  # nif
            row.append(0)  # tcontacto
            row.append(str(contact.id))  # coddireccion
            row.append(contact.phone)  # tlffijo
            row.append(contact.mobile)  # tlfmovil
            row.append("")  # fax
            row.append(contact.email)  # email
            row.append("")  # ind1
            row.append("")  # ind2
            row.append("")  # ind3
            writer.writerow(row)
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('contactos'), ftp.getcwd() + '/contactos.csv')

        ftp.chdir(path)
        ftp.put(get_directory('contactos'), ftp.getcwd() + '/contactos.csv')

    # Obligatorio
    def export_partabiertas(self, ftp, sociedad, path):
        partner_ids = self.env['res.partner'].search([('customer', '=', True)])
        account_move_line_ids = self.env['account.move.line'].search(
            [('partner_id.id', 'in', partner_ids.ids), ('account_id.internal_type', '=', 'receivable'),
             ('amount_residual', '!=', 0)])

        directory = get_directory("partabiertas")
        writer, f = open_file(directory)

        header = ['codcli', 'ndoc', 'nvcto', 'fchemi', 'fchvcto', 'importe', 'estado', 'dotada', 'codvp',
                  'codcondp', 'codmondoc', 'impmondoc', 'ind1', 'ind2', 'ind3', 'ind4', 'ind5', 'ind6', 'ind7',
                  'ind8', 'ind9',
                  'tdoc', 'campoid', 'codejercicio', 'numdocorigen']
        writer.writerow(header)

        # Content
        for partner_id in partner_ids:
            account_move_lines = account_move_line_ids.filtered(lambda x: x.partner_id.id == partner_id.id)
            for account_move_line in account_move_lines:
                row = []
                row.append(str(partner_id.id))  # codcli
                if account_move_line.invoice_id and account_move_line.invoice_id.type in ['out_invoice', 'out_refund']:
                    row.append(account_move_line.invoice_id.number)  # ndoc
                elif account_move_line.document and account_move_line.move_id.payment_document_id:
                    row.append(account_move_line.move_id.payment_document_id.name)  # ndoc
                elif account_move_line.order_id and account_move_line.move_id.payment_order_id:
                    row.append(account_move_line.move_id.payment_order_id.name)  # ndoc
                elif account_move_line.document_line_id and account_move_line.document_line_id.document_id:
                    row.append(account_move_line.document_line_id.document_id.name)  # ndoc
                elif account_move_line.bank_payment_line_id:
                    row.append(account_move_line.bank_payment_line_id.name)  # ndoc
                elif account_move_line.ref:
                    row.append(account_move_line.ref)  # ndoc
                else:
                    continue
                row.append("")  # nvcto
                row.append(account_move_line.date)  # fchemi
                row.append(account_move_line.date_maturity)  # fchvcto
                row.append(account_move_line.amount_residual)  # importe
                row.append("")  # estado
                row.append("")  # dotada
                row.append("")  # codvp
                row.append("")  # codcondp
                row.append("")  # codmondoc
                row.append("")  # impmondoc
                row2 = []
                if account_move_line.invoice_id and account_move_line.invoice_id.type in ['out_invoice',
                                                                                          'out_refund'] and not account_move_line.document_line_ids and not account_move_line.payment_line_ids:
                    row.append("")  # ind1
                elif account_move_line.document_line_ids:
                    for document_id in account_move_line.document_line_ids.mapped("document_id"):
                        if document_id.payment_order_id:
                            row2.append(document_id.payment_order_id.name)  # ind1
                        else:
                            row2.append(document_id.name)  # ind1
                    row.append(str(row2).replace("[", "").replace("]", "").replace("'", ""))
                elif account_move_line.payment_line_ids:
                    row.append(
                        str(account_move_line.payment_line_ids.mapped("order_id.name")).replace("[", "").replace("]",
                                                                                                                 "").replace(
                            "'", ""))  # ind1
                elif account_move_line.document_line_id:
                    if account_move_line.document_line_id.document_id.payment_order_id:
                        row.append(account_move_line.document_line_id.document_id.payment_order_id.name)  # ind1
                    else:
                        row.append(account_move_line.document_line_id.document_id.name)  # ind1
                elif account_move_line.document:
                    if account_move_line.move_id.payment_document_id.payment_order_id:
                        row.append(account_move_line.move_id.payment_document_id.payment_order_id.name)  # ind1
                    else:
                        row.append(account_move_line.move_id.payment_document_id.name)  # ind1
                elif account_move_line.bank_payment_line_id:
                    if account_move_line.bank_payment_line_id.order_id:
                        row.append(account_move_line.bank_payment_line_id.order_id.name)  # ind1
                    else:
                        row.append(account_move_line.bank_payment_line_id.name)  # ind1
                elif account_move_line.order_id:
                    row.append(account_move_line.move_id.payment_order_id.name)  # ind1
                else:
                    row.append("")  # ind1
                row.append("")  # ind2
                row.append("")  # ind3
                row.append("")  # ind4
                row.append("")  # ind5
                row.append("")  # ind6
                row.append("")  # ind7
                row.append("")  # ind8
                row.append("")  # ind9
                if account_move_line.invoice_id and account_move_line.invoice_id.type == 'out_invoice':
                    row.append("Factura")  # tdoc
                elif account_move_line.invoice_id and account_move_line.invoice_id.type == 'out_refund':
                    row.append("Abono")  # tdoc
                elif account_move_line.document or account_move_line.order_id or account_move_line.document_line_id or account_move_line.bank_payment_line_id:
                    row.append("Efecto")  # tdoc
                else:
                    row.append("Otro")  # tdoc
                row.append(str(account_move_line.id))  # campoid
                row.append("")  # codejercicio
                row.append("")  # numdocorigen
                writer.writerow(row)
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('partabiertas'), ftp.getcwd() + '/partabiertas.csv')

        ftp.chdir(path)
        ftp.put(get_directory('partabiertas'), ftp.getcwd() + '/partabiertas.csv')

    # Obligatorio
    def export_partcomps(self, ftp, sociedad, path):
        last_file = False
        last_file_lines = False
        if os.path.exists(get_directory('partcomps')):
            last_file = open(get_directory("partcomps"), 'r')
            last_file_lines = last_file.readlines()

        partner_ids = self.env['res.partner'].search([('customer', '=', True)])
        account_move_line_ids = self.env['account.move.line'].search(
            [('partner_id.id', 'in', partner_ids.ids), ('account_id.internal_type', '=', 'receivable'),
             ('amount_residual', '=', 0), ('reconciled', '=', True), ('full_reconcile_id', '!=', False),
             ('create_date', '>=', datetime.today() + relativedelta(years=-3)), '|',
             ('matched_debit_ids.origin_returned_move_ids', '=', False),
             ('matched_credit_ids.origin_returned_move_ids', '=', False)])

        directory = get_directory("partcomps")
        writer, f = open_file(directory)

        header = ['codcli', 'ndoc', 'nvcto', 'fchemi', 'fchvcto', 'fchcomp', 'importe', 'marca', 'impmondoc',
                  'codmondoc', 'ind1',
                  'ind2', 'ind3', 'ind4', 'ind5', 'ind6', 'ind7', 'ind8', 'ind9', 'tdoc', 'campoid', 'codejercicio',
                  'codejerciciocomp', 'numdoccobro', 'numdocorigen']
        writer.writerow(header)

        # Content
        for partner_id in partner_ids:
            account_move_lines = account_move_line_ids.filtered(lambda x: x.partner_id.id == partner_id.id)
            for account_move_line in account_move_lines:
                row = []
                row.append(str(partner_id.id))  # codcli
                if account_move_line.invoice_id and account_move_line.invoice_id.type in ['out_invoice', 'out_refund']:
                    row.append(account_move_line.invoice_id.number)  # ndoc
                elif account_move_line.document:
                    row.append(account_move_line.move_id.payment_document_id.name)  # ndoc
                elif account_move_line.order_id:
                    row.append(account_move_line.move_id.payment_order_id.name)  # ndoc
                elif account_move_line.document_line_id:
                    row.append(account_move_line.document_line_id.document_id.name)  # ndoc
                elif account_move_line.bank_payment_line_id:
                    row.append(account_move_line.bank_payment_line_id.name)  # ndoc
                else:
                    row.append(account_move_line.ref)  # ndoc
                row.append("")  # nvcto
                row.append(account_move_line.date)  # fchemi
                row.append(account_move_line.date_maturity)  # fchvcto
                ids = []
                ids.extend([r.debit_move_id.id for r in
                            account_move_line.matched_debit_ids] if account_move_line.credit > 0 else [
                    r.credit_move_id.id for r in account_move_line.matched_credit_ids])
                aml = self.env['account.move.line'].browse(ids)
                row.append(max(aml.mapped('date_maturity')))  # fchcomp
                row.append(account_move_line.balance)  # importe
                row.append("")  # marca
                row.append("")  # impmondoc
                row.append("")  # codmondoc
                row.append("")  # ind1
                row.append("")  # ind2
                row.append("")  # ind3
                row.append("")  # ind4
                row.append("")  # ind5
                row.append("")  # ind6
                row.append("")  # ind7
                row.append("")  # ind8
                row.append("")  # ind9
                if account_move_line.invoice_id and account_move_line.invoice_id.type == 'out_invoice':
                    row.append("Factura")  # tdoc
                elif account_move_line.invoice_id and account_move_line.invoice_id.type == 'out_refund':
                    row.append("Abono")  # tdoc
                elif account_move_line.document or account_move_line.order_id or account_move_line.document_line_id or account_move_line.bank_payment_line_id or (
                        account_move_line.full_reconcile_id.reconciled_line_ids.filtered(
                            lambda x: x.order_id and x.id != account_move_line.id and x.full_reconcile_id.id == account_move_line.full_reconcile_id.id)):
                    row.append("Efecto")  # tdoc
                else:
                    row.append("Otro")  # tdoc
                row.append(str(account_move_line.id))  # campoid
                row.append("")  # codejercicio
                row.append("")  # codejerciciocomp
                row.append("")  # numdoccobro
                row.append("")  # numdocorigen
                writer.writerow(row)
        f.close()

        current_file = open(get_directory("partcomps"), 'r')
        current_file_lines = current_file.readlines()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('partcomps'), ftp.getcwd() + '/partcomps.csv')

        ftp.chdir(path)
        if not last_file:
            ftp.put(get_directory('partcomps'), ftp.getcwd() + '/partcomps.csv')
        else:
            remote_file = ftp.open('partcomps.csv', 'w+')
            writer = csv.writer(remote_file, delimiter=';', quotechar='"', dialect='excel', quoting=csv.QUOTE_MINIMAL)

            header = ['codcli', 'ndoc', 'nvcto', 'fchemi', 'fchvcto', 'fchcomp', 'importe', 'marca', 'impmondoc',
                      'codmondoc', 'ind1',
                      'ind2', 'ind3', 'ind4', 'ind5', 'ind6', 'ind7', 'ind8', 'ind9', 'tdoc', 'campoid', 'codejercicio',
                      'codejerciciocomp', 'numdoccobro', 'numdocorigen']
            writer.writerow(header)

            for current_file_line in current_file_lines:
                if current_file_line not in last_file_lines:
                    cfl = current_file_line.split(';')
                    row = cfl[:-1]
                    writer.writerow(row)
            remote_file.close()
            last_file.close()
            current_file.close()

    # Obligatorio
    def export_partcompsinv(self, ftp, sociedad, path):
        last_file = False
        last_file_lines = False
        if os.path.exists(get_directory('partcompsinv')):
            last_file = open(get_directory("partcompsinv"), 'r')
            last_file_lines = last_file.readlines()

        directory = get_directory("partcompsinv")
        writer, f = open_file(directory)

        header = ['numcobro', 'fchinv', 'fchcreacion']
        writer.writerow(header)

        # Content
        partner_ids = self.env['res.partner'].search([('customer', '=', True)])
        account_move_line_ids = self.env['account.move.line'].search(
            [('partner_id.id', 'in', partner_ids.ids), ('account_id.internal_type', '=', 'receivable'),
             ('amount_residual', '=', 0), ('reconciled', '=', True), ('full_reconcile_id', '!=', False),
             ('create_date', '>=', datetime.today() + relativedelta(years=-3)), '|',
             ('matched_debit_ids.origin_returned_move_ids', '!=', False),
             ('matched_credit_ids.origin_returned_move_ids', '!=', False)])
        account_invoice_refund_move_line_ids = self.env['account.move.line'].search(
            [('partner_id.id', 'in', partner_ids.ids), ('account_id.internal_type', '=', 'receivable'),
             ('amount_residual', '=', 0), ('reconciled', '=', True), ('full_reconcile_id', '!=', False),
             ('invoice_id.type', '=', 'out_refund'), ('create_date', '>=', datetime.today() + relativedelta(years=-3))])

        for partner_id in partner_ids:
            account_invoice_refund_move_lines = account_invoice_refund_move_line_ids.filtered(
                lambda x: x.partner_id.id == partner_id.id)
            for account_invoice_refund_move_line in account_invoice_refund_move_lines:
                row = []
                if account_invoice_refund_move_line.invoice_id and account_invoice_refund_move_line.invoice_id.type in [
                    'out_invoice', 'out_refund']:
                    row.append(account_invoice_refund_move_line.invoice_id.number)  # numcobro
                elif account_invoice_refund_move_line.document:
                    row.append(account_invoice_refund_move_line.move_id.payment_document_id.name)  # numcobro
                elif account_invoice_refund_move_line.order_id:
                    row.append(account_invoice_refund_move_line.move_id.payment_order_id.name)  # numcobro
                elif account_invoice_refund_move_line.document_line_id:
                    row.append(account_invoice_refund_move_line.document_line_id.document_id.name)  # numcobro
                elif account_invoice_refund_move_line.bank_payment_line_id:
                    row.append(account_invoice_refund_move_line.bank_payment_line_id.name)  # numcobro
                else:
                    row.append(account_invoice_refund_move_line.ref)  # numcobro
                row.append(account_invoice_refund_move_line.date)  # fchinv
                row.append(account_invoice_refund_move_line.create_date)  # fchcreacion
                writer.writerow(row)
            account_move_lines = account_move_line_ids.filtered(lambda x: x.partner_id.id == partner_id.id)
            for account_move_line in account_move_lines:
                row = []
                if account_move_line.invoice_id and account_move_line.invoice_id.type in [
                    'out_invoice', 'out_refund']:
                    row.append(account_move_line.invoice_id.number)  # numcobro
                elif account_move_line.document:
                    row.append(account_move_line.move_id.payment_document_id.name)  # numcobro
                elif account_move_line.order_id:
                    row.append(account_move_line.move_id.payment_order_id.name)  # numcobro
                elif account_move_line.document_line_id:
                    row.append(account_move_line.document_line_id.document_id.name)  # numcobro
                elif account_move_line.bank_payment_line_id:
                    row.append(account_move_line.bank_payment_line_id.name)  # numcobro
                else:
                    row.append(account_move_line.ref)  # numcobro
                row.append(account_move_line.date)  # fchinv
                row.append(account_move_line.create_date)  # fchcreacion
                writer.writerow(row)
        f.close()

        current_file = open(get_directory("partcompsinv"), 'r')
        current_file_lines = current_file.readlines()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('partcompsinv'), ftp.getcwd() + '/partcompsinv.csv')

        ftp.chdir(path)
        if not last_file:
            ftp.put(get_directory('partcompsinv'), ftp.getcwd() + '/partcompsinv.csv')
        else:
            remote_file = ftp.open('partcompsinv.csv', 'w+')
            writer = csv.writer(remote_file, delimiter=';', quotechar='"', dialect='excel', quoting=csv.QUOTE_MINIMAL)

            header = ['numcobro', 'fchinv', 'fchcreacion']
            writer.writerow(header)

            for current_file_line in current_file_lines:
                if current_file_line not in last_file_lines:
                    cfl = current_file_line.split(';')
                    row = cfl[:-1]
                    writer.writerow(row)
            remote_file.close()
            last_file.close()
            current_file.close()

    # Obligatorio
    def export_saldosnofacturados(self, ftp, path):
        directory = get_directory("saldosnofacturados")
        writer, f = open_file(directory)

        header = ['codcli', 'importe', 'fchfacturacion', 'plazopago', 'numpedido', 'numalbaran', 'campoid']
        writer.writerow(header)

        # Content
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('saldosnofacturados'), ftp.getcwd() + '/saldosnofacturados.csv')

        ftp.chdir(path)
        ftp.put(get_directory('saldosnofacturados'), ftp.getcwd() + '/saldosnofacturados.csv')

    # Obligatorio
    def export_ventas(self, ftp, path):
        directory = get_directory("ventas")
        writer, f = open_file(directory)

        header = ['codcli', 'anio', 'mes', 'importe']
        writer.writerow(header)

        # Content
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('ventas'), ftp.getcwd() + '/ventas.csv')

        ftp.chdir(path)
        ftp.put(get_directory('ventas'), ftp.getcwd() + '/ventas.csv')

    # Obligatorio
    def export_facturasefectos(self, ftp, sociedad, path):
        last_file = False
        last_file_lines = False
        if os.path.exists(get_directory('facturasefectos')):
            last_file = open(get_directory("facturasefectos"), 'r')
            last_file_lines = last_file.readlines()

        directory = get_directory("facturasefectos")
        writer, f = open_file(directory)

        header = ['campoidfactura', 'reldocs', 'codcli', 'ndoc', 'ndocinterno', 'tdoc', 'importependiente',
                  'importeoriginal', 'importeimpuestos', 'importebase', 'estado', 'fchcreacion', 'fchemi', 'fchvcto',
                  'fchcomp', 'codmondoc', 'impmondoc']
        writer.writerow(header)

        # Content
        partner_ids = self.env['res.partner'].search([('customer', '=', True)])
        account_move_line_ids_partabiertas = self.env['account.move.line'].search(
            [('partner_id.id', 'in', partner_ids.ids), ('account_id.internal_type', '=', 'receivable'),
             ('amount_residual', '!=', 0), ('create_date', '>', datetime.today() + relativedelta(years=-3))])
        account_move_line_ids_partcomps = self.env['account.move.line'].search(
            [('partner_id.id', 'in', partner_ids.ids), ('account_id.internal_type', '=', 'receivable'),
             ('amount_residual', '=', 0), ('reconciled', '=', True), ('full_reconcile_id', '!=', False),
             ('create_date', '>', datetime.today() + relativedelta(years=-3)), '|',
             ('matched_debit_ids.origin_returned_move_ids', '=', False),
             ('matched_credit_ids.origin_returned_move_ids', '=', False)])
        account_move_line_ids = account_move_line_ids_partabiertas + account_move_line_ids_partcomps
        for partner_id in partner_ids:
            account_move_lines = account_move_line_ids.filtered(lambda x: x.partner_id.id == partner_id.id)
            for account_move_line in account_move_lines:
                row = []
                row.append(str(account_move_line.id))  # campoidfactura
                row.append("")  # reldocs
                row.append(str(partner_id.id))  # codcli
                if account_move_line.invoice_id and account_move_line.invoice_id.type in ['out_invoice', 'out_refund']:
                    row.append(account_move_line.invoice_id.number)  # ndoc
                elif account_move_line.document:
                    row.append(account_move_line.move_id.payment_document_id.name)  # ndoc
                elif account_move_line.order_id:
                    row.append(account_move_line.move_id.payment_order_id.name)  # ndoc
                elif account_move_line.document_line_id:
                    row.append(account_move_line.document_line_id.document_id.name)  # ndoc
                elif account_move_line.bank_payment_line_id:
                    row.append(account_move_line.bank_payment_line_id.name)  # ndoc
                else:
                    row.append(account_move_line.ref)  # ndoc
                row.append("")  # ndocinterno
                if account_move_line.invoice_id and account_move_line.invoice_id.type == 'out_invoice':
                    row.append("Factura")  # tdoc
                elif account_move_line.invoice_id and account_move_line.invoice_id.type == 'out_refund':
                    row.append("Abono")  # tdoc
                elif account_move_line.document or account_move_line.order_id or account_move_line.document_line_id or account_move_line.bank_payment_line_id or (
                        account_move_line.full_reconcile_id.reconciled_line_ids.filtered(
                            lambda x: x.order_id and x.id != account_move_line.id and x.full_reconcile_id.id == account_move_line.full_reconcile_id.id)):
                    row.append("Efecto")  # tdoc
                else:
                    row.append("Otro")  # tdoc
                row.append(account_move_line.amount_residual)  # importependiente
                row.append(account_move_line.balance)  # importeoriginal
                importeimpuestos = abs(
                    sum(account_move_line.move_id.line_ids.filtered(lambda x: x.tax_line_id).mapped('balance')))
                row.append(importeimpuestos)  # importeimpuestos
                row.append(float('{:.2f}'.format(account_move_line.balance - importeimpuestos)))  # importebase
                if account_move_line.amount_residual != 0:
                    row.append(1)  # estado
                else:
                    row.append(2)  # estado
                row.append(account_move_line.create_date.date())  # fchcreacion
                row.append(account_move_line.date)  # fchemi
                row.append(account_move_line.date_maturity)  # fchvcto
                ids = []
                ids.extend([r.debit_move_id.id for r in
                            account_move_line.matched_debit_ids] if account_move_line.credit > 0 else [
                    r.credit_move_id.id for r in account_move_line.matched_credit_ids])
                aml = self.env['account.move.line'].browse(ids)
                if aml:
                    row.append(max(aml.mapped('date_maturity')))  # fchcomp
                else:
                    row.append(account_move_line.date_maturity)  # fchcomp
                row.append("")  # codmondoc
                row.append("")  # impmondoc
                writer.writerow(row)
        f.close()

        current_file = open(get_directory("facturasefectos"), 'r')
        current_file_lines = current_file.readlines()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('facturasefectos'), ftp.getcwd() + '/facturasefectos.csv')

        ftp.chdir(path)
        if not last_file:
            ftp.put(get_directory('facturasefectos'), ftp.getcwd() + '/facturasefectos.csv')
        else:
            remote_file = ftp.open('facturasefectos.csv', 'w+')
            writer = csv.writer(remote_file, delimiter=';', quotechar='"', dialect='excel', quoting=csv.QUOTE_MINIMAL)

            header = ['campoidfactura', 'reldocs', 'codcli', 'ndoc', 'ndocinterno', 'tdoc', 'importependiente',
                      'importeoriginal', 'importeimpuestos', 'importebase', 'estado', 'fchcreacion', 'fchemi',
                      'fchvcto',
                      'fchcomp', 'codmondoc', 'impmondoc']
            writer.writerow(header)

            for current_file_line in current_file_lines:
                if current_file_line not in last_file_lines:
                    cfl = current_file_line.split(';')
                    row = cfl[:-1]
                    writer.writerow(row)
            remote_file.close()
            last_file.close()
            current_file.close()

    # Obligatorio
    def export_facturaspartidas(self, ftp, sociedad, path):
        directory = get_directory("facturaspartidas")
        writer, f = open_file(directory)

        header = ['campoidfactura', 'campoidpartidaabierta']
        writer.writerow(header)

        # Content
        partner_ids = self.env['res.partner'].search([('customer', '=', True)])
        account_invoice_ids = self.env['account.invoice'].search([('partner_id.id', 'in', partner_ids.ids)])
        account_move_line_ids = self.env['account.move.line'].search(
            [('partner_id.id', 'in', partner_ids.ids), ('account_id.internal_type', '=', 'receivable'),
             ('amount_residual', '!=', 0)])
        for account_invoice in account_invoice_ids:
            for account_move_line in account_move_line_ids:
                if account_move_line.id in account_invoice.move_id.line_ids.ids:
                    row = []
                    row.append(str(account_invoice.id))  # campoidfactura
                    row.append(str(account_move_line.id))  # campoidpartidaabierta
                    writer.writerow(row)
        f.close()

        ftp.chdir('/configuracion')
        ftp.put(get_directory('facturaspartidas'), ftp.getcwd() + '/facturaspartidas.csv')

        ftp.chdir(path)
        ftp.put(get_directory('facturaspartidas'), ftp.getcwd() + '/facturaspartidas.csv')

    def export_files(self):
        ftp = self.connect()
        sociedades = self.env['res.company'].search([])

        ftp.chdir("/")
        self.export_sociedades(ftp, sociedades)

        if 'ColaCargas' not in ftp.listdir():
            ftp.mkdir('ColaCargas')

        ftp.chdir("/ColaCargas")
        for sociedad in sociedades:
            name = sociedad.name.replace(" ", "_")
            name = name.replace(".", "")
            if name not in ftp.listdir():
                ftp.mkdir(name)
            ftp.chdir("/ColaCargas/%s" % name)

            now = datetime.now()
            formated_date = str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2) + "." + str(now.hour).zfill(2) + str(now.minute).zfill(2)
            if formated_date not in ftp.listdir():
                ftp.mkdir(formated_date)

            ftp.chdir(formated_date)
            path = ftp.getcwd()

            self.export_clasifcriterios(ftp, path)
            self.export_viaspago(ftp, sociedad, path)
            self.export_cndpago(ftp, sociedad, path)
            self.export_clientes(ftp, sociedad, path)
            self.export_direcciones(ftp, sociedad, path)
            self.export_contactos(ftp, sociedad, path)
            self.export_partabiertas(ftp, sociedad, path)
            self.export_partcomps(ftp, sociedad, path)
            self.export_partcompsinv(ftp, sociedad, path)
            self.export_saldosnofacturados(ftp, path)
            self.export_ventas(ftp, path)
            self.export_facturasefectos(ftp, sociedad, path)
            self.export_facturaspartidas(ftp, sociedad, path)

        ftp.close()

    def connect(self):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        server = self.env["ir.default"].sudo().get("res.config.settings", "axesor_server")
        port = self.env["ir.default"].sudo().get("res.config.settings", "axesor_port")
        username = self.env["ir.default"].sudo().get("res.config.settings", "axesor_username")
        password = self.env["ir.default"].sudo().get("res.config.settings", "axesor_password")
        ssh_client.connect(hostname=server, port=port, username=username, password=password)
        ftp_client = ssh_client.open_sftp()
        return ftp_client
