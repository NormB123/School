from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)  #__name__ is a variable that uses the name of the application running in Python

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

engine = create_engine('postgres://ozgpfjjccokjnc:c0d7be055c2266e33cae8911990dd9d1eea12016b2221cc99fbb1b093023e806@ec2-54-235-181-120.compute-1.amazonaws.com:5432/d6qvpsv07j1urk')
# ('sqlite:///restaurantmenu.db')  #remarked this out for heroku, then didn't use it
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/restaurants/<int:restaurant_id>/menu/JSON')  #provides a GET API for retstaurant menu items
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return jsonify(MenuItems = [i.serialize for i in items]) # loop to serialize all DB menu items for the given restaurant

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')  #provides a GET API for one restaurant menu item
def restaurantMenuItemJSON(restaurant_id, menu_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	item = session.query(MenuItem).filter_by(id = menu_id).one()
	return jsonify(MenuItem = item.serialize) #[i.serialize for i in items]) # loop to serialize all DB menu items for the given restaurant

@app.route('/')  #wraps the Flask function in the defined text '/'
@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant.id)
	return render_template('menu.html', restaurant = restaurant, items = items)

# Task 1: Create route for newMenuItem function here

@app.route('/restaurants/<int:restaurant_id>/new/', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
	if request.method == 'POST':
		newItem = MenuItem(name = request.form['name'], restaurant_id = restaurant_id)
		session.add(newItem)
		session.commit()
		flash("New Menu Item Created!!")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
		return render_template('newmenuitem.html', restaurant_id = restaurant_id, restaurant = restaurant.name)
	return "page to create a new menu item. Task 1 complete!"

# Task 2: Create route for editMenuItem function here

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	if request.method == 'POST':
		restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
		item = session.query(MenuItem).filter_by(id = menu_id).one()
		item.name = request.form['name']
		session.add(item)
		session.commit()
		flash("Menu Item Edited!!")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
		item = session.query(MenuItem).filter_by(id = menu_id).one()
		return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, restaurant = restaurant.name, item_name = item.name)
	return "page to edit a menu item. Task 2 complete!"

# Task 3: Create a route for deleteMenuItem function here

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	if request.method == 'POST':
		restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
		item = session.query(MenuItem).filter_by(id = menu_id).one()
		session.delete(item)
		session.commit()
		flash("Menu Item Deleted!!")
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
		item = session.query(MenuItem).filter_by(id = menu_id).one()
		return render_template('deletemenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, restaurant = restaurant.name, item_name = item.name)
	return "page to delete a menu item. Task 3 complete!"

# if __name__ == '__main__':  # remarked this out for Heroku, then didn't use it
app.secret_key = 'super_secret_key'
app.debug = True
	# app.run(host = '0.0.0.0', port = 5000)  # remarked this out for Heroku, then didn't use it
