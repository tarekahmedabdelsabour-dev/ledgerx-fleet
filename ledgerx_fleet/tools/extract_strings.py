"""List every translatable string used in py/js code and custom field definitions."""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT))


def py_strings(path):
	out = set()
	tree = ast.parse(open(path, encoding="utf-8").read())
	for n in ast.walk(tree):
		if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_" and n.args:
			a = n.args[0]
			if isinstance(a, ast.Constant) and isinstance(a.value, str):
				out.add(a.value)
	return out


JS_RE = re.compile(r"""__\(\s*(["'`])((?:\\.|(?!\1).)*)\1""")


def js_strings(path):
	return {m.group(2).replace('\\"', '"').replace("\\'", "'") for m in JS_RE.finditer(open(path, encoding="utf-8").read())}


def collect():
	found = set()
	for base, _d, files in os.walk(os.path.join(ROOT, "ledgerx_fleet")):
		for f in files:
			p = os.path.join(base, f)
			if f.endswith(".py"):
				found |= py_strings(p)
			elif f.endswith(".js"):
				found |= js_strings(p)
	try:
		import frappe  # noqa: F401
	except ImportError:  # only the data tables of install.py are needed here
		import types

		for name in ("frappe", "frappe.custom", "frappe.custom.doctype", "frappe.custom.doctype.custom_field",
				"frappe.custom.doctype.custom_field.custom_field"):
			sys.modules[name] = types.ModuleType(name)
		sys.modules["frappe.custom.doctype.custom_field.custom_field"].create_custom_fields = lambda *a, **k: None
	from ledgerx_fleet import install

	for fld in install.VEHICLE_FIELDS + install.DRIVER_FIELDS:
		if fld.get("label"):
			found.add(fld["label"])
		if fld["fieldtype"] == "Select":
			found |= {o for o in fld["options"].split("\n") if o}
	for title, _i, items in install._sections():
		found.add(title)
		found |= {label for label, _t, _k in items}
	found |= {"Fleet Management", "Fleet", "Maintenance", "Operations", "Home", "Vehicle Registration"}
	for name, *_r in install.DEFAULT_DOCUMENT_TYPES:
		found.add(name)
	for name, *_r in install.DEFAULT_VEHICLE_TYPES:
		found.add(name)
	return found


if __name__ == "__main__":
	for s in sorted(collect()):
		print(s)
