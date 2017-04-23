from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import httplib2
import json
import requests

app = Flask(__name__)
#__name__ is a variable that uses the name of the application running in Python

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

#create database engine
engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine  #bind database engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

####  Login stuff   ####


####  Login verification helper function for edits and deletes  ####

def verifier(user_id):
	# restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if user_id != login_session['user_id']:
		return True

####  Google Login methods  ####				


@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) 
		for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:  #check to ensure state tokens from server and client match
		response = make_response(json.dumps("Invalid state parameter"), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	code = request.data

	try:                              # change auth code to credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)

	except FlowExchangeError:
		response = make_response(json.dumps("Failed to create authorization code."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	access_token = credentials.access_token                           #check for valid access token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# print 'Got G access token'

	if result.get('error') is not None:                           #handles access token info errors
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
	gplus_id = credentials.id_token['sub']

	if result['user_id'] != gplus_id:                             #verify user and token match
		response = make_response(
			json.dumps("Tokens user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	if result['issued_to'] != CLIENT_ID:                           #verify application and token match
		response = make_response(json.dumps("Tokens client ID doesn't match apps."), 401)
		print "Tokens client ID doesn't match apps."
		response.headers['Content-Type'] = 'application/json'
		return response
	stored_credentials = login_session.get('credentials')  #store credentials for later use...
	stored_gplus_id = login_session.get('gplus_id')

	if stored_credentials is not None and gplus_id == stored_gplus_id: #see if user is already logged in
		response = make_response(json.dumps("Current user is already logged in."), 200)
		response.headers['Content-Type'] = 'application/json'

	login_session['provider'] = 'google'
	login_session['credentials'] = credentials.access_token 
	login_session['gplus_id'] = gplus_id                            

	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt':'json'}
	answer = requests.get(userinfo_url, params=params)
	
	data = json.loads(answer.text)  

	replace = data['email']
	replaceMe = replace[0:replace.find("@")]  #use the first part of the email address if no name on account
	if data['name']:
		login_session['username'] = data['name']
	else:
		login_session['username'] = replaceMe 
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id
			
	output = ''                                                    #Load message for display on website
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += '" style = "width: 300px; hieght: 300px; border-radius: 150px; -webkit-border-radius: 150px; -moz-border-radius: 150px;">'
	flash('You are now logged in with Google as %s' % login_session['username'])
	return output


		####  Facebook login methods

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = request.data
	# print 'Got FB access token'
	# print access_token

	app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
	app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	userinfo_url = "https://graph.facebook.com/v2.8/me"  #changed v2.2 to v2.8 to match login.html <-------------------------<<<

	token = result.split("&")[0]  #strip expire tag from access_token

	url = "https://graph.facebook.com/v2.2/me?%s&fields=name,id,email" % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data['name']
	login_session['email'] = data['email']
	login_session['facebook_id'] = data['id']

	# store token for later use
	stored_token = token.split("=")[1]
	login_session['access_token'] = stored_token

	url = "https://graph.facebook.com/v2.8/me/picture?%s&redirect=0&height=200&width=200" % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	data = json.loads(result)
	login_session['picture'] = data["data"]["url"]
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id
			
	output = ''                                                    #Load message for display on website
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += '" style = "width: 300px; hieght: 300px; border-radius: 150px; -webkit-border-radius: 150px; -moz-border-radius: 150px;">'
	flash('You are now logged in with Facebook as %s' % login_session['username'])
	return output


    #### clear session - for testing
@app.route('/clearSession')
def clearSession():
    login_session.clear()
    return "Session cleared"


	###  All Disconnect
@app.route("/disconnect")
def disconnect():
	if 'provider' in login_session:
		if login_session['provider'] == 'google':
			#q = login_session['access_token']
			#print q
			gdisconnect()
			print 'DC from Google'
			del login_session['gplus_id']
			del login_session['credentials']

		if login_session['provider'] == 'facebook':
			fbdisconnect()
			del login_session['facebook_id']
			
			print 'DC from Facebook'
		del login_session['user_id']
		del login_session['username']
		del login_session['picture']
		del login_session['email']
		flash("You have been logged out.")
		return redirect(url_for('showRestaurants'))
	else:
		flash("You weren't logged in!!")
		redirect(url_for('showRestaurants'))

	####  Facebook disconnect
@app.route('/fbdisconnect')
def fbdisconnect():
	facebook_id = login_session['facebook_id']
	access_token = login_session['access_token']
	print access_token
	url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	# print'hit FB logout function'

         #### Google disconnect
@app.route("/gdisconnect")
def gdisconnect():
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	access_token = credentials  #.access_token
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]

	if result.status == 200:
		response = make_response(json.dumps('Successfully disconnected!'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	else:
		response = make_response(json.dumps('Failed to revoke token for user.'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response



####  JSON Methods  ####

@app.route('/restaurants/JSON')  #provides a GET API for all restaurants
def showRestarauntsJSON():
	restaurants = session.query(Restaurant).all()
	return jsonify(Restaurant=[i.serialize for i in restaurants])

@app.route('/restaurants/<int:restaurant_id>/menu/JSON')  #provides a GET API for retstaurant menu items
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
	return jsonify(MenuItems=[i.serialize for i in items]) # loop to serialize all DB menu items for the given restaurant

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')  #provides a GET API for one restaurant menu item
def restaurantMenuItemJSON(restaurant_id, menu_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	item = session.query(MenuItem).filter_by(id=menu_id).one()
	return jsonify(MenuItem=item.serialize) 


####  Restaurant methods  ####

@app.route('/')
@app.route('/restaurants')
def showRestaurants():  #  This page will show all restaurants
	restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
	if 'username' not in login_session:
		return render_template('publicrestaurants.html', restaurants=restaurants)
	else:
		return render_template('restaurants.html', restaurants=restaurants) 

@app.route('/restaurant/new', methods=['GET', 'POST'])   #  new restaurant
def newRestaurant():
	if request.method == 'POST':
		if 'username' not in login_session:
			return redirect('/login')
		else:
			newrestaurant = Restaurant(name=request.form['name'], user_id=login_session['user_id'])
			session.add(newrestaurant)
			session.commit()
			flash("New Restaurant Created!!")
			return redirect(url_for('showRestaurants'))
	else:
		if 'username' not in login_session:
			return redirect('/login')
		else:
			return render_template('newRestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])  #  edit restaurant
def editRestaurant(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	oops = "<script>function myFunction() {alert('You cannot edit this restaurant.  You are not the owner');\
				 window.location= '/restaurants';};</script><body onload='myFunction()'>"
	if request.method == 'POST':
		if verifier(restaurant.user_id) == True:
				return oops
		else:
			restaurant.name = request.form['name']
			session.add(restaurant)
			session.commit()
			flash("Restaurant Edited!!")
			return redirect(url_for('showRestaurants'))
	else:
		if 'username' not in login_session:
			return redirect('/login')
		else:
			if verifier(restaurant.user_id) == True:
				return oops 
			else:
				return render_template('editRestaurant.html', restaurant=restaurant.name, restaurant_id=restaurant_id)


@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET', 'POST']) #  delete restaurant
def deleteRestaurant(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	oops = "<script>function myFunction() {alert('You cannot delete this restaurant.  You are not the owner');\
	 window.location= '/restaurants';};</script><body onload='myFunction()'>"
	if 'username' not in login_session:
			return redirect('/login')
	if verifier(restaurant.user_id) == True:
		return oops

	if request.method == 'POST':
		if verifier(restaurant.user_id) == True:
			return oops
		else:
			session.delete(restaurant)
			session.commit()
			flash("Restaurant Deleted!!")
			return redirect(url_for('showRestaurants'))
		
	else:
		restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
		return render_template('deleteRestaurant.html', restaurant_id=restaurant_id, restaurant=restaurant.name)


####  Menu methods  ####

@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu')  #display menu items
def restaurantMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	creator = getUserInfo(restaurant.user_id)
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id).all()
	if 'username' not in login_session or creator.id != login_session['user_id']:
		return render_template('publicmenu.html', items=items, restaurant=restaurant, creator=creator)
	else:
		if items == []:
			return render_template('noMenu.html', restaurant=restaurant)
		else:
			return render_template('menu.html', restaurant=restaurant, items=items)

@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'])  #create new menu items
def newMenuItem(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if request.method == 'POST':
		newItem = MenuItem(name=request.form['name'], description=request.form['description'],
			price=request.form['price'], course=request.form['course'], restaurant_id=restaurant_id, user_id=restaurant.user_id)
		session.add(newItem)
		session.commit()
		flash("New Menu Item Created!!")
		return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
	else:
		if 'username' not in login_session:
			return redirect('/login')
		else:
			return render_template('newmenuitem.html', restaurant_id=restaurant_id, restaurant=restaurant.name)

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET', 'POST'])  #edit menu items
def editMenuItem(restaurant_id, menu_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	oops = "<script>function myFunction() {alert('You cannot edit this restaurant menu.  You are not the owner');\
	 window.location= '/restaurants';};</script><body onload='myFunction()'>"
	if request.method == 'POST':
		if verifier(restaurant.user_id) == True:
			return oops
		else:
			item = session.query(MenuItem).filter_by(id=menu_id).one()
			
			if request.form['course']:
				item.course = request.form['course']
				print item.course
				session.add(item) 

			if request.form['price']:
				item.price = request.form['price']
				session.add(item)

			if request.form['description']:
				item.description = request.form['description']
				session.add(item)

			if request.form['name']:
				item.name = request.form['name']
				session.add(item)

			session.commit()
			flash("Menu Item Edited!!")
			return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
	else:
		if 'username' not in login_session:
			return redirect('/login')
			if verifier(restaurant.user_id) == True:
				return oops

		else:
			restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
			item = session.query(MenuItem).filter_by(id=menu_id).one()
			return render_template('editmenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, 
				restaurant=restaurant.name, item_name=item.name, item_price=item.price, 
				item_description=item.description, item_course=item.course)

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET', 'POST']) #delete menu items
def deleteMenuItem(restaurant_id, menu_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	oops = "<script>function myFunction() {alert('You cannot delete this restaurant menu item.  You are not the owner');\
	 window.location= '/restaurants';};</script><body onload='myFunction()'>"
	if request.method == 'POST':
		if verifier(restaurant.user_id) == True:
			return oops
		else:
			item = session.query(MenuItem).filter_by(id=menu_id).one()
			session.delete(item)
			session.commit()
			flash("Menu Item Deleted!!")
			return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
	else:
		if 'username' not in login_session:
			return redirect('/login')
		else:
			if verifier(restaurant.user_id) == True:
				return oops
			else:
				restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
				item = session.query(MenuItem).filter_by(id=menu_id).one()
				return render_template('deletemenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, \
					restaurant=restaurant.name, item_name=item.name)

														# User methods
def getUserID(email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None


def getUserInfo(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user

def createUser(login_session):
	newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
