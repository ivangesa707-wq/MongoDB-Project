"""
Price Listings CRUD routes.
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from bson import ObjectId
from ..extensions import mongo
from ..utils.helpers import utcnow, Pagination, build_sort

price_listings_bp = Blueprint("price_listings", __name__)
COLLECTION = "price_listings"


def _get_col():
    return mongo.db[COLLECTION]


def _lookup_refs():
    farmers = list(mongo.db.farmers.find({}, {"name": 1}).sort("name", 1))
    markets = list(mongo.db.markets.find({}, {"name": 1}).sort("name", 1))
    return farmers, markets


@price_listings_bp.route("/")
def index():
    col = _get_col()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config["ITEMS_PER_PAGE"]
    search = request.args.get("q", "").strip()
    sort_param = request.args.get("sort", "-listing_date")
    filter_market = request.args.get("market", "").strip()
    filter_farmer = request.args.get("farmer", "").strip()

    query = {}
    if search:
        query["$or"] = [
            {"product": {"$regex": search, "$options": "i"}},
            {"unit": {"$regex": search, "$options": "i"}},
        ]
    if filter_market:
        try:
            query["market_id"] = ObjectId(filter_market)
        except Exception:
            pass
    if filter_farmer:
        try:
            query["farmer_id"] = ObjectId(filter_farmer)
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

    # Enrich with farmer and market names
    for doc in docs:
        if doc.get("farmer_id"):
            f = mongo.db.farmers.find_one({"_id": doc["farmer_id"]}, {"name": 1})
            doc["farmer_name"] = f["name"] if f else "—"
        if doc.get("market_id"):
            m = mongo.db.markets.find_one({"_id": doc["market_id"]}, {"name": 1})
            doc["market_name"] = m["name"] if m else "—"

    farmers, markets = _lookup_refs()
    pagination = Pagination(total, page, per_page)
    return render_template(
        "price_listings/index.html",
        listings=docs,
        pagination=pagination,
        search=search,
        sort=sort_param,
        total=total,
        farmers=farmers,
        markets=markets,
        filter_market=filter_market,
        filter_farmer=filter_farmer,
    )


@price_listings_bp.route("/new", methods=["GET", "POST"])
def new():
    farmers, markets = _lookup_refs()

    if request.method == "POST":
        product = request.form.get("product", "").strip()
        market_id = request.form.get("market_id", "").strip()
        farmer_id = request.form.get("farmer_id", "").strip()
        price_str = request.form.get("price", "").strip()
        unit = request.form.get("unit", "").strip()
        listing_date_str = request.form.get("listing_date", "").strip()

        errors = []
        if not product:
            errors.append("Product/crop name is required.")
        if not market_id:
            errors.append("Please select a market.")
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
        if not unit:
            errors.append("Unit is required (e.g. kg, bag, crate).")
        if not listing_date_str:
            errors.append("Listing date is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "price_listings/form.html",
                action="new",
                data=request.form,
                farmers=farmers,
                markets=markets,
            )

        from datetime import datetime
        listing_date = datetime.strptime(listing_date_str, "%Y-%m-%d")

        _get_col().insert_one({
            "product": product,
            "market_id": ObjectId(market_id) if market_id else None,
            "farmer_id": ObjectId(farmer_id) if farmer_id else None,
            "price": float(price_str),
            "unit": unit,
            "listing_date": listing_date,
            "created_at": utcnow(),
        })
        flash(f"Price listing for '{product}' added.", "success")
        return redirect(url_for("price_listings.index"))

    return render_template(
        "price_listings/form.html",
        action="new",
        data={"listing_date": date.today().isoformat()},
        farmers=farmers,
        markets=markets,
    )


@price_listings_bp.route("/<id>")
def view(id):
    doc = _get_col().find_one_or_404({"_id": ObjectId(id)})
    if doc.get("farmer_id"):
        doc["farmer"] = mongo.db.farmers.find_one({"_id": doc["farmer_id"]})
    if doc.get("market_id"):
        doc["market"] = mongo.db.markets.find_one({"_id": doc["market_id"]})
    return render_template("price_listings/view.html", listing=doc)


@price_listings_bp.route("/<id>/edit", methods=["GET", "POST"])
def edit(id):
    col = _get_col()
    doc = col.find_one_or_404({"_id": ObjectId(id)})
    farmers, markets = _lookup_refs()

    if request.method == "POST":
        product = request.form.get("product", "").strip()
        market_id = request.form.get("market_id", "").strip()
        farmer_id = request.form.get("farmer_id", "").strip()
        price_str = request.form.get("price", "").strip()
        unit = request.form.get("unit", "").strip()
        listing_date_str = request.form.get("listing_date", "").strip()

        errors = []
        if not product:
            errors.append("Product/crop name is required.")
        if not market_id:
            errors.append("Please select a market.")
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
        if not unit:
            errors.append("Unit is required.")
        if not listing_date_str:
            errors.append("Listing date is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "price_listings/form.html",
                action="edit",
                data=request.form,
                doc=doc,
                farmers=farmers,
                markets=markets,
            )

        from datetime import datetime
        listing_date = datetime.strptime(listing_date_str, "%Y-%m-%d")

        col.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "product": product,
                "market_id": ObjectId(market_id) if market_id else None,
                "farmer_id": ObjectId(farmer_id) if farmer_id else None,
                "price": float(price_str),
                "unit": unit,
                "listing_date": listing_date,
            }},
        )
        flash(f"Price listing for '{product}' updated.", "success")
        return redirect(url_for("price_listings.view", id=id))

    # Prepare form data with existing values
    form_data = dict(doc)
    if doc.get("listing_date"):
        try:
            form_data["listing_date"] = doc["listing_date"].strftime("%Y-%m-%d")
        except AttributeError:
            pass
    if doc.get("market_id"):
        form_data["market_id"] = str(doc["market_id"])
    if doc.get("farmer_id"):
        form_data["farmer_id"] = str(doc["farmer_id"])

    return render_template(
        "price_listings/form.html",
        action="edit",
        data=form_data,
        doc=doc,
        farmers=farmers,
        markets=markets,
    )


@price_listings_bp.route("/<id>/delete", methods=["POST"])
def delete(id):
    doc = _get_col().find_one_or_404({"_id": ObjectId(id)})
    _get_col().delete_one({"_id": ObjectId(id)})
    flash(f"Price listing for '{doc['product']}' deleted.", "warning")
    return redirect(url_for("price_listings.index"))
