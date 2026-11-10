import frappe

from ledgerx_fleet.install import ensure_modules


def execute():
	"""Runs before the doctype/workspace sync so the new modules exist when their files are imported."""
	ensure_modules()
