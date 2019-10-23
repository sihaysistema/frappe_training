# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Mis Doctypes"),
			"items": [
				{
					"type": "doctype",
                    "label": _("Config APP"),
					"name": "Config APP",
					"description": _("Doctype de prueba")
				},
				{
					"type": "doctype",
					"label": _("Encuesta APP"),
					"name": "Encuesta APP",
					"description": _("Ejemplo encuesta"),
				}
			]
		},
		# {
		# 	"label": _("Analytics"),
		# 	"icon": "fa fa-table",
		# 	"items": [
		# 		{
		# 			"type": "page",
		# 			"name": "sales-analytics-2",
		# 			"label": _("Sales Analytics 2"),
		# 			"icon": "fa fa-bar-chart",
		# 		}
		# 	]
		# },
		{
			"label": _("Reporte Ventas"),
			"icon": "fa fa-table",
			"items": [
				{
					"type": "report",
					"name": "Ventas",
					"doctype": "Frappe Training",
					"is_query_report": True
				}
			]
		}
	]