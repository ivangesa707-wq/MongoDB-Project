"""
Records (transactions) CRUD routes.
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from bson import ObjectId
from ..extensions import mongo
from ..utils.helpers import utcnow, Pagination, build_sort

records_bp = Blueprint("records", __name__)
COLLECTION = "records"

TRANSACTION_TYPES = [
    "Sale", "Purchase", "Transfer", "Return", "Inspection", "Other"
]


def _get_col():
    return mongo.db[COLLECTION]


def _lookup_refs():
    buyers = list(mongo.db.buyers.find({}, {"name": 1}).sort("name", 1))
    farmers = list(mongo.db.farmers.find({}, {"name": 1}).sort("name", 1))
    markets = list(mongo.db.markets.find({}, {"name": 1}).sort("name", 1))
    return buyers, farmers, markets


@records_bp.route("/")
def index():
    col = _get_col()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config["ITEMS_PER_PAGE"]
    search = request.args.get("q", "").strip()
    sort_param = request.args.get("sort", "-date")
    filter_type = request.args.get("type", "").strip()
    filter_market = request.args.get("market", "").strip()

    query = {}
    if search:
        query["$or"] = [
            {"product": {"$regex": search, "$options": "i"}},
            {"transaction_type": {"$regex": search, "$options": "i"}},
        ]
    if filter_type:
        query["transaction_type"] = filter_type
    if filter_market:
        try:
            query["market_id"] = ObjectId(filter_market)
        except Exception:
            pass

    sort_field, sort_dir = build_sort(sort_param)
    total = col.count_documents(query)
    docs = list(
        col.find(query)
        .sort(sort_field, sort_dir)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    # Enrich references
    for doc in docs:
        if doc.get("buyer_id"):
            b = mongo.db.buyers.find_one({"_id": doc["buyer_id"]}, {"name": 1})
            doc["buyer_name"] = b["name"] if b else "—"
        if doc.get("farmer_id"):
            f = mongo.db.farmers.find_one({"_id": doc["farmer_id"]}, {"name": 1})
            doc["farmer_name"] = f["name"] if f else "—"
        if doc.get("market_id"):
            m = mongo.db.markets.find_one({"_id": doc["market_id"]}, {"name": 1})
            doc["market_name"] = m["name"] if m else "—"

    markets = list(mongo.db.markets.find({}, {"name": 1}).sort("name", 1))
    pagination = Pagination(total, page, per_page)
    return render_template(
        "records/index.html",
        records=docs,
        pagination=pagination,
        search=search,
        sort=sort_param,
        total=total,
        transaction_types=TRANSACTION_TYPES,
        filter_type=filter_type,
        filter_market=filter_market,
        markets=markets,
    )


@records_bp.route("/new", methods=["GET", "POST"])
def new():
    buyers, farmers, markets = _lookup_refs()

    if request.method == "POST":
        transaction_type = request.form.get("transaction_type", "").strip()
        buyer_id = request.form.get("buyer_id", "").strip()
        farmer_id = request.form.get("farmer_id", "").strip()
        product = request.form.get("product", "").strip()
        quantity_str = request.form.get("quantity", "").strip()
        price_str = request.form.get("price", "").strip()
        market_id = request.form.get("market_id", "").strip()
        date_str = request.form.get("date", "").strip()
        notes = request.form.get("notes", "").strip()

        errors = []
        if not transaction_type:
            errors.append("Transaction type is required.")
        if not product:
            errors.append("Product is required.")
        if not quantity_str:
            errors.append("Quantity is required.")
        else:
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    errors.append("Quantity must be greater than zero.")
            except ValueError:
                errors.append("Quantity must be a valid number.")
                quantity = 0
        if not price_str:
            errors.append("Price is required.")
        else:
            try:
                price = float(price_str)
                if price < 0:
                    errors.append("Price cannot be negative.")
            except ValueError:
                errors.append("Price must be a valid number.")
                price = 0
        if not date_str:
            errors.append("Date is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "records/form.html",
                action="new",
                data=request.form,
                buyers=buyers,
                farmers=farmers,
                markets=markets,
                transaction_types=TRANSACTION_TYPES,
            )

        from datetime import datetime
        rec_date = datetime.strptime(date_str, "%Y-%m-%d")

        _get_col().insert_one({
            "transaction_type": transaction_type,
            "buyer_id": ObjectId(buyer_id) if buyer_id else None,
            "farmer_id": ObjectId(farmer_id) if farmer_id else None,
            "product": product,
            "quantity": float(quantity_str),
            "price": float(price_str),
            "market_id": ObjectId(market_id) if market_id else None,
            "date": rec_date,
            "notes": notes,
            "created_at": utcnow(),
        })
        flash("Record added successfully.", "success")
        return redirect(url_for("records.index"))

    return render_template(
        "records/form.html",
        action="new",
        data={"date": date.today().isoformat()},
        buyers=buyers,
        farmers=farmers,
        markets=markets,
        transaction_types=TRANSACTION_TYPES,
    )


@records_bp.route("/<id>")
def view(id):
    doc = _get_col().find_one_or_404({"_id": ObjectId(id)})
    if doc.get("buyer_id"):
        doc["buyer"] = mongo.db.buyers.find_one({"_id": doc["buyer_id"]})
    if doc.get("farmer_id"):
        doc["farmer"] = mongo.db.farmers.find_one({"_id": doc["farmer_id"]})
    if doc.get("market_id"):
        doc["market"] = mongo.db.markets.find_one({"_id": doc["market_id"]})
    return render_template("records/view.html", record=doc)


@records_bp.route("/<id>/edit", methods=["GET", "POST"])
def edit(id):
    col = _get_col()
    doc = col.find_one_or_404({"_id": ObjectId(id)})
    buyers, farmers, markets = _lookup_refs()

    if request.method == "POST":
        transaction_type = request.form.get("transaction_type", "").strip()
        buyer_id = request.form.get("buyer_id", "").strip()
        farmer_id = request.form.get("farmer_id", "").strip()
        product = request.form.get("product", "").strip()
        quantity_str = request.form.get("quantity", "").strip()
        price_str = request.form.get("price", "").strip()
        market_id = request.form.get("market_id", "").strip()
        date_str = request.form.get("date", "").strip()
        notes = request.form.get("notes", "").strip()

        errors = []
        if not transaction_type:
            errors.append("Transaction type is required.")
        if not product:
            errors.append("Product is required.")
        if not quantity_str:
            errors.append("Quantity is required.")
        else:
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    errors.append("Quantity must be greater than zero.")
            except ValueError:
                errors.append("Quantity must be a valid number.")
                quantity = 0
        if not price_str:
            errors.append("Price is required.")
        else:
            try:
                price = float(price_str)
                if price < 0:
                    errors.append("Price cannot be negative.")
            except ValueError:
                errors.append("Price must be a valid number.")
                price = 0
        if not date_str:
            errors.append("Date is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "records/form.html",
                action="edit",
                data=request.form,
                doc=doc,
                buyers=buyers,
                farmers=farmers,
                markets=markets,
                transaction_types=TRANSACTION_TYPES,
            )

        from datetime import datetime
        rec_date = datetime.strptime(date_str, "%Y-%m-%d")

        col.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "transaction_type": transaction_type,
                "buyer_id": ObjectId(buyer_id) if buyer_id else None,
                "farmer_id": ObjectId(farmer_id) if farmer_id else None,
                "product": product,
                "quantity": float(quantity_str),
                "price": float(price_str),
                "market_id": ObjectId(market_id) if market_id else None,
                "date": rec_date,
                "notes": notes,
            }},
        )
        flash("Record updated successfully.", "success")
        return redirect(url_for("records.view", id=id))

    # Prepare form data
    form_data = dict(doc)
    if doc.get("date"):
        try:
            form_data["date"] = doc["date"].strftime("%Y-%m-%d")
        except AttributeError:
            pass
    for field in ("buyer_id", "farmer_id", "market_id"):
        if doc.get(field):
            form_data[field] = str(doc[field])

    return render_template(
        "records/form.html",
        action="edit",
        data=form_data,
        doc=doc,
        buyers=buyers,
        farmers=farmers,
        markets=markets,
        transaction_types=TRANSACTION_TYPES,
    )


@records_bp.route("/<id>/delete", methods=["POST"])
def delete(id):
    doc = _get_col().find_one_or_404({"_id": ObjectId(id)})
    _get_col().delete_one({"_id": ObjectId(id)})
    flash("Record deleted.", "warning")
    return redirect(url_for("records.index"))
