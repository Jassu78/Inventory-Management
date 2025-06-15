import sys
import os
import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QMessageBox, QLabel, QLineEdit, QPushButton,
    QFormLayout, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox,
    QTabWidget, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QStackedWidget, QGroupBox
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

DB_PATH = "inventory.db"


def resource_path(relative_path):
    # Helper for PyInstaller to find resources
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        # Table for operator login
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # Table for goods receiving
        c.execute("""
            CREATE TABLE IF NOT EXISTS goods_receiving (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                supplier_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_of_measurement TEXT NOT NULL,
                rate_per_unit REAL NOT NULL,
                total_rate REAL NOT NULL,
                tax REAL NOT NULL
            )
        """)

        # Table for sales
        c.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_of_measurement TEXT NOT NULL,
                rate_per_unit REAL NOT NULL,
                total_rate REAL NOT NULL,
                tax REAL NOT NULL
            )
        """)

        # Table for product master list
        c.execute("""
            CREATE TABLE IF NOT EXISTS product_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL,
                sku_id TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                product_image_path TEXT,
                product_name TEXT NOT NULL,
                description TEXT,
                tax REAL NOT NULL,
                price REAL NOT NULL,
                default_unit_of_measurement TEXT NOT NULL
            )
        """)
        self.conn.commit()

        # Insert default users if not exists
        c.execute("SELECT COUNT(*) FROM users")
        count = c.fetchone()[0]
        if count == 0:
            # Two operators with simple passwords (hashed passwords recommended for prod)
            users = [
                ("operator1", "password123"),
                ("operator2", "password123")
            ]
            c.executemany("INSERT INTO users (username, password) VALUES (?, ?)", users)
            self.conn.commit()

    def authenticate_user(self, username, password):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        return c.fetchone() is not None

    def insert_goods_receiving(self, data):
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO goods_receiving
            (product_name, supplier_name, quantity, unit_of_measurement, rate_per_unit, total_rate, tax)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["product_name"],
            data["supplier_name"],
            data["quantity"],
            data["unit_of_measurement"],
            data["rate_per_unit"],
            data["total_rate"],
            data["tax"]
        ))
        self.conn.commit()

    def insert_sales(self, data):
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO sales
            (product_name, customer_name, quantity, unit_of_measurement, rate_per_unit, total_rate, tax)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["product_name"],
            data["customer_name"],
            data["quantity"],
            data["unit_of_measurement"],
            data["rate_per_unit"],
            data["total_rate"],
            data["tax"]
        ))
        self.conn.commit()

    def insert_product(self, data):
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO product_master
            (barcode, sku_id, category, subcategory, product_image_path, product_name, description, tax, price, default_unit_of_measurement)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["barcode"],
            data["sku_id"],
            data["category"],
            data["subcategory"],
            data["product_image_path"],
            data["product_name"],
            data["description"],
            data["tax"],
            data["price"],
            data["default_unit_of_measurement"]
        ))
        self.conn.commit()

    def get_all_products(self):
        c = self.conn.cursor()
        c.execute("SELECT id, product_name FROM product_master ORDER BY product_name ASC")
        return c.fetchall()

    def get_product_details(self, product_name):
        c = self.conn.cursor()
        c.execute("SELECT * FROM product_master WHERE product_name = ?", (product_name,))
        return c.fetchone()


class LoginWindow(QWidget):
    def __init__(self, database_manager):
        super().__init__()
        self.db = database_manager
        self.setWindowTitle("Operator Login")
        self.setFixedSize(350, 180)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        self.setLayout(layout)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        layout.addRow("Password:", self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        layout.addRow(self.login_button)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
        if self.db.authenticate_user(username, password):
            self.accept_login(username)
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password")

    def accept_login(self, username):
        self.close()
        self.main_window = MainWindow(self.db, username)
        self.main_window.show()


class GoodsReceivingForm(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.setWindowTitle("Goods Receiving Form")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        self.setLayout(layout)

        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("Product name")
        layout.addRow("Product Name:", self.product_name_input)

        self.supplier_name_input = QLineEdit()
        self.supplier_name_input.setPlaceholderText("Supplier name")
        layout.addRow("Supplier Name:", self.supplier_name_input)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1000000)
        layout.addRow("Quantity:", self.quantity_input)

        self.unit_input = QComboBox()
        self.unit_input.addItems(["pcs", "kg", "liters", "boxes", "packs"])
        layout.addRow("Unit of Measurement:", self.unit_input)

        self.rate_per_unit_input = QDoubleSpinBox()
        self.rate_per_unit_input.setRange(0, 1000000)
        self.rate_per_unit_input.setDecimals(2)
        self.rate_per_unit_input.setPrefix("$ ")
        layout.addRow("Rate per Unit:", self.rate_per_unit_input)

        self.tax_input = QDoubleSpinBox()
        self.tax_input.setRange(0, 100)
        self.tax_input.setDecimals(2)
        self.tax_input.setSuffix(" %")
        layout.addRow("Tax (%):", self.tax_input)

        self.total_rate_label = QLabel("$ 0.00")
        layout.addRow("Total Rate:", self.total_rate_label)

        self.rate_per_unit_input.valueChanged.connect(self.calculate_total)
        self.quantity_input.valueChanged.connect(self.calculate_total)
        self.tax_input.valueChanged.connect(self.calculate_total)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_form)
        layout.addRow(self.submit_button)

    def calculate_total(self):
        quantity = self.quantity_input.value()
        rate_per_unit = self.rate_per_unit_input.value()
        tax = self.tax_input.value()
        subtotal = quantity * rate_per_unit
        total_with_tax = subtotal + (subtotal * tax / 100)
        self.total_rate_label.setText(f"$ {total_with_tax:,.2f}")

    def submit_form(self):
        product_name = self.product_name_input.text().strip()
        supplier_name = self.supplier_name_input.text().strip()
        quantity = self.quantity_input.value()
        unit = self.unit_input.currentText()
        rate_per_unit = self.rate_per_unit_input.value()
        tax = self.tax_input.value()
        total_rate = quantity * rate_per_unit + (quantity * rate_per_unit * tax / 100)

        if not product_name or not supplier_name or quantity <= 0 or rate_per_unit <= 0:
            QMessageBox.warning(self, "Input error", "Please fill in all required fields correctly.")
            return

        data = {
            "product_name": product_name,
            "supplier_name": supplier_name,
            "quantity": quantity,
            "unit_of_measurement": unit,
            "rate_per_unit": rate_per_unit,
            "total_rate": total_rate,
            "tax": tax
        }
        self.db.insert_goods_receiving(data)

        QMessageBox.information(self, "Success", "Goods receiving data saved successfully.")
        self.clear_form()

    def clear_form(self):
        self.product_name_input.clear()
        self.supplier_name_input.clear()
        self.quantity_input.setValue(1)
        self.unit_input.setCurrentIndex(0)
        self.rate_per_unit_input.setValue(0)
        self.tax_input.setValue(0)
        self.total_rate_label.setText("$ 0.00")


class SalesForm(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.setWindowTitle("Sales Form")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        self.setLayout(layout)

        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("Product name")
        layout.addRow("Product Name:", self.product_name_input)

        self.customer_name_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("Customer name")
        layout.addRow("Customer Name:", self.customer_name_input)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1000000)
        layout.addRow("Quantity:", self.quantity_input)

        self.unit_input = QComboBox()
        self.unit_input.addItems(["pcs", "kg", "liters", "boxes", "packs"])
        layout.addRow("Unit of Measurement:", self.unit_input)

        self.rate_per_unit_input = QDoubleSpinBox()
        self.rate_per_unit_input.setRange(0, 1000000)
        self.rate_per_unit_input.setDecimals(2)
        self.rate_per_unit_input.setPrefix("$ ")
        layout.addRow("Rate per Unit:", self.rate_per_unit_input)

        self.tax_input = QDoubleSpinBox()
        self.tax_input.setRange(0, 100)
        self.tax_input.setDecimals(2)
        self.tax_input.setSuffix(" %")
        layout.addRow("Tax (%):", self.tax_input)

        self.total_rate_label = QLabel("$ 0.00")
        layout.addRow("Total Rate:", self.total_rate_label)

        self.rate_per_unit_input.valueChanged.connect(self.calculate_total)
        self.quantity_input.valueChanged.connect(self.calculate_total)
        self.tax_input.valueChanged.connect(self.calculate_total)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_form)
        layout.addRow(self.submit_button)

    def calculate_total(self):
        quantity = self.quantity_input.value()
        rate_per_unit = self.rate_per_unit_input.value()
        tax = self.tax_input.value()
        subtotal = quantity * rate_per_unit
        total_with_tax = subtotal + (subtotal * tax / 100)
        self.total_rate_label.setText(f"$ {total_with_tax:,.2f}")

    def submit_form(self):
        product_name = self.product_name_input.text().strip()
        customer_name = self.customer_name_input.text().strip()
        quantity = self.quantity_input.value()
        unit = self.unit_input.currentText()
        rate_per_unit = self.rate_per_unit_input.value()
        tax = self.tax_input.value()
        total_rate = quantity * rate_per_unit + (quantity * rate_per_unit * tax / 100)

        if not product_name or not customer_name or quantity <= 0 or rate_per_unit <= 0:
            QMessageBox.warning(self, "Input error", "Please fill in all required fields correctly.")
            return

        data = {
            "product_name": product_name,
            "customer_name": customer_name,
            "quantity": quantity,
            "unit_of_measurement": unit,
            "rate_per_unit": rate_per_unit,
            "total_rate": total_rate,
            "tax": tax
        }
        self.db.insert_sales(data)

        QMessageBox.information(self, "Success", "Sales data saved successfully.")
        self.clear_form()

    def clear_form(self):
        self.product_name_input.clear()
        self.customer_name_input.clear()
        self.quantity_input.setValue(1)
        self.unit_input.setCurrentIndex(0)
        self.rate_per_unit_input.setValue(0)
        self.tax_input.setValue(0)
        self.total_rate_label.setText("$ 0.00")


class ProductMasterForm(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.setWindowTitle("Product Master List")
        self.setMinimumWidth(600)
        self.image_path = None
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        self.setLayout(layout)

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barcode")
        layout.addRow("Barcode:", self.barcode_input)

        self.sku_id_input = QLineEdit()
        self.sku_id_input.setPlaceholderText("SKU ID")
        layout.addRow("SKU ID:", self.sku_id_input)

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Category")
        layout.addRow("Category:", self.category_input)

        self.subcategory_input = QLineEdit()
        self.subcategory_input.setPlaceholderText("Subcategory")
        layout.addRow("Subcategory:", self.subcategory_input)

        img_layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setFixedSize(120, 120)
        self.image_label.setStyleSheet("border: 1px solid #ccc; border-radius: 8px;")
        self.image_label.setAlignment(Qt.AlignCenter)
        img_layout.addWidget(self.image_label)

        self.upload_image_button = QPushButton("Upload Image")
        self.upload_image_button.clicked.connect(self.upload_image)
        img_layout.addWidget(self.upload_image_button)

        layout.addRow("Product Image:", img_layout)

        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("Product Name")
        layout.addRow("Product Name:", self.product_name_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description")
        self.description_input.setFixedHeight(80)
        layout.addRow("Description:", self.description_input)

        self.tax_input = QDoubleSpinBox()
        self.tax_input.setRange(0, 100)
        self.tax_input.setDecimals(2)
        self.tax_input.setSuffix(" %")
        layout.addRow("Tax (%):", self.tax_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1000000)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$ ")
        layout.addRow("Price:", self.price_input)

        self.unit_input = QComboBox()
        self.unit_input.addItems(["pcs", "kg", "liters", "boxes", "packs"])
        layout.addRow("Default Unit of Measurement:", self.unit_input)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_form)
        layout.addRow(self.submit_button)

    def upload_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Product Image", "",
                                                  "Image files (*.png *.jpg *.jpeg *.bmp)")
        if filepath:
            pixmap = QPixmap(filepath).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.image_path = filepath

    def submit_form(self):
        barcode = self.barcode_input.text().strip()
        sku_id = self.sku_id_input.text().strip()
        category = self.category_input.text().strip()
        subcategory = self.subcategory_input.text().strip()
        product_name = self.product_name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        tax = self.tax_input.value()
        price = self.price_input.value()
        default_unit = self.unit_input.currentText()

        if not barcode or not sku_id or not category or not subcategory or not product_name or price <= 0:
            QMessageBox.warning(self, "Input error", "Please fill in all required fields correctly.")
            return

        # Save a copy of the image in ./product_images folder for consistency
        saved_img_path = None
        if self.image_path:
            img_folder = Path("product_images")
            img_folder.mkdir(exist_ok=True)
            img_ext = Path(self.image_path).suffix
            img_name = f"{sku_id}{img_ext}"
            saved_img_path = str(img_folder / img_name)
            try:
                with open(self.image_path, "rb") as src_file, open(saved_img_path, "wb") as dest_file:
                    dest_file.write(src_file.read())
            except Exception as e:
                QMessageBox.warning(self, "Image save error", f"Failed to save image: {e}")
                saved_img_path = None

        data = {
            "barcode": barcode,
            "sku_id": sku_id,
            "category": category,
            "subcategory": subcategory,
            "product_image_path": saved_img_path,
            "product_name": product_name,
            "description": description,
            "tax": tax,
            "price": price,
            "default_unit_of_measurement": default_unit
        }

        self.db.insert_product(data)
        QMessageBox.information(self, "Success", "Product master data saved.")
        self.clear_form()

    def clear_form(self):
        self.barcode_input.clear()
        self.sku_id_input.clear()
        self.category_input.clear()
        self.subcategory_input.clear()
        self.image_label.clear()
        self.image_label.setText("No Image")
        self.image_path = None
        self.product_name_input.clear()
        self.description_input.clear()
        self.tax_input.setValue(0)
        self.price_input.setValue(0)
        self.unit_input.setCurrentIndex(0)


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager, username: str):
        super().__init__()
        self.db = db
        self.username = username
        self.setWindowTitle(f"Inventory Management - Operator: {username}")
        self.setFixedSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        welcome_label = QLabel(f"Welcome, {self.username}")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        main_layout.addWidget(welcome_label)

        # Buttons to open forms
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        self.goods_btn = QPushButton("Goods Receiving")
        self.goods_btn.clicked.connect(self.open_goods_receiving)
        self.goods_btn.setMinimumHeight(80)
        buttons_layout.addWidget(self.goods_btn)

        self.sales_btn = QPushButton("Sales Form")
        self.sales_btn.clicked.connect(self.open_sales_form)
        self.sales_btn.setMinimumHeight(80)
        buttons_layout.addWidget(self.sales_btn)

        self.product_master_btn = QPushButton("Product Master List")
        self.product_master_btn.clicked.connect(self.open_product_master)
        self.product_master_btn.setMinimumHeight(80)
        buttons_layout.addWidget(self.product_master_btn)

        # Stacked Widget to hold forms
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Initialize forms but don't add to layout yet
        self.goods_form = GoodsReceivingForm(self.db)
        self.sales_form = SalesForm(self.db)
        self.product_master_form = ProductMasterForm(self.db)

        self.stacked_widget.addWidget(self.goods_form)
        self.stacked_widget.addWidget(self.sales_form)
        self.stacked_widget.addWidget(self.product_master_form)

    def open_goods_receiving(self):
        self.stacked_widget.setCurrentWidget(self.goods_form)

    def open_sales_form(self):
        self.stacked_widget.setCurrentWidget(self.sales_form)

    def open_product_master(self):
        self.stacked_widget.setCurrentWidget(self.product_master_form)


def main():
    app = QApplication(sys.argv)

    # Set application font and style for better appearance
    app.setStyle("Fusion")
    try:
        from PySide6.QtGui import QFontDatabase
        id = QFontDatabase.addApplicationFont(":/fonts/Inter-Regular.ttf")
    except Exception:
        pass  # fallback to default

    db = DatabaseManager()

    login_window = LoginWindow(db)
    login_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

