# -*- coding: utf-8 -*-
from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from lxml import etree
import json
import logging

_logger = logging.getLogger(__name__)


RANGES = {
        'incipiente': range(0, 76),
        'aceptable': range(77, 152),
        'confiable': range(153, 228)
    }

CRM_DIAGNOSTIC_SELECTION_FIELDS = {
    'doctype': 'tipo_documento',
    'x_ubic': 'ubicacion',
    'x_actcomer': 'actividad_micronegocio',
    'x_microneg': 'tipo_micronegocio',
    }

ANSWER_VALUES = {
        'si': 5,
        'no': 1,
        'no_aplica': 0
    }

TEXT_VALUATION = {
        1: 'Incipiente',
        2: 'Aceptable',
        3: 'Confiable'
    }


class CrmLead(models.Model):
    _inherit = 'crm.lead'


    crm_lead_id = fields.One2many(
        'crm.diagnostic',
        'lead_id',
        string='CRM Diagnostic',
        copy=False)
    mentors = fields.Many2many(
        'res.partner',
        string='Mentores',
        readonly=True
    )
    coordinador = fields.Many2one(
        'res.users',
        string='Coordinador'
    )
    diagnostico = fields.Selection(
        selection=[
            ('competitividad', 'Nivel de competitividad'),
            ('incipiente', 'Incipiento'),
            ('aceptable', 'Aceptable'),
            ('confiable', 'Confiable')],
        string='Diagnostico'
    )
    # computed fields
    first_module_ready = fields.Boolean(
        compute='compute_first_module'
    )
    second_module_read = fields.Boolean(
        compute='compute_second_module'
    )
    third_module_ready = fields.Boolean(
        compute='compute_third_module'
    )

    # returning an action to go to crm.diagnostic form view related to lead
    def action_crm_diagnostic_view(self):
        for record in self:
            # validating if it is necessary to create a new diagnistic record or return the first on the list
            if len(record.crm_lead_id) > 0:
                return record.action_to_return_to_crm_diagnostic(record.crm_lead_id[0])
            else:
                # we avoid to execute the diagnostic whether question modules haven't executed yet
                if not record.first_module_ready or not record.second_module_read or not record.third_module_ready:
                    raise ValidationError('Para realizar el diagnostico, debe responder las preguntas de los 3 modulos.')
                crm_diagnostic_vals = record.getting_values_to_crm_diagnostic()
                crm_diagnostic_id = self.env['crm.diagnostic'].create(crm_diagnostic_vals)
                crm_diagnostic_id.valuacion_diagnostico = record.diagnostico
            return record.action_to_return_to_crm_diagnostic(crm_diagnostic_id)

    # return a dic values for crm.diagnostic
    def getting_values_to_crm_diagnostic(self):
        for lead in self:
            dic_vals = {
                'lead_id': lead.id,
                'fecha': fields.Date.today(),
                'nombre_negocio': lead.x_nombre_negocio,
                'nombre_propietario': lead.x_nombre,
                'numero_identificacion': lead.x_identification,
                'crm_diagnostic_line_ids': []
            }
            dic_sel_fields = lead.getting_selection_fields_to_dignostic_form(lead)
            dic_vals.update(dic_sel_fields)
            dic_vals['crm_diagnostic_line_ids'] = lead.prepare_diagnostic_lines(lead)
            return dic_vals

    # getting str values from selection fields
    @api.model
    def getting_selection_fields_to_dignostic_form(self, lead):
        dic_fields = lead.read()[0]
        dic_selection_fields = {}
        for k, v in CRM_DIAGNOSTIC_SELECTION_FIELDS.items():
            for key in dic_fields:
                if k == key:
                    dic_selection_fields[v] = dict(lead._fields[k].selection).get(getattr(lead, k))
        return dic_selection_fields

    # return a list of values to create diagnostic lines
    @api.model
    def prepare_diagnostic_lines(self, lead):
        lines = []
        dic_fields = lead.read()[0]
        _fields = self.env['ir.model.fields'].search(
            [('name', 'ilike', 'x_'),
             ('model_id.model', '=', lead._name),
             ('selectable', '=', True),
             ('ttype', '=', 'selection')]).filtered(
                 lambda f : f.name.startswith('x_'))
        puntaje = 0
        for field in _fields:
            field_value = dic_fields.get(field.name)
            # TODO
            # validating if the field value is in ANSWER_VALUES
            # we obtain certain values from lead on its field what is iterating
            if field_value in ANSWER_VALUES:
                answer = dict(lead._fields[field.name].selection).get(getattr(lead, field.name))
                score = ANSWER_VALUES.get(field_value)
                valuation = TEXT_VALUATION.get(score)
                suggestion, area = self.get_sugestion(field.name, score)
                lines.append(
                    (0, 0, {
                        'name': field.field_description,
                        'respuesta': answer,
                        'puntaje': score,
                        'area': area,
                        'sugerencia': suggestion,
                        'valoracion': valuation,
                        }))
            else:
                answer = dict(lead._fields[field.name].selection).get(getattr(lead, field.name))
                score = ANSWER_VALUES.get(field_value)
                valuation = TEXT_VALUATION.get(score)
                suggestion, area = self.get_sugestion(field.name, score)
                lines.append(
                    (0, 0, {
                        'name': field.field_description,
                        'respuesta': answer,
                        'puntaje': score,
                        'area': area,
                        'sugerencia': suggestion,
                        'valoracion': valuation,
                        }))
            if score:
                puntaje += score
        self.set_diagnostico(puntaje, lead)
        return lines

    # set diagnostico based on range
    @api.model
    def set_diagnostico(self, score, lead):
        if score > 380:
            lead.diagnostico = 'excelencia'
            return
        for k, v in RANGES.items():
            if score in v:
                lead.diagnostico = k

    # this method is called from cron
    def relate_events_to_leads(self):
        event_ids = self.available_events()
        if not event_ids:
            return
        lead_ids = self.search(
            [('mentors', '=', False),
             ('diagnostico', 'in', ('confiable', 'competente', 'excelencia'))])
        if not lead_ids:
            return
        for lead in lead_ids:
            for event in event_ids.sorted(reverse=True):
                # TODO
                # we remove the current item of lead_ids and event_ids of their each object array
                # because an opportunity has to be in an event
                event.opportunity_id = lead.id
                lead.mentors += event.partner_ids
                self.send_mail_notification(lead)
                event_ids -= event
                lead_ids -= lead
                break

    # send email notification to coordinador and facilitador
    

    # return events availables
    def available_events(self):
        week_days = range(0, 5)
        date_to_search = fields.Date.today() + timedelta(days=1)
        events =  self.env['calendar.event'].search(
            ['|', ('start_date', '>=', date_to_search),
             ('start_datetime', '>=', date_to_search),
             ('opportunity_id', '=', False)])
        for event in events:
            # validate if we have to use start date or start date time to check the day of the week
            if event.start_date:
                if event.start_date.weekday() not in week_days:
                    events -= event
            else:
                if event.start_datetime.weekday() not in week_days:
                    events -= event
        return events

    # returning area and suggestion base on field_name and score
    @api.model
    def get_sugestion(self, field_name, score):
        suggestion = False
        area = False
        # TODO if any param comes in False we immediatly return values in False
        if not score or not field_name:
            return suggestion, area
        if field_name in SUGGEST_VALUATION:
            suggestion = SUGGEST_VALUATION[field_name].get(score, False)
            area = SUGGEST_VALUATION[field_name].get('area', False)
        return suggestion, area

    @api.model
    def action_to_return_to_crm_diagnostic(self, crm_diagnostic_id):
        search_view = self.env.ref('crm_diagnostic.crm_diagnostic_view')
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'crm.diagnostic',
            'res_id': crm_diagnostic_id.id,
            'views': [(search_view.id, 'form')],
            'view_id': search_view.id,
            'target': 'current',
            'flags': {'mode': 'readonly', 'action_buttons': True},
        }

