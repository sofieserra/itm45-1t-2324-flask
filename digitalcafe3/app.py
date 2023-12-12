from flask import Flask,redirect,flash,url_for
from flask import render_template
from flask import request
from flask import session
import database as db
import authentication
import logging
import ordermanagement as om

app = Flask(__name__)

# Set the secret key to some random bytes. 
# Keep this really secret!
app.secret_key = b's@g@d@c0ff33!'

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.INFO)

@app.route('/')
def index():
    return render_template('index.html', page="Index")

@app.route('/products')
def products():
    product_list = db.get_products()
    return render_template('products.html', page="Products", product_list=product_list)

@app.route('/productdetails')
def productdetails():
    code = request.args.get('code', '')
    product = db.get_product(int(code))

    return render_template('productdetails.html', code=code, product=product)

@app.route('/branches')
def branches():
    branch_list = db.get_branches()
    return render_template('branches.html', page = "Branches", branch_list = branch_list)

@app.route('/branch_details/<int:code>')
def branch_details(code):
    branch = db.get_branch(code)
    return render_template('branchdetails.html', branch=branch)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html', page="About Us")

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/auth', methods = ['GET', 'POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')

    is_successful, user = authentication.login(username, password)
    app.logger.info('%s', is_successful)
    if(is_successful):
        session["user"] = user
        app.logger.info('Login successful for user: %s', username)
        return redirect('/')
    else:
        app.logger.warning('Login unsuccessful for user: %s', username)
        error = "Invalid username or password. Please try again."
        return render_template('login.html', error=error)
    
@app.route('/logout')
def logout():
    session.pop("user",None)
    session.pop("cart",None)
    return redirect('/')

@app.route('/addtocart')
def addtocart():
    code = request.args.get('code', '')
    product = db.get_product(int(code))
    item=dict()
    # A click to add a product translates to a 
    # quantity of 1 for now

    item["qty"] = 1
    item["name"] = product["name"]
    item["subtotal"] = product["price"]*item["qty"]
    item["code"] = code

    if(session.get("cart") is None):
        session["cart"]={}

    cart = session["cart"]
    cart[code]=item
    session["cart"]=cart
    return redirect('/cart')

@app.route('/cart')
def cart():
    return render_template('cart.html')
    
@app.route('/updatecart')
def updatecart():
    return render_template('updatecart.html')

@app.route('/updatecartsubmission', methods = ['GET', 'POST'])
def updatecartsubmission():
    cart = session["cart"]
    code = list(cart.keys())
    qty = request.form.getlist("qty")
    qty = list(map(int, qty))

    for index, x in enumerate(qty):
        product = db.get_product(int(code[index]))
        cart[code[index]]["qty"] = qty[index]
        cart[code[index]]["subtotal"] = qty[index] * product["price"]
        
    print(cart)
    session["cart"] = cart
    return redirect('/cart')

@app.route('/removeproduct')
def removeproduct():
    code = request.args.get('code', '')
    cart = session["cart"]
    print(code)
    try:
        del cart[code]
    except:
        print("code is: ",code)
    session["cart"] = cart
    return redirect('/cart')

@app.route('/checkout')
def checkout():
    # clear cart in session memory upon checkout
    om.create_order_from_cart()
    session.pop("cart",None)
    return redirect('/ordercomplete')

@app.route('/ordercomplete')
def ordercomplete():
    return render_template('ordercomplete.html')

@app.route('/past_orders')
def past_orders():
    username = session.get("user")["username"]
    past_orders = db.get_past_orders(username)
    if past_orders is None:
        past_orders = []
    return render_template('pastorders.html', page="Past Orders", past_orders=past_orders)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
      
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

       
        username = session['user']['username']

     
        is_valid_login, user = authentication.login(username, old_password)

        if not is_valid_login:
            flash('Incorrect old password. Please try again.', 'error')
        elif new_password != confirm_password:
            flash('New password and confirmation do not match. Please try again.', 'error')
        else:
          
            db.update_password(username, new_password)
            flash('Password updated successfully!', 'success')
            return redirect(url_for('index'))

    return render_template('change_password.html', page="Change Password")