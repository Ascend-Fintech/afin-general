app_name = "delight_shade"
app_title = "Delight Shade"
app_publisher = "Simon Wanyama	"
app_description = "Customizations for Delight Shade"
app_email = "wanyamasp@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "delight_shade",
# 		"logo": "/assets/delight_shade/logo.png",
# 		"title": "Delight Shade",
# 		"route": "/delight_shade",
# 		"has_permission": "delight_shade.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/delight_shade/css/delight_shade.css"
# app_include_js = "/assets/delight_shade/js/delight_shade.js"

# include js, css files in header of web template
# web_include_css = "/assets/delight_shade/css/delight_shade.css"
# web_include_js = "/assets/delight_shade/js/delight_shade.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "delight_shade/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "delight_shade/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "delight_shade.utils.jinja_methods",
# 	"filters": "delight_shade.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "delight_shade.install.before_install"
after_install = "delight_shade.custom_fields.setup_custom_fields"

# Uninstallation
# ------------

# before_uninstall = "delight_shade.uninstall.before_uninstall"
# after_uninstall = "delight_shade.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "delight_shade.utils.before_app_install"
# after_app_install = "delight_shade.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "delight_shade.utils.before_app_uninstall"
# after_app_uninstall = "delight_shade.utils.after_app_uninstall"

# Migration Events
# ----------------
after_migrate = "delight_shade.custom_fields.setup_custom_fields"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "delight_shade.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Quotation": {
		"validate": "delight_shade.sales_commission.distribute_commission"
	},
	"Sales Order": {
		"validate": "delight_shade.sales_commission.distribute_commission"
	},
	"Sales Invoice": {
		"validate": "delight_shade.sales_commission.distribute_commission",
		"on_submit": "delight_shade.sales_commission.make_commission_gl_entries",
		"on_cancel": "delight_shade.sales_commission.cancel_commission_gl_entries"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"delight_shade.tasks.all"
# 	],
# 	"daily": [
# 		"delight_shade.tasks.daily"
# 	],
# 	"hourly": [
# 		"delight_shade.tasks.hourly"
# 	],
# 	"weekly": [
# 		"delight_shade.tasks.weekly"
# 	],
# 	"monthly": [
# 		"delight_shade.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "delight_shade.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "delight_shade.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "delight_shade.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "delight_shade.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["delight_shade.utils.before_request"]
# after_request = ["delight_shade.utils.after_request"]

# Job Events
# ----------
# before_job = ["delight_shade.utils.before_job"]
# after_job = ["delight_shade.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"delight_shade.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

