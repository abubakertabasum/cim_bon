odoo.define('cim.SwitchCompanyMenu', function(require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');

var _t = core._t;


var CompanyMenu = require('web.SwitchCompanyMenu');

CompanyMenu.SwitchCompanyMenu.include({
		
	/**
     * @override
     */
    willStart: function () {
        return session.user_companies ? this._super() : $.Deferred().reject();
    },
	
	
	});


});
