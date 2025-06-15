# Inventory Management System

---

This is a desktop application for managing inventory, built with Python and PySide6. It provides modules for operator login, goods receiving, sales recording, and maintaining a product master list.

## Features

* **Operator Login:** Secure access for different operators.
* **Goods Receiving:** Record details of incoming products from suppliers.
* **Sales Form:** Log sales transactions with customer information.
* **Product Master List:** Manage product details, including barcode, SKU, category, pricing, and product images.
* **SQLite Database:** All data is stored locally in an SQLite database.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Jassu78/Inventory-Management.git
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\\venv\\Scripts\\activate
    # On macOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install PySide6
    ```

## Usage

1.  **Run the application:**
    ```bash
    python App.py
    ```
    (Replace `App.py` with the actual name of the Python file containing the `main()` function.)

2.  **Login:** Use the default credentials:
    * **Username:** `operator1` or `operator2`
    * **Password:** `password123`

3.  **Navigate:** Use the buttons in the main window to switch between the Goods Receiving, Sales Form, and Product Master List sections.

## Database Schema

The application uses an SQLite database named `inventory.db` with the following tables:

* **`users`**: Stores operator usernames and passwords.
* **`goods_receiving`**: Records incoming inventory details.
* **`sales`**: Stores sales transaction details.
* **`product_master`**: Contains comprehensive product information.

## Project Structure

* `App.py`: (The provided code) Contains all the application logic, including UI setup and database interactions.
* `inventory.db`: The SQLite database file (created automatically on first run).
* `product_images/`: Directory to store uploaded product images.

## Customization

* **Database Path:** The `DB_PATH` variable can be modified to change the database file location.
* **Default Users:** You can modify the `create_tables` method in `DatabaseManager` to add or remove default users.
* **Units of Measurement:** The `QComboBox` items for units can be customized in `GoodsReceivingForm`, `SalesForm`, and `ProductMasterForm`.
