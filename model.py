from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

#Creating the database models

# User Table
class User(db.Model):
    __tablename__ = "user"
    
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    address = db.Column(db.String, nullable=False)
    ploc = db.Column(db.String, nullable=False)
    pinc = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    # One user can have many occupancy records
    occupancy = db.relationship("Occupancy", backref="user", cascade="all, delete-orphan")

    def __init__(self, name, dob, email, address, ploc, pinc, password):
        self.name = name
        self.dob = dob
        self.email = email
        self.address = address
        self.ploc = ploc
        self.pinc = pinc
        self.password = password

# Prime Location Table
class Location(db.Model):
    __tablename__ = "location"
    
    lid = db.Column(db.Integer, primary_key=True)
    lname = db.Column(db.String, unique=True, nullable=False)

    # One location has many lots
    parking_lots = db.relationship("Lot", backref="location", cascade="all, delete-orphan")

    def __init__(self, lname):
        self.lname = lname

# Parking Lot Table
class Lot(db.Model):
    __tablename__ = "parking_lot"
    
    pid = db.Column(db.Integer, primary_key=True)
    pname = db.Column(db.String, unique=True, nullable=False)
    paddress = db.Column(db.String, nullable=False)
    plcode = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    pmax = db.Column(db.Integer, nullable=False) # Max Number of spots in the parking lot
    earnings = db.Column(db.Integer, nullable=True)


    # Foreign Key to Prime Location
    location_id = db.Column(db.Integer, db.ForeignKey('location.lid'), nullable=False)

    # One lot has many occupancies
    occupancies = db.relationship("Occupancy", backref="parking_lot", cascade="all, delete-orphan")

    def __init__(self, pname, paddress, plcode, price, pmax, earnings, location_id):
        self.pname = pname
        self.paddress = paddress
        self.plcode = plcode
        self.price = price
        self.pmax = pmax
        self.earnings = earnings
        self.location_id = location_id

# Occupancy Table
class Occupancy(db.Model):
    __tablename__ = "occupancy"
    
    oid = db.Column(db.Integer, primary_key=True)
    ores = db.Column(db.Integer, nullable = False)
    oveh = db.Column(db.String, nullable = True)
    otstp = db.Column(db.DateTime, nullable = True, default=datetime.utcnow())
    oetp = db.Column(db.DateTime, nullable=True)

    # Total time (in hours) - can be calculated as a property
    @property
    def otot(self):
        if self.oetp and self.otstp:
            duration = self.oetp - self.otstp
            return round(duration.total_seconds() / 3600, 2)  # Hours with 2 decimals
        return None

    # Foreign Keys
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.pid'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.uid'), nullable=True)

    def __init__(self, parking_lot_id, user_id, ores, oveh):
        self.parking_lot_id = parking_lot_id
        self.user_id = user_id
        self.ores = ores
        self.oveh = oveh
