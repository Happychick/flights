from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class Location(Base):
    __tablename__ = 'locations'
    airport_id = Column(Integer, primary_key=True)
    airport_code = Column(String(5))
    city = Column(String(120))
    city_id = Column(Integer)
    country = Column(String(120))
    continent = Column(String(120))

    def __init__(self, airport_code=None, city=None, city_id=None, country=None, continent=None):
        self.airport_code = airport_code
        self.city = city
        self.city_id = city_id
        self.country = country
        self.continent = continent

    def __repr__(self):
        return '<Location %r>' % (self.airport_code)
