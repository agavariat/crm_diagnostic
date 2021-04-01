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
        'confiable': range(153, 228),
        'competente': range(229, 304),
        'excelencia': range(305, 380)
    }

CRM_DIAGNOSTIC_SELECTION_FIELDS = {
    'doctype': 'tipo_documento',
    'x_ubic': 'ubicacion',
    'x_actcomer': 'actividad_micronegocio',
    'x_microneg': 'tipo_micronegocio',
    }

ANSWER_VALUES = {
        'si': 5,
        'en_proceso': 3,
        'no': 1,
        'no_aplica': 0,
        'totalmente_de_acuerdo': 5,
        'de_acuerdo': 4,
        'ni_de_acuerdo_ni_en_desacuerdo': 3,
        'en_desacuerdo': 2,
        'totalmente_en_desacuerdo': 1
    }

TEXT_VALUATION = {
        1: 'Incipiente',
        2: 'Aceptable',
        3: 'Confiable',
        4: 'Competente',
        5: 'Excelencia'
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
            ('confiable', 'Confiable'),
            ('competente', 'Competente'),
            ('excelencia', 'Excelencia')],
        string='Diagnostico'
    )
  
    

    # returning an action to go to crm.diagnostic form view related to lead
    def action_crm_diagnostic_view(self):
        for record in self:
            # validating if it is necessary to create a new diagnistic record or return the first on the list
            if len(record.crm_lead_id) > 0:
                return record.action_to_return_to_crm_diagnostic(record.crm_lead_id[0])
            else:
                # we avoid to execute the diagnostic whether question modules haven't executed yet
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
    @api.model
    def send_mail_notification(self, lead_id):
        try:
            template_id = self.env.ref('crm_diagnostic.q_mail_template_event_notification')
            template_id.send_mail(lead_id.id, force_send=True)
        except Exception as e:
            print(e)

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
