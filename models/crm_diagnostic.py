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
    numero_identificacion = fields.Char(string="Número de Identificacion")
    codigo_formulario = fields.Char(string="Codigo de formulario")
    valoracion_micronegocio = fields.Char(string="Valoracion del Micronegocio")
    diagnostico = fields.Text(strint="Diagnóstico") 
    valuacion_diagnostico = fields.Selection(
        selection=[
            ('competitividad', 'Nivel de competitividad'),
            ('incipiente', 'Incipiento'),
            ('aceptable', 'Aceptable'),
            ('confiable', 'Confiable')],
        string='Valuación de diagnóstico'
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self : self.env.company)
    # principal records
    crm_diagnostic_line_ids = fields.One2many(
        'crm.diagnostic.line',
        'diagnostic_id',
    )
    crm_diagnostic_line_innovation_ids = fields.One2many(
        'crm.diagnostic.line',
        compute='_get_lines_for_areas')
    # records for Orientaciones de bioseguridad
    crm_diagnostic_line_orientation_ids = fields.One2many(
        'crm.diagnostic.line',
        compute='_get_lines_for_areas')
    # records for Modelo de Negocio
    crm_diagnostic_line_business_model_ids = fields.One2many(
        'crm.diagnostic.line',
        compute='_get_lines_for_areas')
    # records for Producción
    crm_diagnostic_line_production_ids = fields.One2many(
        'crm.diagnostic.line',
        compute='_get_lines_for_areas')

    diagnostic_chart = fields.Html(
        compute='_get_chart', store=True, sanitize=False)
    char_img = fields.Binary(compute='_get_chart', store=True,)
    char_img_bar = fields.Binary(compute='_get_chart', store=True,)
    #char_img_barx = fields.Binary(compute='_get_chart', store=True,)
    diagnostic_chart_two = fields.Char(
    compute='_get_chart', store=True)

    @api.depends('crm_diagnostic_line_ids')
    def _get_lines_for_areas(self):
      for record in self:
          record.crm_diagnostic_line_innovation_ids = self.remove_duplicate_suggest_lines(
              record.crm_diagnostic_line_ids.filtered(
                  lambda line : line.area == 'PLANEAR')
          )         
          record.crm_diagnostic_line_orientation_ids = self.remove_duplicate_suggest_lines(
              record.crm_diagnostic_line_ids.filtered(
                  lambda line : line.area == 'HACER')
          )
          record.crm_diagnostic_line_business_model_ids = self.remove_duplicate_suggest_lines(
              record.crm_diagnostic_line_ids.filtered(
                  lambda line : line.area == 'VERIFICAR')
          )
          record.crm_diagnostic_line_production_ids = self.remove_duplicate_suggest_lines(
              record.crm_diagnostic_line_ids.filtered(
                  lambda line : line.area == 'ACTUAR')
          )
        
    @api.model
    def remove_duplicate_suggest_lines(self, line_ids):
        # lines without suggestion
        wo_suggestion_lines = line_ids.filtered(lambda x: x.sugerencia in ('', None, False)).ids
        # lines with suggestion
        suggestion_lines = line_ids.filtered(lambda l: l.sugerencia not in ('', None, False))
        suggestions = suggestion_lines.mapped('sugerencia')
        final_suggestions = list(dict.fromkeys(suggestions))
        lines = []
        for suggest in final_suggestions:
            lines.append(suggestion_lines.filtered(lambda s: s.sugerencia == suggest).ids[0])
        wo_suggestion_lines.extend(lines)
        if wo_suggestion_lines:
            return wo_suggestion_lines
        else:
            return self.env['crm.diagnostic.line']


    #def make_chart_bar(self, data):
        #width = 0.5
   #     buf = io.BytesIO()
    #    objects = ['Planear', 'Hacer', 'Verificar', 'Actuar']
     #   x_pos = np.arange(len(objects))
      #  performance = data
        #reference = (65, 60, 15, 10)
      #  plt.figure(figsize =(10, 6))
       # plt.ylim(0, 70)
        #plt.bar(x_pos - width/2, reference, width, alpha=0.5, color='b')
        #plt.bar(x_pos + width/2, performance, width, alpha=0.5, color='g')
        #plt.xticks(x_pos, objects)
        #plt.bar(x_pos, performance, align='center', alpha=0.5)
        #plt.xticks(x_pos, objects)
        #plt.legend(x_pos, ['Nivel esperado', 'Nivel obtenido'])
        #plt.ylabel('Puntaje', fontsize=16)
        #plt.title('Nivel de la Empresa', fontsize=18)
        #plt.savefig(buf, format='png')
        #plt.close()
        #return buf.getvalue()


    def make_chart_bar(self, data):
        width = 0.35
        reference = (65, 60, 15, 10)
        buf = io.BytesIO()
        objects = ['Planear', 'Hacer', 'Verificar', 'Actuar']
        x_pos = np.arange(len(objects))
        performance = data
        plt.figure(figsize =(10, 6))
        yvalues = (0, 70)
        plt.ylim(yvalues, fontsize=16)
        plt.bar(x_pos - width/2, reference, width, align='center', alpha=0.5, color='b')
        plt.bar(x_pos + width/2, performance, width, align='center', alpha=0.5, color='g')
        plt.xticks(x_pos, objects, fontsize=16)
        plt.legend(labels =('Puntaje Maximo', 'Puntaje Obtenido'), loc = 1, fontsize=16)
        plt.ylabel('Puntaje', fontsize=16)
        plt.title('Nivel de la Empresa', fontsize=18)
        plt.savefig(buf, format='png')
        plt.close()
        return buf.getvalue()  

    




    @api.depends('crm_diagnostic_line_ids')
    def _get_chart(self):
        for diagnostic in self:
            planear = 0
            hacer = 0
            verificar = 0
            actuar = 0

            for line in diagnostic.crm_diagnostic_line_innovation_ids:
                planear += int(line.puntaje)
            for line in diagnostic.crm_diagnostic_line_orientation_ids:
                hacer += int(line.puntaje)
            for line in diagnostic.crm_diagnostic_line_business_model_ids:
                verificar += int(line.puntaje)
            for line in diagnostic.crm_diagnostic_line_production_ids:
                actuar += int(line.puntaje)
           
            #data_chart = [planear, hacer, verificar, actuar] 
            
            data2 = self.make_chart_bar([planear, hacer, verificar, actuar])
            #data3 = self.make_chart_bar([planear, hacer, verificar, actuar])
            diagnostic.char_img_bar = base64.b64encode(data2)

            
    @api.model
    def create(self, vals):
        context = dict(self.env.context)
        res = super(CrmDiagnostic, self.with_context(context)).create(vals)
        return res