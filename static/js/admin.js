/* ===== KSA Bar Admin JS ===== */

// Confirm dialogs are handled inline via onsubmit="return confirm(...)"
// This file provides helpers used in templates.

function toggleForm(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden');
}

function toggleEditRow(id) {
  const el = document.getElementById('edit-' + id);
  if (el) el.classList.toggle('hidden');
}

function toggleEditCat(id) {
  const el = document.getElementById('edit-cat-' + id);
  if (el) el.classList.toggle('hidden');
}
