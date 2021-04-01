# -*- coding: utf-8 -*-
from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from datetime import datetime, date, time, timedelta
import logging
import pandas as pd
import base64
import matplotlib.pyplot as plt
import numpy as np
from math import pi
import io


_logger = logging.getLogger(__name__)


class CrmDiagnostic(models.Model):
    _name = 'crm.diagnostic'
    _rec_name = 'nombre_negocio'


    lead_id = fields.Many2one('crm.lead')
    fecha = fields.Date("Fecha")
    nombre_negocio = fields.Char(string="Nombre del Negocio")
    nombre_propietario = fields.Char(string="Nombre del Propietario")
    tipo_documento = fields.Char(string="Tipo de Documento")
    ubicacion = fields.Char(string="Ubicación")
    actividad_micronegocio = fields.Char(string="Actividad del Micronegocio")
    tipo_micronegocio = fields.Char(string="Tipo de Negocio")
    numero_identificacion = fields.Char(string="Numero de Identificacion")
    codigo_formulario = fields.Char(string="Codigo de formulario")
    valoracion_micronegocio = fields.Char(string="Valoracion del Micronegocio")
    diagnostico = fields.Text(string="Diagnostico")
    valuacion_diagnostico = fields.Selection(
        selection=[
            ('competitividad', 'Nivel de competitividad'),
            ('incipiente', 'Incipiento'),
            ('aceptable', 'Aceptable'),
            ('confiable', 'Confiable')],
        string='Valuación de diagnostico'
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self : self.env.company)
    # principal records
    crm_diagnostic_line_ids = fields.One2many(
        'crm.diagnostic.line',
        'diagnostic_id',
    )
    # records for Orientaciones de bioseguridad
  #  crm_diagnostic_line_orientation_ids = fields.One2many(
   #     'crm.diagnostic.line',
   #     compute='_get_lines_for_areas')

    #diagnostic_chart = fields.Char(
    #    compute='_get_chart', store=False)

    diagnostic_chart = fields.Html(
        compute='_get_chart', store=True, sanitize=False)
    char_img = fields.Binary(compute='_get_chart', store=True,)
    char_img_bar = fields.Binary(compute='_get_chart', store=True,)
    diagnostic_chart_two = fields.Char(
    compute='_get_chart', store=True)

  #  @api.depends('crm_diagnostic_line_ids')
  #  def _get_lines_for_areas(self):
  #    for record in self:
  #        record.crm_diagnostic_line_orientation_ids = self.remove_duplicate_suggest_lines(
  #            record.crm_diagnostic_line_ids.filtered(
  #                lambda line : line.area == 'PROTOCOLOS DE BIOSEGURIDAD')
  #        )
        
    @api.depends('crm_diagnostic_line_ids')
    def _get_chart(self):
        for diagnostic in self:
            bioseguridad = 0
            
            for line in diagnostic.crm_diagnostic_line_orientation_ids:
                bioseguridad += int(line.puntaje)
         
            data_chart = [bioseguridad] 

            data = self.make_chart_radar(data_chart)
            data2 = self.make_chart_barh([bioseguridad/0.75])
            diagnostic.char_img = base64.b64encode(data)
            diagnostic.char_img_bar = base64.b64encode(data2)

    @api.model
    def create(self, vals):
        context = dict(self.env.context)
        res = super(CrmDiagnostic, self.with_context(context)).create(vals)
        return res
