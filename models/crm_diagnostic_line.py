# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError



class CrmDiagnosticLine(models.Model):
    _name = 'crm.diagnostic.line'
    _description = 'Líneas de diagnostico'
   # _rec_name = 'area'

    ANSWER_VALUES = {
        'si': 1, 
        'no': 2,
        'no_aplica': 0
    }

    TEXT_VALUATION = {
        1: 'Incipiente',
        2: 'Aceptable',
        3: 'Confiable'
    }


    sequence = fields.Integer(
        default=10)
    name = fields.Char(
        string='Pregunta',
    )
    respuesta =  fields.Char(
        string='Respuesta'
    )
    puntaje = fields.Char(
        string='Puntaje'
    )
    valoracion = fields.Char(
        string='Valoración'
    )
    diagnostic_id = fields.Many2one(
        'crm.diagnostic'
    )


    @api.model
    def create(self, values):
        return super(CrmDiagnosticLine, self).create(values)
