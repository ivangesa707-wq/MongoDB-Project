"""
Main / dashboard route.
"""
from flask import Blueprint, render_template
from ..extensions import mongo

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    db = mongo.db
    stats = {
        "buyers": db.buyers.count_documents({}),
        "farmers": db.farmers.count_documents({}),
        "markets": db.markets.count_documents({}),
        "price_listings": db.price_listings.count_documents({}),
        "records": db.records.count_documents({}),
    }

    # Recent price listings (last 5)
    recent_prices = list(
        db.price_listings.find().sort("listing_date", -1).limit(5)
    )

    # Recent records/transactions (last 5)
    recent_records = list(
        db.records.find().sort("date", -1).limit(5)
    )

    return render_template(
        "index.html",
        stats=stats,
        recent_prices=recent_prices,
        recent_records=recent_records,
    )
