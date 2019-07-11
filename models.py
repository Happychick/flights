from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    airport_code = Column(String(5))
    airport_name = Column(String(120))
    city = Column(String(120))
    country = Column(String(120))
    country_iso = Column(String(10))
    continent = Column(String(120))

    def __init__(self, airport_code=None, city=None, city_id=None, country=None, continent=None):
        self.airport_code = airport_code
        self.airport_name = airport_name
        self.city = city
        self.country = country
        self.country_iso = country_iso
        self.continent = continent

    def __repr__(self):
        return '<Location %r>' % (self.airport_code)