##########################################################################
#                            ROLE METHODS
##########################################################################

    # return the field list to validate the module1
    def fields_module1(self):
        return [
            'x_nombre_negocio', 'x_nombre', 'doctype', 'x_identification', 'x_sexo',
            'x_etnia', 'x_edad', 'country_id', 'state_id', 'xcity', 'x_vereda', 'mobile',
            'x_limitacion', 'x_escolaridad', 'x_grupos',
            'x_estrato', 'x_situacion', 'x_sector', 'x_actcomer', 'x_state_id', 'x_city_id',
            'x_ubic', 'x_dir_neg', 'x_com_cuenta', 'x_merc78_form', 'x_merc80_form',
            'x_merc79_form', 'x_merc81_form', 'x_que_por_ren', 'x_que_por_ren_ant',
            'x_tien_dur', 'tie_us_cre', 'tie_ca_ide', 'x_datos1']

    # return the field list to validate the module2
    def fields_module2(self):
        return ['x_cont1', 'x_cont1_por', 'first_module_ready']

    # methos that return list of fields by section
    def fields_module3_generalities(self):
        return [
            'in_empleo', 'x_forma58_form', 'x_forma61_form', 'x_forma60_form',
            'x_forma65_inf', 'x_datos3']

    def fields_module3_biosecurity(self):
        return [
            'x_proto1', 'x_proto2', 'x_proto3', 'x_proto4', 'x_proto6',
            'x_proto7', 'x_proto8', 'x_proto9', 'x_proto10', 'x_proto11', 'x_proto12',
            'x_proto13', 'x_proto14', 'x_proto15', 'x_proto16'
        ]

    def fields_module3_business_model(self):
        return [
            'x_model21', 'x_model22', 'x_model23', 'x_model24', 'x_model25',
            'x_model26', 'x_model27', 'x_model28', 'x_model29', 'x_model30', 'x_model31',
            'x_model32', 'x_model33', 'x_model34', 'x_model35', 'x_model36', 'x_model37',
        ]

    def fields_module3_production(self):
        return [
            'x_innova24', 'x_innova25', 'x_innova26', 'x_innova27', 'x_prodl42',
            'x_prodl43', 'x_innova29', 'x_innova33', 'x_innova36', 'x_prodl47', 'x_innova39'
        ]

    def fields_module3_innovation(self):
        return [
            'x_innova40', 'x_ninova50', 'x_innova43_inf', 'x_ninova52',
            'x_ninova54'
        ]

    def fields_module3_formalization(self):
        return [
            'x_for55', 'x_forma50_inf', 'x_forma52_inf', 'x_forma54_inf',
            'x_forma56_inf', 'n_los_empl'
        ]

    def fields_module3_organization(self):
        return [
            'x_org61', 'x_org62', 'x_org63', 'x_org64', 'x_org65', 'x_org66',
            'x_org67', 'x_org68'
        ]

    def fields_module3_marketing(self):
        return [
            'x_mer69', 'x_mer70', 'x_mer71', 'x_mer72', 'x_mer73', 'x_mer74',
            'x_mer75', 'prom77', 'prom78', 'x_merc86_form', 'prom79', 'prom80', 'prom81',
            'prom82'
        ]

    def fields_module3_financial(self):
        return [
            'x_finan92_form', 'x_finan93_form', 'x_fin85', 'x_finan98_form',
            'x_fin87n','x_fin88n','x_fin89n','x_fin90n','x_fin91n','x_fin92n','x_fin93n',
            'x_fin94n','x_fin95n','x_fin96n', 'x_fin97n'
        ]

    def full_list_field(self):
        full_fields = []
        full_fields.extend(self.fields_module3_generalities())
        full_fields.extend(self.fields_module3_biosecurity())
        full_fields.extend(self.fields_module3_business_model())
        full_fields.extend(self.fields_module3_production())
        full_fields.extend(self.fields_module3_innovation())
        full_fields.extend(self.fields_module3_formalization())
        full_fields.extend(self.fields_module3_organization())
        full_fields.extend(self.fields_module3_marketing())
        full_fields.extend(self.fields_module3_financial())
        full_fields.extend(['second_module_read'])
        return full_fields
    # ended section

    # validating if the current user has the facilitador profile
    

    # validating if the current user has the cordinator profile
    

    # computed if the module1 is ok
    @api.depends(fields_module1)
    def compute_first_module(self):
        for lead in self:
            if lead.is_facilitator():
                if lead.all_fields_module1_are_ok():
                    lead.first_module_ready = True
                else:
                    lead.first_module_ready = False
            else:
                lead.first_module_ready = False

    # computed if the module2 is ok
    @api.depends(fields_module2)
    def compute_second_module(self):
        for lead in self:
            if lead.is_facilitator() and lead.first_module_ready:
                if lead.all_fields_module2_are_ok():
                    lead.second_module_read = True
                else:
                    lead.second_module_read = False
            else:
                lead.second_module_read = False

    # computed if the module3 is ok
    @api.depends(full_list_field)
    def compute_third_module(self):
        for lead in self:
            if lead.is_facilitator() and lead.second_module_read:
                if lead.all_fields_module3_are_ok():
                    lead.third_module_ready = True
                else:
                    lead.third_module_ready = False
            else:
                lead.third_module_ready = False

    # validating it all fields of module3 were filled
    def all_fields_module3_are_ok(self):
        result = []
        # fields = self.fields_module3()
        result.append(self.check_generalities_fields(self.fields_module3_generalities()))
        result.append(self.check_biosecurity_fields(self.fields_module3_biosecurity()))
        result.append(self.check_business_model_fields(self.fields_module3_business_model()))
        result.append(self.check_production_fields(self.fields_module3_production()))
        result.append(self.check_innovation_fields(self.fields_module3_innovation()))
        result.append(self.check_formalization_fields(self.fields_module3_formalization()))
        result.append(self.check_organization_fields(self.fields_module3_organization()))
        result.append(self.check_marketing_fields(self.fields_module3_marketing()))
        result.append(self.check_financial_fields(self.fields_module3_financial()))
        if any(r == False for r in result):
            return False
        else:
            return True

    # checking if all generalities field section are ok
    def check_generalities_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # checking if all biosecurity field section are ok
    def check_biosecurity_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # checking if all business model field section are ok
    def check_business_model_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # checking if all production field section are ok
    def check_production_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # checking if all innovation field section are ok
    def check_innovation_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # checking if all formalization field section are ok
    def check_formalization_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # checking if all organization field section are ok
    def check_organization_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # checking if all marketing field section are ok
    def check_marketing_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # checking if all financial field section are ok
    def check_financial_fields(self, fields):
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True


    # validating it all fields of module1 were filled
    def all_fields_module1_are_ok(self):
        fields = self.fields_module1()
        if any(not getattr(self, field) for field in fields):
            return False
        else:
            return True

    # validating it all fields of module2 were filled
    def all_fields_module2_are_ok(self):
        if getattr(self, 'x_cont1') and getattr(self, 'x_cont1') == 'si':
            return True
        elif (getattr(self, 'x_cont1') and getattr(self, 'x_cont1') == 'no') and getattr(self, 'x_cont1_por'):
            return False
        else:
            return False

    # getting the stage by stage state
    @api.model
    def get_stage(self, stage_state):
        stage_id = self.env['crm.stage'].sudo().search([('stage_state', '=', stage_state)], limit=1)
        return stage_id

    # change the stage on lead according if the question modules
    @api.onchange('first_module_ready', 'second_module_read', 'third_module_ready')
    def update_stage(self):
        if self.is_facilitator():
            if self.first_module_ready:
                second_stage =  self.get_stage('segundo_encuentro')
                self.stage_id = second_stage if second_stage else self.stage_id
            if self.first_module_ready and self.second_module_read:
                third_stage =  self.get_stage('tercer_encuentro')
                self.stage_id = third_stage if third_stage else self.stage_id
            if self.first_module_ready and self.second_module_read and self.third_module_ready:
                fourth_stage =  self.get_stage('espera_de_plan')
                self.stage_id = fourth_stage if fourth_stage else self.stage_id

    # inherit method to validate if the current user has the cordinator profile
    # if so then we set readonly=False on mentors field
    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form', toolbar=False,
            submenu=False):
        res = super(CrmLead, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form' and self.is_cordinator():
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='mentors']"):
                if 'modifiers' in node.attrib:
                    modifiers = json.loads(node.attrib["modifiers"])
                    modifiers['readonly'] = False
                    node.attrib['modifiers'] = json.dumps(modifiers)
            res['arch'] = etree.tostring(doc)
        return res

