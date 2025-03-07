from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request, flash, redirect, url_for, render_template, session
import secrets
import json
from authlib.integrations.flask_client import OAuth
import re
from urllib.parse import quote_plus, urlencode
from models.car_owner import CarOwner
from config import Config
from models.ride import Ride
from models.route import Route
from models.user import User
from models.vehicle import Vehicle
from datetime import date
from init import app, db
import re

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=Config.AUTH0_CLIENT_ID,
    client_secret=Config.AUTH0_CLIENT_SECRET,
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{Config.AUTH0_DOMAIN}/.well-known/openid-configuration'
)

@app.route('/')
def index():
    user=User.query.all()
    # for user in uservar:
    #     print("User name:",user.user_name)
    car_owners = CarOwner.query.all() 
    for owner in car_owners:
        print("owner name:",owner.name)
    user = session.get("user")
    
    vehicles = Vehicle.query.all()  
    
    vehicle_list = [{
        'vehicle_id': vehicle.vehicle_id,
        'owner_name': vehicle.owner.name,
        'available_seats': vehicle.available_seats,
        'charges': vehicle.charges,
        'vehicle_name': vehicle.vehicle_name,
        'vehicle_description': vehicle.vehicle_description,
        'vehicle_type': vehicle.vehicle_type,
        'duration': vehicle.duration,
        'owner_email': vehicle.owner.email,
        'owner_phone': vehicle.owner.whatsapp_number,
        'departure_time': vehicle.ride.departure_time if vehicle.ride else None, 
        'return_time': vehicle.ride.return_time if vehicle.ride else None, 
    } for vehicle in vehicles]
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify(vehicle_list)
    
    return render_template("index.html", session=user, pretty=json.dumps(user, indent=4), vehicles=vehicle_list)

@app.route("/callback", methods=["GET", "POST"])
def callback():
    try:
        token = oauth.auth0.authorize_access_token()
        session["user"] = token
        user_info = token.get("userinfo")
        
        user_name = user_info.get("name")
        email = user_info.get("email")

        if user_name and email:
            patterns = [
                r'[a-zA-Z]\d{6}',               
                r'\d{2}[a-zA-Z]-\d{4}'          
            ]
            for pattern in patterns:
                user_name = re.sub(pattern, '', user_name)
            
            user_name = user_name.strip()

            if not user_name:
                flash("Invalid user name. Please try again.", "danger")
                return redirect(url_for("index"))

            existing_user = User.query.filter_by(email=email).first()
            if not existing_user:
                new_user = User(user_name=user_name, email=email)
                db.session.add(new_user)
                db.session.commit()
    except Exception as e:
        app.logger.error(f"Authentication failed: {e}")
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for("index"))

    return redirect(url_for("index"))


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://{Config.AUTH0_DOMAIN}/v2/logout?"
        + urlencode({
            "returnTo": url_for("index", _external=True),
            "client_id": Config.AUTH0_CLIENT_ID,
        }, quote_via=quote_plus)
    )
    

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    if 'user' not in session:
        return redirect(url_for('login'))
    try:
        user_info = session['user']['userinfo']
        owner_name = user_info.get('user_name')
        print("during adding vehicle: ",user_info.get('user_name'))
        email = user_info.get('email')

        owner = CarOwner.query.filter_by(email=email).first()
        if not owner:
            owner = CarOwner(
                email=email,
                name=owner_name,
                whatsapp_number=request.form['whatsapp_num'],
                off_day=request.form['off_day'],
            )
            db.session.add(owner)
            db.session.flush()

        route = Route(
            pickup_location=request.form['from'],
            dropoff_location=request.form['to']
        )
        db.session.add(route)
        db.session.flush()

        vehicle = Vehicle(
            vehicle_name=request.form['carname'],
            vehicle_description=request.form['car_description'],
            number_plate=request.form['number_plate'],
            vehicle_type=request.form['vehicle_type'],
            available_seats=int(request.form['seats']) if request.form['seats'] != 'four+'
            else int(request.form['custom_seats']),
            duration=request.form['duration'],
            charges=request.form['charges'],
            owner_id=owner.owner_id
        )
        if(vehicle.available_seats < 1):
            raise Exception("Available Seats less than 1")
        db.session.add(vehicle)


        ride = Ride(
            user_id=session['user']['userinfo'].get('sub'), 
            owner_id=owner.owner_id,
            route_id=route.route_id,
            date=date.today(),
            departure_time=request.form['departure_time'],
            return_time=request.form['return_time']
        )
            
        
        db.session.add(ride)

        db.session.commit()
        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/add_vehicle')
def add_vehicle_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('add_vehicle.html')    

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)
