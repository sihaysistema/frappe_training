// Copyright (c) 2019, Si Hay Sistema and contributors
// For license information, please see license.txt

frappe.ui.form.on('Configuracion Tipo Cambio', {
	refresh: function (frm) {
		console.log('Se refreso form');
		frm.page.set_secondary_action(__("Tipo Cambio GTQ"), function () {
			frappe.call({
				method: "frappe_training.api.preparar_peticion_banguat",
				args: {
					opt: '1'
				},
				freeze: true,
				freeze_message: __("Consultado tipo cambio del dia..."),
				callback: function (r) {
					if (!r.exc) {
						clearInterval(frm.page["interval"]);
						// frm.page.set_indicator(__('Importacion Exitosa!!'), 'blue');
						// create_reset_button(frm);
						console.log(r.message)
					}
				}
			});
		}).addClass('btn btn-primary');
	}
});