# -*- coding: utf-8 -*-
# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe_training.api import preparar_peticion_banguat


def cada_minuto():
	'''Funcion para prueba, se ejecuta cada minuto '''
	estado = verificar_configuracion('Cada Minuto')
	return estado


def test():
	'''Funcion para prueba, se ejecuta cada Hora '''
	estado = verificar_configuracion('Cada Hora')
	return estado
	# frappe.publish_realtime(event='eval_js', message='alert("{0}")'.format(estado), user=frappe.session.user)


def run_every_ten_mins():
	'''Se ejecuta cada 10 minutos'''
	pass


def all():
	'''Se ejecuta cada 4 minutos'''
	pass


def daily():
	'''Se ejecuta cada 24 horas'''
	estado = verificar_configuracion('Cada dia')
	return


def hourly():
	'''Se ejecuta cada 60 minutos'''
	estado = verificar_configuracion('Cada Hora')
	return


def weekly():
	'''Se ejecuta cada semana'''
	pass


def monthly():
	'''Se ejecuta cada mes'''
	pass


def verificar_configuracion(opt):
	'''Funcion para verificar la configuracion'''
	# Obtiene data del doctype configuracion
	configuracion = frappe.get_doc('Configuracion Tipo Cambio')

	# Si el servicio esta activo
	if configuracion.desactivar_consultas == 0:
		if str(configuracion.frecuencia) == opt:
			# Obtiene el cambio del dia USD
			estado_cambio_dia = preparar_peticion_banguat('1')

			# Obtiene el tipo cambio del dia en base a codigos de moneda
			# tipo_cambio_monedas = preparar_peticion_banguat('6')
			tipo_cambio_monedas = ''

			return estado_cambio_dia, tipo_cambio_monedas
		else:
			# No hara nada
			return
	else:
		return 'Servicio desactivado por usuario'
