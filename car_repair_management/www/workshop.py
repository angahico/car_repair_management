import json
import os
import re

import frappe

no_cache = 1

ASSET_BASE = "/assets/car_repair_management/frontend"


def _public_frontend_dir():
	"""Absolute path to the built frontend directory shipped in the app."""
	app_path = frappe.get_app_path("car_repair_management")
	return os.path.join(app_path, "public", "frontend")


def _resolve_assets_from_manifest():
	"""Read Vite's manifest.json and return (js_src, css_href, extra_css).

	Vite >=4 writes the manifest to .vite/manifest.json by default; older
	versions (and some configurations) emit manifest.json at the root of
	outDir. Try both.
	"""
	frontend_dir = _public_frontend_dir()
	candidates = [
		os.path.join(frontend_dir, ".vite", "manifest.json"),
		os.path.join(frontend_dir, "manifest.json"),
	]
	manifest_path = next((p for p in candidates if os.path.exists(p)), None)
	if not manifest_path:
		return None, None, []

	try:
		with open(manifest_path) as f:
			manifest = json.load(f)
	except (OSError, ValueError):
		return None, None, []

	# Find the entry chunk (isEntry: true). Typically src/main.ts.
	entry = None
	for value in manifest.values():
		if isinstance(value, dict) and value.get("isEntry"):
			entry = value
			break
	if not entry:
		return None, None, []

	js_file = entry.get("file")
	css_files = entry.get("css") or []

	js_src = f"{ASSET_BASE}/{js_file}" if js_file else None
	css_href = f"{ASSET_BASE}/{css_files[0]}" if css_files else None
	extra_css = [f"{ASSET_BASE}/{c}" for c in css_files[1:]] if len(css_files) > 1 else []
	return js_src, css_href, extra_css


def _resolve_assets_from_index_html():
	"""Fallback: scrape the built public/frontend/index.html for asset URLs."""
	index_path = os.path.join(_public_frontend_dir(), "index.html")
	if not os.path.exists(index_path):
		return None, None, []

	try:
		with open(index_path) as f:
			html = f.read()
	except OSError:
		return None, None, []

	js_match = re.search(
		r'<script[^>]+src="([^"]+\.js)"',
		html,
	)
	css_matches = re.findall(
		r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+\.css)"',
		html,
	)
	# Also accept attribute order: href before rel
	if not css_matches:
		css_matches = re.findall(
			r'<link[^>]+href="([^"]+\.css)"[^>]+rel="stylesheet"',
			html,
		)

	js_src = js_match.group(1) if js_match else None
	css_href = css_matches[0] if css_matches else None
	extra_css = css_matches[1:] if len(css_matches) > 1 else []
	return js_src, css_href, extra_css


def _resolve_assets():
	js_src, css_href, extra_css = _resolve_assets_from_manifest()
	if js_src:
		return js_src, css_href, extra_css
	return _resolve_assets_from_index_html()


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()

	js_src, css_href, extra_css = _resolve_assets()

	context.boot = {
		"csrf_token": csrf_token,
		"user": frappe.session.user,
		"user_id": frappe.session.user,
	}
	context.js_src = js_src
	context.css_href = css_href
	context.extra_css = extra_css
	context.assets_missing = not js_src
	return context


@frappe.whitelist(allow_guest=True)
def get_context_for_dev():
	if frappe.session.user == "Guest":
		return {}
	return {
		"csrf_token": frappe.sessions.get_csrf_token(),
		"user": frappe.session.user,
	}
