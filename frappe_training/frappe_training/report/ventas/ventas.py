# Copyright (c) 2013, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, scrub
from frappe.utils import getdate, flt, add_to_date, add_days
from six import iteritems
from erpnext.accounts.utils import get_fiscal_year


def execute(filters=None):
	'''Funcion principal para ser ejecutada'''

	# Retorna una instancia de la clase Analytics pasando por argumentos los filtros creandos en JS
	# y Ejecuta la funcion run misma de la clase Analytics
	return Analytics(filters).run()


# Clase encargada de obtener y procesar data
class Analytics(object):
	def __init__(self, filters=None):
		'''Constructor de la clase'''
		self.filters = frappe._dict(filters or {})  # Asigna los valores obtenido de los filtros JS a un diccionario, si no hay data creara un diccionario vacio
		# Similar a operador terniario: SI el doctype seleccionado existe dentro de las opciones escogera
		# transaction_date sino posting_date
		self.date_field = 'transaction_date' \
			if self.filters.doc_type in ['Sales Order', 'Purchase Order'] else 'posting_date'
		# Lista con meses
		self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		self.get_period_date_ranges()

	def run(self):
		'''Funcion principal de la clase'''
		self.get_columns()  # Obtener columnas
		self.get_data()  # Obtener data
		self.get_chart_data()  # Preconfigurar graficas a mostrar
		return self.columns, self.data , None, self.chart

	def get_columns(self):
		'''Funcion encargada de crear las columnas'''
		self.columns =[{
				"label": _(self.filters.tree_type + " ID"),
				"options": self.filters.tree_type,
				"fieldname": "entity",
				"fieldtype": "Link",
				"width": 140
			}]
		if self.filters.tree_type in ["Customer", "Supplier", "Item"]:
			self.columns.append({
				"label": _(self.filters.tree_type + " Name"),
				"fieldname": "entity_name",
				"fieldtype": "Data",
				"width": 140
			})

		if self.filters.tree_type == "Item":
			self.columns.append({
				"label": _("UOM"),
				"fieldname": 'stock_uom',
				"fieldtype": "Link",
				"options": "UOM",
				"width": 100
			})

		for end_date in self.periodic_daterange:
			period = self.get_period(end_date)
			self.columns.append({
				"label": _(period),
				"fieldname": scrub(period),
				"fieldtype": "Float",
				"width": 120
			})

		self.columns.append({
			"label": _("Total"),
			"fieldname": "total",
			"fieldtype": "Float",
			"width": 120
		})

	def get_data(self):
		'''Funcion encargada de obtener la data'''
		if self.filters.tree_type in ["Customer", "Supplier"]:
			self.get_sales_transactions_based_on_customers_or_suppliers()
			self.get_rows()

		elif self.filters.tree_type == 'Item':
			self.get_sales_transactions_based_on_items()
			self.get_rows()

		elif self.filters.tree_type in ["Customer Group", "Supplier Group", "Territory"]:
			self.get_sales_transactions_based_on_customer_or_territory_group()
			self.get_rows_by_group()

		elif self.filters.tree_type == 'Item Group':
			self.get_sales_transactions_based_on_item_group()
			self.get_rows_by_group()

	def get_sales_transactions_based_on_customers_or_suppliers(self):
		'''Funcion encargada de obtener transacciones basadas en cliente o proveedores'''

		if self.filters["value_quantity"] == 'Value':
			value_field = "base_net_total as value_field"
		else:
			value_field = "total_qty as value_field"

		if self.filters.tree_type == 'Customer':
			entity = "customer as entity"
			entity_name = "customer_name as entity_name"
		else:
			entity = "supplier as entity"
			entity_name = "supplier_name as entity_name"

		self.entries = frappe.get_all(self.filters.doc_type,
			fields=[entity, entity_name, value_field, self.date_field],
			filters = {
				"docstatus": 1,
				"company": self.filters.company,
				self.date_field: ('between', [self.filters.from_date, self.filters.to_date])
			}
		)

		self.entity_names = {}
		for d in self.entries:
			self.entity_names.setdefault(d.entity, d.entity_name)

	def get_sales_transactions_based_on_items(self):
		'''Funcion encargada de obtener transacciones basadas en items'''

		if self.filters["value_quantity"] == 'Value':
			value_field = 'base_amount'
		else:
			value_field = 'stock_qty'

		self.entries = frappe.db.sql("""
			select i.item_code as entity, i.item_name as entity_name, i.stock_uom, i.{value_field} as value_field, s.{date_field}
			from `tab{doctype} Item` i , `tab{doctype}` s
			where s.name = i.parent and i.docstatus = 1 and s.company = %s
			and s.{date_field} between %s and %s
		"""
		.format(date_field=self.date_field, value_field = value_field, doctype=self.filters.doc_type),
		(self.filters.company, self.filters.from_date, self.filters.to_date), as_dict=1)

		self.entity_names = {}
		for d in self.entries:
			self.entity_names.setdefault(d.entity, d.entity_name)

	def get_sales_transactions_based_on_customer_or_territory_group(self):
		'''Funcion encargada de obtener transacciones en base a cliente o grupo'''

		if self.filters["value_quantity"] == 'Value':
			value_field = "base_net_total as value_field"
		else:
			value_field = "total_qty as value_field"

		if self.filters.tree_type == 'Customer Group':
			entity_field = 'customer_group as entity'
		elif self.filters.tree_type == 'Supplier Group':
			entity_field = "supplier as entity"
			self.get_supplier_parent_child_map()
		else:
			entity_field = "territory as entity"

		self.entries = frappe.get_all(self.filters.doc_type,
			fields=[entity_field, value_field, self.date_field],
			filters = {
				"docstatus": 1,
				"company": self.filters.company,
				self.date_field: ('between', [self.filters.from_date, self.filters.to_date])
			}
		)
		self.get_groups()

	def get_sales_transactions_based_on_item_group(self):
		'''Funcion encarga de obtener trasacciones en base de grupo de items'''

		if self.filters["value_quantity"] == 'Value':
			value_field = "base_amount"
		else:
			value_field = "qty"

		self.entries = frappe.db.sql("""
			select i.item_group as entity, i.{value_field} as value_field, s.{date_field}
			from `tab{doctype} Item` i , `tab{doctype}` s
			where s.name = i.parent and i.docstatus = 1 and s.company = %s
			and s.{date_field} between %s and %s
		""".format(date_field=self.date_field, value_field = value_field, doctype=self.filters.doc_type),
		(self.filters.company, self.filters.from_date, self.filters.to_date), as_dict=1)

		self.get_groups()

	def get_rows(self):
		'''Funcion encargada de obtener filas'''
		self.data=[]
		self.get_periodic_data()

		for entity, period_data in iteritems(self.entity_periodic_data):
			row = {
				"entity": entity,
				"entity_name": self.entity_names.get(entity)
			}
			total = 0
			for end_date in self.periodic_daterange:
				period = self.get_period(end_date)
				amount = flt(period_data.get(period, 0.0))
				row[scrub(period)] = amount
				total += amount

			row["total"] = total

			if self.filters.tree_type == "Item":
				row["stock_uom"] = period_data.get("stock_uom")

			self.data.append(row)

	def get_rows_by_group(self):
		self.get_periodic_data()
		out = []

		for d in reversed(self.group_entries):
			row = {
				"entity": d.name,
				"indent": self.depth_map.get(d.name)
			}
			total = 0
			for end_date in self.periodic_daterange:
				period = self.get_period(end_date)
				amount = flt(self.entity_periodic_data.get(d.name, {}).get(period, 0.0))
				row[scrub(period)] = amount
				if d.parent:
					self.entity_periodic_data.setdefault(d.parent, frappe._dict()).setdefault(period, 0.0)
					self.entity_periodic_data[d.parent][period] += amount
				total += amount
			row["total"] = total
			out = [row] + out
		self.data = out

	def get_periodic_data(self):
		self.entity_periodic_data = frappe._dict()

		for d in self.entries:
			if self.filters.tree_type == "Supplier Group":
				d.entity = self.parent_child_map.get(d.entity)
			period = self.get_period(d.get(self.date_field))
			self.entity_periodic_data.setdefault(d.entity, frappe._dict()).setdefault(period, 0.0)
			self.entity_periodic_data[d.entity][period] += flt(d.value_field)

			if self.filters.tree_type == "Item":
				self.entity_periodic_data[d.entity]['stock_uom'] = d.stock_uom

	def get_period(self, posting_date):
		if self.filters.range == 'Weekly':
			period = "Week " + str(posting_date.isocalendar()[1]) + " " + str(posting_date.year)
		elif self.filters.range == 'Monthly':
			period = str(self.months[posting_date.month - 1]) + " " + str(posting_date.year)
		elif self.filters.range == 'Quarterly':
			period = "Quarter " + str(((posting_date.month-1)//3)+1) +" " + str(posting_date.year)
		else:
			year = get_fiscal_year(posting_date, company=self.filters.company)
			period = str(year[0])
		return period

	def get_period_date_ranges(self):
		'''Funcion encargada de obtener el rango entre periodos'''
		from dateutil.relativedelta import relativedelta, MO
		from_date, to_date = getdate(self.filters.from_date), getdate(self.filters.to_date)

		increment = {
			"Monthly": 1,
			"Quarterly": 3,
			"Half-Yearly": 6,
			"Yearly": 12
		}.get(self.filters.range, 1)

		if self.filters.range in ['Monthly', 'Quarterly']:
			from_date = from_date.replace(day = 1)
		elif self.filters.range == "Yearly":
			from_date = get_fiscal_year(from_date)[1]
		else:
			from_date = from_date + relativedelta(from_date, weekday=MO(-1))

		self.periodic_daterange = []
		for dummy in range(1, 53):
			if self.filters.range == "Weekly":
				period_end_date = add_days(from_date, 6)
			else:
				period_end_date = add_to_date(from_date, months=increment, days=-1)

			if period_end_date > to_date:
				period_end_date = to_date

			self.periodic_daterange.append(period_end_date)

			from_date = add_days(period_end_date, 1)
			if period_end_date == to_date:
				break

	def get_groups(self):
		if self.filters.tree_type == "Territory":
			parent = 'parent_territory'
		if self.filters.tree_type == "Customer Group":
			parent = 'parent_customer_group'
		if self.filters.tree_type == "Item Group":
			parent = 'parent_item_group'
		if self.filters.tree_type == "Supplier Group":
			parent = 'parent_supplier_group'

		self.depth_map = frappe._dict()

		self.group_entries = frappe.db.sql("""select name, lft, rgt , {parent} as parent
			from `tab{tree}` order by lft"""
			.format(tree=self.filters.tree_type, parent=parent), as_dict=1)

		for d in self.group_entries:
			if d.parent:
				self.depth_map.setdefault(d.name, self.depth_map.get(d.parent) + 1)
			else:
				self.depth_map.setdefault(d.name, 0)

	def get_supplier_parent_child_map(self):
		self.parent_child_map = frappe._dict(frappe.db.sql(""" select name, supplier_group from `tabSupplier`"""))

	def get_chart_data(self):
		length = len(self.columns)

		if self.filters.tree_type in ["Customer", "Supplier"]:
			labels = [d.get("label") for d in self.columns[2:length - 1]]
		elif self.filters.tree_type == "Item":
			labels = [d.get("label") for d in self.columns[3:length - 1]]
		else:
			labels = [d.get("label") for d in self.columns[1:length-1]]
		self.chart = {
			"data": {
				'labels': labels,
				'datasets':[]
			},
			"type": "line"
		}