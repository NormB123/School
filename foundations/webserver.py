###  import database and server stuff
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import string

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

###  import database engine stuff
engine = create_engine('sqlite:///restaurantMenu.db')
Base.metadata.bind=engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


class webServerHandler(BaseHTTPRequestHandler):

	def do_GET(self):
		try:
			if self.path.endswith("/new"):
				self.send_response(201) #changed response to show which URL was working for testing...
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				output = ""
				output += "<html><body>"
				output += '''<form method=POST enctype='multipart/form-data' action='/restaurants/new'>'''
				output += '''<h1>Add a New Restaurant</h1><input type="text" name="newRestName">'''
				output += '''<br><input type = "submit" value = "Submit"></form>'''
				output += "</html></body>"
				self.wfile.write(output)
				return

			if self.path.endswith("/edit"):
				self.send_response(202) #changed response to show which URL was working for testing...
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				o = string.split(self.path, '/')
				rest = session.query(Restaurant).filter_by(id = o[2]).one() 
				print o[2]
				output = ""
				output += "<html><body>"
				output += '''<form method=POST enctype='multipart/form-data' action='/restaurants/%d/edit'>''' % rest.id
				output += '''<h1>Edit %s Restaurant Name</h1><input type="text" name='editRestName'>''' % rest.name
				output += '''<br><input type = "submit" value = "Submit"></form>'''
				output += "</html></body>"
				self.wfile.write(output)
				return

			if self.path.endswith("/delete"):
				self.send_response(203) #changed response to show which URL was working for testing...
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				o = string.split(self.path, '/')
				rest = session.query(Restaurant).filter_by(id = o[2]).one() 
				print o[2]
				output = ""
				output += "<html><body>"
				output += '''<h1>Delete %s??</h1>''' % rest.name				
				output += '''<form method=POST enctype='multipart/form-data' action='/restaurants/%s/delete'>''' % rest.id
				#output += '''<h1><textarea name = 'deleteRestName'>'''
				#output += '''</textarea></h1>'''
				output += '''<br><input type = "submit" value = "Delete"></form>'''
				output += "</html></body>"
				self.wfile.write(output)
				return

			if self.path.endswith("/restaurants"):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				restaurants = session.query(Restaurant).all()
				output = ""
				output += "<html><body>"
				output += "<a href = '/restaurants/new'><h2>Click to Add a New Restaurant</h2></a>"
				output += "<h1>Restaurants</h1>"
				for restaurant in restaurants:
					output += "<p>"
					output += " %s <br>"  % restaurant.name
					output += "<a href = 'restaurants/%s/edit'> Edit </a>" % restaurant.id
					output += " | <a href = 'restaurant/%s/delete'> Delete </a>" % restaurant.id
					output += "</p>"
				
				output += "</body></html>"
				self.wfile.write(output)
				#print output  #this is temp for testing...
				return

		except IOError:
			self.send_error(404, "File not found %s" % self.path)



	def do_POST(self):
		try:
			if self.path.endswith("/edit"):
				print "editing"
				print self.path
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
					messagecontent = fields.get('editRestName')
					print messagecontent
					o = string.split(self.path, '/')[2]

					editRestaurant = session.query(Restaurant).filter_by(id = o).one()
					print editRestaurant
					editRestaurant.name = messagecontent[0]
					session.add(editRestaurant)
					session.commit()

					self.send_response(302)
					self.send_header('Content-type', 'text/html')
					self.send_header('Location', '/restaurants')
					self.end_headers()
					return

			if self.path.endswith("/delete"):
				print "deleting"
				print self.path
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
					o = string.split(self.path, '/')[2]
					editRestaurant = session.query(Restaurant).filter_by(id = o).one()
					print editRestaurant
					session.delete(editRestaurant)
					session.commit()

					self.send_response(303)
					self.send_header('Content-type', 'text/html')
					self.send_header('Location', '/restaurants')
					self.end_headers()
					return

			if self.path.endswith("/new"):
				print self.path
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields=cgi.parse_multipart(self.rfile, pdict)
					messagecontent = fields.get('newRestName')
					print messagecontent

					newRestaurant = Restaurant(name = messagecontent[0])
					session.add(newRestaurant)
					session.commit()

					self.send_response(301)
					self.send_header('Content-type', 'text/html')
					self.send_header('Location', '/restaurants')
					self.end_headers()
					return

		except:
			print "error on post"
			#pass


def main():
	try:
		port = 8080
		server = HTTPServer(('', port), webServerHandler)
		print "webserver running on port %s" % port
		server.serve_forever()


	except KeyboardInterrupt:  #this is a built in python interupt executed by pressing cntrl+c on the keyboard.
		print "^C entered, web server stopped"
		server.socket.close()

if __name__ == '__main__':
	main()