// Copyright (c) 2016, Si Hay Sistema and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ventas"] = {
	// Filtro a utilizar en el front end
	"filters": [{
			fieldname: "tree_type", // Nombre del campo
			label: __("Tree Type"), // Texto a mostrar
			fieldtype: "Select", // Tipo de campo: son los mismos tipos de datos para doctypes
			options: ["Customer Group", "Customer", "Item Group", "Item", "Territory"], // Opciones ya que es un select
			default: "Customer", // Se le puede agregar un valor default
			reqd: 1 // Le podemos especificar si es obligatorio con 1
		},
		{
			fieldname: "doc_type",
			label: __("based_on"),
			fieldtype: "Select",
			options: ["Sales Order", "Delivery Note", "Sales Invoice"],
			default: "Sales Invoice",
			reqd: 1
		},
		{
			fieldname: "value_quantity",
			label: __("Value Or Qty"),
			fieldtype: "Select",
			options: [{
					"value": "Value",
					"label": __("Value")
				},
				{
					"value": "Quantity",
					"label": __("Quantity")
				},
			],
			default: "Value",
			reqd: 1
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_start_date"),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_end_date"),
			reqd: 1
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "range",
			label: __("Range"),
			fieldtype: "Select",
			options: [{
					"value": "Weekly",
					"label": __("Weekly")
				},
				{
					"value": "Monthly",
					"label": __("Monthly")
				},
				{
					"value": "Quarterly",
					"label": __("Quarterly")
				},
				{
					"value": "Yearly",
					"label": __("Yearly")
				}
			],
			default: "Monthly",
			reqd: 1
		}
	],
	// Renderiza la animacion de hacer check
	after_datatable_render: function (datatable_obj) {
		$(datatable_obj.wrapper).find(".dt-row-0").find('input[type=checkbox]').click();
	},
	// Opciones de datatable encargador de generar tablas en Frappe. Documentacion aqui: https://frappe.io/datatable
	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true,
			events: {
				onCheckRow: function (data) {
					row_name = data[2].content;
					length = data.length;

					var tree_type = frappe.query_report.filters[0].value;

					if (tree_type == "Customer") {
						row_values = data.slice(4, length - 1).map(function (column) {
							return column.content;
						})
					} else if (tree_type == "Item") {
						row_values = data.slice(5, length - 1).map(function (column) {
							return column.content;
						})
					} else {
						row_values = data.slice(3, length - 1).map(function (column) {
							return column.content;
						})
					}

					entry = {
						'name': row_name,
						'values': row_values
					}

					let raw_data = frappe.query_report.chart.data;
					let new_datasets = raw_data.datasets;

					var found = false;

					for (var i = 0; i < new_datasets.length; i++) {
						if (new_datasets[i].name == row_name) {
							found = true;
							new_datasets.splice(i, 1);
							break;
						}
					}

					if (!found) {
						new_datasets.push(entry);
					}

					let new_data = {
						labels: raw_data.labels,
						datasets: new_datasets
					}

					setTimeout(() => {
						frappe.query_report.chart.update(new_data)
					}, 500)


					setTimeout(() => {
						frappe.query_report.chart.draw(true);
					}, 1000)

					frappe.query_report.raw_chart_data = new_data;
				},
			}
		})
	},
}