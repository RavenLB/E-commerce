# E-commerce API

This is a RESTful API for an e-commerce application built with Flask, SQLAlchemy, and Stripe for payment processing. The API allows users to manage products, their shopping cart, and orders, while also providing admin functionalities for managing products and orders.

## Features

- User authentication and authorization using JWT
- Product management 
- Shopping cart functionality
- Order management
- Payment processing with Stripe
- Admin functionalities for managing products and orders
- Search and filtering capabilities for products

## Technologies Used

- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Marshmallow for serialization
- SQLAlchemy for ORM
- Stripe for payment processing
- SQLite for the database

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/RavenLB/E-commerce.git
   cd ecommerce-api
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install the required packages:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database:**

   ```bash
   flask init-db
   ```

6. **Create an admin user (optional):**

   ```bash
   flask create-admin
   ```

## Usage

1. **Run the application:**

   ```bash
   python run.py
   ```

2. **API Endpoints:**

   - **Authentication:**
     - `POST /auth/register`: Register a new user
     - `POST /auth/login`: Log in and receive a JWT

   - **Products:**
     - `GET /products`: Get all products
       - **Query Parameters**:
         - `search`: Search for products by name or description
         - `category`: Filter products by category
         - `min_price`: Filter products with a minimum price
         - `max_price`: Filter products with a maximum price
         - `sort`: Sort products by `name`, `price`, or `created_at`
         - `order`: Sort order, either `asc` or `desc`
     - `POST /products`: Create a new product (Admin only)
     - `PUT /products/<id>`: Update a product (Admin only)
     - `DELETE /products/<id>`: Delete a product (Admin only)

   - **Cart:**
     - `GET /cart`: Get the user's cart
     - `POST /cart`: Add an item to the cart
     - `PUT /cart/<item_id>`: Update a cart item
     - `DELETE /cart/<item_id>`: Remove an item from the cart
     - `POST /cart/checkout`: Checkout and create an order

   - **Orders:**
     - `GET /orders`: Get all orders for the user
     - `GET /orders/<id>`: Get a specific order
     - `POST /orders/<id>/cancel`: Cancel an order (only if pending)

   - **Admin:**
     - `GET /admin/orders`: Get all orders (Admin only)
     - `PUT /admin/orders/<id>/status`: Update order status (Admin only)


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

