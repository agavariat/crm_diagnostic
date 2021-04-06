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
        'incipiente': range(0, 90),
        'aceptable': range(91, 129),
        'confiable': range(130, 150)
    }
        
CRM_DIAGNOSTIC_SELECTION_FIELDS = {
    'doctype': 'tipo_documento',
    'x_ubic': 'ubicacion',
    'x_actcomer': 'actividad_micronegocio',
    'x_microneg': 'tipo_micronegocio',
    }

ANSWER_VALUES = {
        'si': 5,
        'en_proceso': 0,
        'no': 0,
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
        'area': 'PLANEAR'
        },
    'x_proto2': {
        1: 'Acompañamiento y asesoría en la implementación de los protocolos de bioseguridad según la actividad económica del micronegocio.',
        'area': 'PLANEAR'
        },
    'x_proto3': {
        1: 'Buscar proyectos y programas públicos y privados que subsidien o faciliten la obtención de tapabocas y elementos de protección para el micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto4': {
        1: 'Buscar proyectos y programas públicos y privados que subsidien o faciliten la obtención de tapabocas y elementos de protección para el micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto5': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto6': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto7': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto8': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto9': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto10': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto11': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto12': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto13': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'PLANEAR'
        },
    'x_proto14': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'HACER'
        },
    'x_proto15': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'HACER'
        },
    'x_proto16': {
        1: 'Capacitación e implementación en protocolos de bioseguridad para el funcionamiento seguro del micronegocio',
        'area': 'HACER'
        },
    'x_model21': {
        1: 'Capacitar al propietario en el diseño del modelo de negocio.',
        'area': 'HACER'
        },
    'x_model22': {
        1: 'Capacitar al propietario en el diseño del modelo de negocio.',
        'area': 'HACER'
        },
    'x_model23': {
        1: 'Capacitar al propietario del negocio sobre los canales de distribución y definir cuál es el más adecuado para el producto o servicio',
        'area': 'HACER'
        },
    'x_model24': {
        1: '',
        'area': 'HACER'
        },
    'x_model25': {
        1: 'Determinar los conocimiento y habilidades que requieren los trabajadores para laborar en el micronegocio',
        'area': 'HACER'
        },
    'x_model26': {
        1: 'Acompañamiento en programas de manipulación de alimentos',
        'area': 'HACER'
        },
    'x_model27': {
        1: 'Capacitar al propietario del negocio en seguridad y salud en el trabajo',
        'area': 'HACER'
        },
    'x_model28': {
        1: 'Definir procedimientos, instrucciones y normas que se deben tener para producir alimentos saludables',
        'area': 'HACER'
        },
    'x_model29': {
        1: 'Acompañamiento en la búsqueda y selección de proveedores que mejor se adecuen a las necesidades del negocio',
        'area': 'HACER'
        },
    'x_model30': {
        1: 'Orientar al personal sobre los beneficios que puede obtener en cada uno de los pagos.',
        'area': 'VERIFICAR'
        },
    'x_model31': {
        1: 'Capacitar al propietario del negocio en proyecciones de compra.',
        'area': 'VERIFICAR'
        },
    'x_model32': {
        1: 'Acompañamiento en la definición de procesos estandarizado para la producción o manipulación del producto',
        'area': 'VERIFICAR'
        },
    'x_model33': {
        1: 'Acompañamiento en la definición de proceso estandarizado para la producción o manipulación del producto',
        'area': 'ACTUAR'
        },
    'x_model34': {
        1: 'Acompañamiento en la definición de controles de existencias, que permitan conocer los productos de mayor demanda y realizar compras inteligentes.',
        'area': 'ACTUAR'
        },
}
class CrmLead(models.Model):
    _inherit = 'crm.lead'


    crm_lead_id = fields.One2many(
        'crm.diagnostic',
        'lead_id',
        string='CRM Diagnostic',
        copy=False)
      
    diagnostico = fields.Selection(
        selection=[
            ('competitividad', 'Nivel de competitividad'),
            ('incipiente', 'Incipiento'),
            ('aceptable', 'Aceptable'),
            ('confiable', 'Confiable')],
        string='Diagnostico'
    )
  
    # returning an action to go to crm.diagnostic form view related to lead ##
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
        if score > 150:
            lead.diagnostico = 'confiable'
            return
        for k, v in RANGES.items():
            if score in v:
                lead.diagnostico = k


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