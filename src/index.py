import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from varasto import Varasto

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# In-memory storage for warehouses: {id: {"name": str, "varasto": Varasto}}
warehouses = {}


def _create_warehouse_dict(name, varasto):
    return {"name": name, "varasto": varasto}


@app.route("/")
def home():
    return render_template("index.html", warehouses=warehouses)


@app.route("/warehouse/create", methods=["POST"])
def create_warehouse():
    name = request.form.get("name", "").strip()
    capacity = request.form.get("capacity", type=float)

    if not name:
        flash("Warehouse name is required.", "error")
        return redirect(url_for("home"))

    if capacity is None or capacity <= 0:
        flash("Capacity must be a positive number.", "error")
        return redirect(url_for("home"))

    warehouse_id = str(uuid.uuid4())
    warehouses[warehouse_id] = _create_warehouse_dict(name, Varasto(capacity))

    flash(f"Warehouse '{name}' created successfully!", "success")
    return redirect(url_for("warehouse_detail", warehouse_id=warehouse_id))


@app.route("/warehouse/<warehouse_id>")
def warehouse_detail(warehouse_id):
    if warehouse_id not in warehouses:
        flash("Warehouse not found.", "error")
        return redirect(url_for("home"))

    return render_template(
        "warehouse.html",
        warehouse=warehouses[warehouse_id],
        warehouse_id=warehouse_id,
        tab="main"
    )


@app.route("/warehouse/<warehouse_id>/settings")
def warehouse_settings(warehouse_id):
    if warehouse_id not in warehouses:
        flash("Warehouse not found.", "error")
        return redirect(url_for("home"))

    return render_template(
        "warehouse.html",
        warehouse=warehouses[warehouse_id],
        warehouse_id=warehouse_id,
        tab="settings"
    )


@app.route("/warehouse/<warehouse_id>/add", methods=["POST"])
def add_stock(warehouse_id):
    if warehouse_id not in warehouses:
        flash("Warehouse not found.", "error")
        return redirect(url_for("home"))

    amount = request.form.get("amount", type=float)
    if amount is None or amount <= 0:
        flash("Amount must be a positive number.", "error")
        return redirect(url_for("warehouse_detail", warehouse_id=warehouse_id))

    warehouse = warehouses[warehouse_id]
    warehouse["varasto"].lisaa_varastoon(amount)
    flash(f"Added {amount} units to storage.", "success")
    return redirect(url_for("warehouse_detail", warehouse_id=warehouse_id))


@app.route("/warehouse/<warehouse_id>/remove", methods=["POST"])
def remove_stock(warehouse_id):
    if warehouse_id not in warehouses:
        flash("Warehouse not found.", "error")
        return redirect(url_for("home"))

    amount = request.form.get("amount", type=float)
    if amount is None or amount <= 0:
        flash("Amount must be a positive number.", "error")
        return redirect(url_for("warehouse_detail", warehouse_id=warehouse_id))

    warehouse = warehouses[warehouse_id]
    removed = warehouse["varasto"].ota_varastosta(amount)
    flash(f"Removed {removed} units from storage.", "success")
    return redirect(url_for("warehouse_detail", warehouse_id=warehouse_id))


@app.route("/warehouse/<warehouse_id>/capacity", methods=["POST"])
def update_capacity(warehouse_id):
    if warehouse_id not in warehouses:
        flash("Warehouse not found.", "error")
        return redirect(url_for("home"))

    new_capacity = request.form.get("new_capacity", type=float)
    if new_capacity is None or new_capacity <= 0:
        flash("Capacity must be a positive number.", "error")
        settings_url = url_for("warehouse_settings", warehouse_id=warehouse_id)
        return redirect(settings_url)

    _apply_capacity_update(warehouse_id, new_capacity)
    return redirect(url_for("warehouse_settings", warehouse_id=warehouse_id))


def _apply_capacity_update(warehouse_id, new_capacity):
    warehouse = warehouses[warehouse_id]
    current_stock = warehouse["varasto"].saldo
    # Create new Varasto with updated capacity (respects class invariants)
    new_stock = min(current_stock, new_capacity)
    warehouse["varasto"] = Varasto(new_capacity, new_stock)
    flash(f"Capacity updated to {new_capacity} units.", "success")


@app.route("/warehouse/<warehouse_id>/delete", methods=["POST"])
def delete_warehouse(warehouse_id):
    if warehouse_id not in warehouses:
        flash("Warehouse not found.", "error")
        return redirect(url_for("home"))

    name = warehouses[warehouse_id]["name"]
    del warehouses[warehouse_id]
    flash(f"Warehouse '{name}' has been deleted.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
