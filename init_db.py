# init_db.py
# Quick script to create the database and add some example data.

from datetime import date, timedelta
from app import create_app
from models import db, Product, AdminUser, Order, ActivityLog

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create admin user
    admin = AdminUser(name="Istanbul Gasht Admin", email="admin@istanbulgasht.com")
    db.session.add(admin)

    # Some sample products
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

    # Sample orders for the past 14 days
    today = date.today()
    products = [p1, p2, p3]

    for i in range(14):
        day = today - timedelta(days=i)
       
        for j in range(i % 3):
            product = products[j % len(products)]
            quantity = (j + 1)
            total_amount = product.price * quantity
            order = Order(
                product_id=product.id,
                quantity=quantity,
                total_amount=total_amount,
                order_date=day,
            )
            db.session.add(order)

    db.session.commit()

    # Initial activity log
    db.session.add(
        ActivityLog(
            action_type="system_init",
            description="Database initialized with sample data.",
        )
    )
    db.session.commit()

    print("Database initialized with sample data.")
