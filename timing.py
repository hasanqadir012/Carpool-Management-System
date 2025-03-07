from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Time, Date
from sqlalchemy.orm import relationship
from models import db
class Timing(db.Model):
    __tablename__ = 'timings'
    
    timing_id= db.Column(db.Integer,primary_key=True, auto_increment=True)
    date= db.Column(db.Date,nullabe=False)
    departure_time= db.Column(db.Time,nullabe=False)
    return_time= db.Column(db.Time,nullabe=False)
    owner_id= db.Column(db.Integer,db.foriegn_key('car_owner.owner_id'),nullable=False)
    user_id= db.Column(db.Integer,db.foriegn_key('user.id'),nullable=False)

    
    rides = db.relationship('Ride', backref='timing', lazy=True)