# app.py
# Main Flask app for Istanbul Gasht Store Admin Dashboard.
# Trying to keep things simple and readable so it's easy to follow in an assessment.

import os
from datetime import date, timedelta
from uuid import uuid4

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from sqlalchemy import func

from models import db, Product, AdminUser, Order, ActivityLog


def create_app():
    app = Flask(__name__)

    # Secret key for flash messages etc.
    # For a real deploy I would put this in an env var, but for now it's fine.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-real-deploy")

    # SQLite database file
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///istanbul_gasht_store.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # File upload folder (for product images and avatar)
    upload_folder = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    db.init_app(app)

    # -------------- Helper: log activity --------------

    def log_activity(action_type, description):
        """Just a small helper so I don't repeat this everywhere."""
        entry = ActivityLog(action_type=action_type, description=description)
        db.session.add(entry)
        db.session.commit()

    # Make helper accessible inside views
    app.log_activity = log_activity

    # -------------- Dashboard route --------------

    @app.route("/")
    @app.route("/dashboard")
    def dashboard():
        # KPI: total orders, total revenue, total products
        total_orders = db.session.query(func.count(Order.id)).scalar() or 0
        total_revenue = (
            db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar()
            or 0
        )
        total_products = db.session.query(func.count(Product.id)).scalar() or 0

        # Weekly growth: compare last 7 days vs previous 7 days
        today = date.today()
        current_start = today - timedelta(days=6)
        prev_start = current_start - timedelta(days=7)
        prev_end = current_start - timedelta(days=1)

        current_period_revenue = (
            db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
            .filter(Order.order_date >= current_start)
            .filter(Order.order_date <= today)
            .scalar()
            or 0
        )

        previous_period_revenue = (
            db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
            .filter(Order.order_date >= prev_start)
            .filter(Order.order_date <= prev_end)
            .scalar()
            or 0
        )

        if previous_period_revenue > 0:
            weekly_growth = (
                (current_period_revenue - previous_period_revenue)
                / previous_period_revenue
                * 100
            )
        else:
            # If no previous data, I just show 0 so it does not explode.
            weekly_growth = 0

        # Sales chart: 7-day trend (last 7 days including today)
        chart_labels = []
        chart_data = []

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_label = day.strftime("%b %d")  # e.g. "Nov 18"
            day_revenue = (
                db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
                .filter(Order.order_date == day)
                .scalar()
                or 0
            )
            chart_labels.append(day_label)
            chart_data.append(round(day_revenue, 2))

        # Recent activity feed (last 10)
        recent_activities = (
            ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
        )

        return render_template(
            "dashboard.html",
            total_orders=total_orders,
            total_revenue=total_revenue,
            total_products=total_products,
            weekly_growth=weekly_growth,
            chart_labels=chart_labels,
            chart_data=chart_data,
            recent_activities=recent_activities,
        )

    # -------------- Product CRUD --------------

    @app.route("/products")
    def list_products():
        products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template("products/list.html", products=products)

    @app.route("/products/create", methods=["GET", "POST"])
    def create_product():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            price_raw = request.form.get("price", "").strip()
            category = request.form.get("category", "").strip()
            stock_raw = request.form.get("stock", "").strip()
            description = request.form.get("description", "").strip()

            # simple validation
            if not name or not price_raw or not category or not stock_raw:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("create_product"))

            try:
                price = float(price_raw)
                stock = int(stock_raw)
            except ValueError:
                flash("Price and stock must be valid numbers.", "error")
                return redirect(url_for("create_product"))

            image_file = request.files.get("image")
            image_filename = None

            if image_file and image_file.filename:
                # I'm just saving the file with a random name to avoid collisions.
                ext = os.path.splitext(image_file.filename)[1]
                image_filename = f"{uuid4().hex}{ext}"
                try:
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
                    image_file.save(image_path)
                except Exception:
                    flash("There was a problem saving the image. Try again.", "error")
                    image_filename = None

            product = Product(
                name=name,
                price=price,
                category=category,
                stock=stock,
                description=description,
                image_filename=image_filename,
            )

            db.session.add(product)
            db.session.commit()

            app.log_activity("product_created", f'Product "{product.name}" was created.')

            flash("Product created successfully.", "success")
            return redirect(url_for("list_products"))

        return render_template("products/form.html", product=None)

    @app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
    def edit_product(product_id):
        product = Product.query.get(product_id)
        if not product:
            flash("Product not found.", "error")
            return redirect(url_for("list_products"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            price_raw = request.form.get("price", "").strip()
            category = request.form.get("category", "").strip()
            stock_raw = request.form.get("stock", "").strip()
            description = request.form.get("description", "").strip()

            if not name or not price_raw or not category or not stock_raw:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("edit_product", product_id=product_id))

            try:
                price = float(price_raw)
                stock = int(stock_raw)
            except ValueError:
                flash("Price and stock must be valid numbers.", "error")
                return redirect(url_for("edit_product", product_id=product_id))

            product.name = name
            product.price = price
            product.category = category
            product.stock = stock
            product.description = description

            image_file = request.files.get("image")
            if image_file and image_file.filename:
                ext = os.path.splitext(image_file.filename)[1]
                image_filename = f"{uuid4().hex}{ext}"
                try:
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
                    image_file.save(image_path)
                    product.image_filename = image_filename
                except Exception:
                    flash("There was a problem updating the image.", "error")

            db.session.commit()

            app.log_activity("product_edited", f'Product "{product.name}" was updated.')

            flash("Product updated successfully.", "success")
            return redirect(url_for("list_products"))

        return render_template("products/form.html", product=product)

    @app.route("/products/<int:product_id>/delete", methods=["POST"])
    def delete_product(product_id):
        product = Product.query.get(product_id)
        if not product:
            flash("Product not found.", "error")
            return redirect(url_for("list_products"))

        name = product.name
        try:
            db.session.delete(product)
            db.session.commit()
            app.log_activity("product_deleted", f'Product "{name}" was deleted.')
            flash("Product deleted successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Could not delete this product right now.", "error")

        return redirect(url_for("list_products"))

    # -------------- Admin profile --------------

    @app.route("/profile", methods=["GET", "POST"])
    def edit_profile():
        # For this simple CRM we assume only one admin with id=1.
        admin = AdminUser.query.get(1)
        if not admin:
            # Friendly fallback if the seed didn't create an admin for some reason.
            admin = AdminUser(id=1, name="Admin", email="admin@example.com")
            db.session.add(admin)
            db.session.commit()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()

            if not name or not email:
                flash("Please enter both name and email.", "error")
                return redirect(url_for("edit_profile"))

            admin.name = name
            admin.email = email

            avatar_file = request.files.get("avatar")
            if avatar_file and avatar_file.filename:
                ext = os.path.splitext(avatar_file.filename)[1]
                avatar_filename = f"avatar_{uuid4().hex}{ext}"
                try:
                    avatar_path = os.path.join(
                        app.config["UPLOAD_FOLDER"], avatar_filename
                    )
                    avatar_file.save(avatar_path)
                    admin.avatar_filename = avatar_filename
                except Exception:
                    flash(
                        "There was a problem saving your avatar, so I kept the old one.",
                        "error",
                    )

            db.session.commit()
            app.log_activity("profile_updated", "Admin profile was updated.")
            flash("Profile updated successfully.", "success")
            return redirect(url_for("edit_profile"))

        return render_template("profile.html", admin=admin)

    # -------------- Init DB route for Render (no shell) --------------

    @app.route("/init-db")
    def init_db_route():
        # This route is just to initialize the DB on Render free plan.
        # You can hit it once in the browser, then optionally remove it.
        try:
            db.drop_all()
            db.create_all()

            # Create admin
            admin = AdminUser(
                name="Istanbul Gasht Admin", email="admin@istanbulgasht.com"
            )
            db.session.add(admin)

            # Sample products
            p1 = Product(
                name="Classic Istanbul T-Shirt",
                price=29.99,
                category="T-Shirts",
                stock=50,
                description="Simple white tee with a minimal Istanbul skyline print.",
            )
            p2 = Product(
                name="Bosporus Hoodie",
                price=59.99,
                category="Hoodies",
                stock=20,
                description="Cozy hoodie inspired by Bosporus nights.",
            )
            p3 = Product(
                name="Grand Bazaar Scarf",
                price=19.99,
                category="Accessories",
                stock=100,
                description="Light scarf with patterns inspired by the Grand Bazaar.",
            )
            db.session.add_all([p1, p2, p3])
            db.session.commit()

            # Sample orders (last 7 days)
            today = date.today()
            products = [p1, p2, p3]

            for i in range(7):
                day = today - timedelta(days=i)
                for j in range(i % 3):
                    product = products[j % 3]
                    quantity = j + 1
                    total = product.price * quantity
                    db.session.add(
                        Order(
                            product_id=product.id,
                            quantity=quantity,
                            total_amount=total,
                            order_date=day,
                        )
                    )

            db.session.add(
                ActivityLog(
                    action_type="system_init",
                    description="Database initialized on Render.",
                )
            )
            db.session.commit()

            return "Database initialized successfully on Render."

        except Exception as e:
            # I keep the error message simple so it's understandable.
            return f"Error initializing database: {e}", 500

    # -------------- Serve uploaded files (if needed) --------------

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        # In most cases we can just reference /static/uploads, but this helper is here just in case.
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # -------------- Error handlers --------------

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        # I don't want to expose errors here; just show a friendly message.
        return render_template("errors/500.html"), 500

    return app


# Expose app for gunicorn / Render
app = create_app()

if __name__ == "__main__":
    # Running in debug mode locally to speed things up.
    app.run(debug=True)
