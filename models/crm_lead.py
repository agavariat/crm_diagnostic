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

SUGGEST_VALUATION = {
    'x_proto1': {
        1: 'Acompañamiento y asesoría en la implementación de los protocolos de bioseguridad según la actividad económica del micronegocio.',
        2: 'Acompañamiento y asesoría en la implementación de los protocolos de bioseguridad según la actividad económica del micronegocio.',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto2': {
        1: 'Acompañamiento y asesoría en la implementación de los protocolos de bioseguridad según la actividad económica del micronegocio.',
        2: 'Acompañamiento y asesoría en la implementación de los protocolos de bioseguridad según la actividad económica del micronegocio.',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto3': {
        1: 'Buscar proyectos y programas públicos y privados que subsidien o faciliten la obtención de tapabocas y elementos de protección para el micronegocio',
        2: 'Buscar proyectos y programas públicos y privados que subsidien o faciliten la obtención de tapabocas y elementos de protección para el micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto4': {
        1: 'Buscar proyectos y programas públicos y privados que subsidien o faciliten la obtención de tapabocas y elementos de protección para el micronegocio',
        2: 'Buscar proyectos y programas públicos y privados que subsidien o faciliten la obtención de tapabocas y elementos de protección para el micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto6': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto7': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto8': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto9': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto10': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto11': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto12': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto13': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto14': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto15': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
    'x_proto16': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        2: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        3: '',
        4: '',
        5: '',
        'area': 'PROTOCOLOS DE BIOSEGURIDAD'
        },
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
   

    # returning an action to go to crm.diagnostic form view related to lead
    def action_crm_diagnostic_view(self):
        for record in self:
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

   
 