##########################################################################
#                           ATTENTION PLAN METHODS
##########################################################################
    crm_attenation_plan_ids = fields.One2many(
        'crm.attention.plan',
        'lead_id',
        copy=False)

    # returning an action to go to crm.attention.plan form view related to lead
    def call_action_crm_attention_plan(self):
        for record in self:
            # validating if it is necessary to create a new attention plan record or return the first on the list
            if len(record.crm_attenation_plan_ids) > 0:
               return record.action_to_return_to_crm_attention_plan(record.crm_attenation_plan_ids[0])
            else:
                if len(record.crm_lead_id) <= 0:
                    # we avoid to execute the attention plan whether diagnostic haven't executed yet
                    raise ValidationError('No puede realizar el plan de atención sin antes haber realizado el diagnostico.')
                attention_plan_vals = record.getting_values_to_crm_attention_plan()
                crm_attention_id = self.env['crm.attention.plan'].create(attention_plan_vals)
                crm_attention_id.diagnostico = record.diagnostico
            return record.action_to_return_to_crm_attention_plan(crm_attention_id)

    # return a dic values for crm.diagnostic
    def getting_values_to_crm_attention_plan(self):
        for lead in self:
            dic_vals = {
                'lead_id': lead.id,
                'nombre_negocio': lead.x_nombre_negocio,
                'ubicacion': lead.x_dir_neg,
                'fecha': fields.Date.today(),
                'plan_line_ids': lead.get_attention_plan_lines()
            }
            return dic_vals

    def get_attention_plan_lines(self):
        lines = []
        items = ['48 H', '1 Semana', '2 Semanas', '1 Mes', 'A futuro', 'Hábitos a desarrollar']
        for item in items:
            lines.append(
                (0, 0, {
                    'prioridad': item,
                    'actividades': False,
                    'soluciones': False,
                    'reponsable': False,
                }))
        return lines

    @api.model
    def action_to_return_to_crm_attention_plan(self, crm_attention_id):
        form_view = self.env.ref('crm_diagnostic.q_crm_attention_plan_form_view')
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'crm.attention.plan',
            'res_id': crm_attention_id.id,
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'current',
        }
