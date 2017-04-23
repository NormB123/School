#####  begin configuration section  #####
import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

#####  begin class section  #####

class User(Base):
	__tablename__ = 'user'
	id = Column (Integer, primary_key = True)
	name = Column (String(80), nullable = False)
	email = Column (String(80), nullable = False)
	picture = Column (String(250))
	

	@property
	def serialize(self):
		return {
			'name' : self.name,
			'email' : self.email,
			'picture' : self.picture,
			'id' : self.id
		}


class Restaurant(Base):
	__tablename__ = 'restaurant'  #####  table section inside class  #####
	name = Column (String(80), nullable = False)  #####  mapper section inside class and table descriptor  #####
	id = Column (Integer, primary_key = True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	menuItems = relationship("MenuItem", cascade = "all, delete-orphan")  #added this out for heroku, then didn't use it.  May need for postgres anyway

	####  setp JSON interface for restaurants   ####

	@property
	def serialize(self):
		return {
			'name' : self.name,
			'id' : self.id
		}


class MenuItem(Base):
	__tablename__ = 'menu_item'
	name = Column (String(80), nullable = False)  #####  mapper section inside class and table descriptor  #####
	id = Column (Integer, primary_key = True)
	course = Column(String(250))
	description = Column(String(250))
	price = Column(String(8))
	restaurant_id = Column(Integer, ForeignKey(Restaurant.id))
	user_id = Column(Integer, ForeignKey('user.id'))
	restaurant = relationship(Restaurant)
	user = relationship(User)

	#####  setup JSON interface for menu items #####

	@property
	def serialize(self):
		return {
			'name' : self.name,
			'description' : self.description,
			'id' : self.id,
			'price' : self.price,
			'course' : self.course,
		}


#######  end configuration section - insert at end of file  ######

engine = create_engine('postgres://ozgpfjjccokjnc:c0d7be055c2266e33cae8911990dd9d1eea12016b2221cc99fbb1b093023e806@ec2-54-235-181-120.compute-1.amazonaws.com:5432/d6qvpsv07j1urk')
# ('sqlite:///restaurantmenuwithusers.db')  #remarked this out for heroku, then didn't use it

Base.metadata.create_all(engine)

