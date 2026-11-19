"""
Markets CRUD routes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from bson import ObjectId
from ..extensions import mongo
from ..utils.helpers import utcnow, Pagination, build_sort

markets_bp = Blueprint("markets", __name__)
COLLECTION = "markets"


def _get_col():
    return mongo.db[COLLECTION]


@markets_bp.route("/")
def index():
    col = _get_col()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config["ITEMS_PER_PAGE"]
    search = request.args.get("q", "").strip()
    sort_param = request.args.get("sort", "name")

    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    sort_field, sort_dir = build_sort(sort_param)
    total = col.count_documents(query)
    docs = list(
        col.find(query)
        .sort(sort_field, sort_dir)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    pagination = Pagination(total, page, per_page)
    return render_template(
        "markets/index.html",
        markets=docs,
        pagination=pagination,
        search=search,
        sort=sort_param,
        total=total,
    )


@markets_bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()

        errors = []
        if not name:
            errors.append("Market name is required.")
        if not location:
            errors.append("Location is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("markets/form.html", action="new", data=request.form)

        _get_col().insert_one({
            "name": name,
            "location": location,
            "description": description,
            "created_at": utcnow(),
        })
        flash(f"Market '{name}' added successfully.", "success")
        return redirect(url_for("markets.index"))

    return render_template("markets/form.html", action="new", data={})


@markets_bp.route("/<id>")
def view(id):
    doc = _get_col().find_one_or_404({"_id": ObjectId(id)})
    listings = list(
        mongo.db.price_listings.find({"market_id": ObjectId(id)}).sort("listing_date", -1).limit(10)
    )
    return render_template("markets/view.html", market=doc, listings=listings)


@markets_bp.route("/<id>/edit", methods=["GET", "POST"])
def edit(id):
    col = _get_col()
    doc = col.find_one_or_404({"_id": ObjectId(id)})

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()

        errors = []
        if not name:
            errors.append("Market name is required.")
        if not location:
            errors.append("Location is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("markets/form.html", action="edit", data=request.form, doc=doc)

        col.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"name": name, "location": location, "description": description}},
        )
        flash(f"Market '{name}' updated.", "success")
        return redirect(url_for("markets.view", id=id))

    return render_template("markets/form.html", action="edit", data=doc, doc=doc)


@markets_bp.route("/<id>/delete", methods=["POST"])
def delete(id):
    doc = _get_col().find_one_or_404({"_id": ObjectId(id)})
    _get_col().delete_one({"_id": ObjectId(id)})
    flash(f"Market '{doc['name']}' deleted.", "warning")
    return redirect(url_for("markets.index"))
