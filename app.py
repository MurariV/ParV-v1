from flask import Flask, render_template, url_for, redirect, session, request
from model import db, User, Location, Lot, Occupancy
from sqlalchemy import func
from sqlalchemy.orm import aliased
from datetime import datetime
from random import shuffle

admin = {
    'name' : 'Admin',
    'password' : 'admin@123',
    'email' : 'admin@email.com',
    'address' : 'Mogappair',
    'ploc' : 'Chennai',
    'pcode' : '600037'
}

app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'hello'

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/", methods=['POST', 'GET'])
@app.route("/user", methods=['POST', 'GET'])
def UserLogin():
    if 'email' in session:
        return redirect(url_for('UserHome'))
    else:
        if request.method == 'POST':
            email = request.form['email']
            pwd = request.form['pwd']
            foundusr = User.query.filter_by(email=email).first()
            if foundusr and (pwd == foundusr.password):
                session['email'] = email
                return redirect(url_for("UserHome"))
            else:
                return redirect(url_for("Registration"))
        else:
            return render_template('user.html')

@app.route("/register", methods=['POST', 'GET']) 
def Registration():
    if request.method == 'POST':
        name = request.form['nm']
        dob = request.form['dob']
        email = request.form['email']
        address = request.form['address']
        ploc = request.form['location']
        pinc = request.form['pcode']
        pwd = request.form['pwd']
        rpwd = request.form['rpwd']
        udate = datetime.strptime(dob, "%Y-%m-%d").date()

        foundusr = User.query.filter_by(email=email).first()
        if foundusr:
            return redirect(url_for('UserLogin'))
        elif rpwd != pwd:
            return redirect(url_for('Registration'))
        else:
            usr = User(name, udate, email, address, ploc, pinc, pwd)
            db.session.add(usr)
            db.session.commit()
            return redirect(url_for('UserLogin'))
    return render_template('register.html')

@app.route("/user/home")
def UserHome():
    if 'email' in session:
        ur = User.query.filter_by(email=session['email']).first()
        ocp = Occupancy.query.filter_by(user_id = ur.uid).all()
        locs = Location.query.all()
        locate = "None"
        sel = session.pop('selected_option', None)
        if sel:
            sloc = Location.query.filter_by(lname=sel).first()
            lots = Lot.query.filter_by(location_id=sloc.lid).all()
            locc = Occupancy.query.filter_by(parking_lot_id=sloc.lid).all()
            locate = sel
        else:
            lots = []
            locc = []

        return render_template('userhome.html', locs=locs, lots=lots, locc=locc, locate = locate, ocp = ocp)
    return redirect(url_for('UserLogin'))

@app.route('/user/home/select', methods=['POST'])
def handleusr_select():
    selected_option = request.form.get('ans')
    session['selected_option'] = selected_option
    return redirect(url_for('UserHome'))

@app.route("/user/booking/<l>", methods=['POST', 'GET'])
def Booking(l):
    if 'email' in session:
        usr = User.query.filter_by(email=session['email']).first()
        if request.method == 'POST':
            vehno = request.form['vehno']
            occ = Occupancy.query.filter_by(ores=0, parking_lot_id=l).first()
            if occ:
                occ.ores = 1
                occ.oveh = vehno
                occ.otstp = db.func.current_timestamp()
                occ.user_id = usr.uid
                db.session.commit()
            return redirect(url_for('UserHome'))
        lot = Lot.query.filter_by(pid = l).first()
        locid = lot.location_id
        loc = Location.query.filter_by(lid = locid).first()
        return render_template('book.html', lot = lot, loc = loc, l = l)
    else:
        return redirect(url_for('UserLogin'))
    
from datetime import datetime

@app.route("/user/release/<int:o>", methods=['POST', 'GET'])
def Release(o):
    if 'email' in session:
        usr = User.query.filter_by(email=session['email']).first()
        occ = Occupancy.query.filter_by(oid=o).first()

        # Set exit time using Python's datetime
        occ.oetp = datetime.utcnow()

        # Ensure otstp is a datetime object
        if occ.otstp and occ.oetp:
            duration = occ.oetp - occ.otstp
            hours = duration.total_seconds() / 3600
        else:
            hours = 0

        # Get lot and compute cost
        lot = Lot.query.filter_by(pid=occ.parking_lot_id).first()
        cost = round(hours * lot.price, 2)

        if request.method == 'POST':
            lot.earnings += cost
            occ.ores = 0
            occ.otstp = datetime.utcnow()
            occ.user_id = None
            db.session.commit()
            return redirect(url_for('UserHome'))

        loc = Location.query.filter_by(lid=lot.location_id).first()
        return render_template('release.html', lot=lot, loc=loc, occ=occ, cost=cost)
    
    else:
        return redirect(url_for('UserLogin'))

@app.route("/user/summary")
def UserSummary():
    if 'email' not in session:
        return redirect(url_for('UserLogin'))

    # Get logged-in user
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('UserLogin'))

    # Global occupancy stats
    total_av = Occupancy.query.filter_by(ores=0).count()
    total_oc = Occupancy.query.filter_by(ores=1).count()

    # User booking count
    user_bookings = Occupancy.query.filter_by(user_id=user.uid).count()

    # User's bookings per parking lot
    lot_data = (
        db.session.query(Lot.pname, func.count(Occupancy.oid))
        .join(Occupancy)
        .filter(Occupancy.user_id == user.uid)
        .group_by(Lot.pname)
        .all()
    )
    lot_names = [lot[0] for lot in lot_data]
    lot_counts = [lot[1] for lot in lot_data]

    return render_template(
        'usersummary.html',
        total_av=total_av,
        total_oc=total_oc,
        user_bookings=user_bookings,
        lot_names=lot_names,
        lot_counts=lot_counts
    )

    
@app.route("/user/profile", methods=['POST', 'GET'])
def UserProfile():
    if 'email' in session:
        if request.method == 'POST':
            foundusr = User.query.filter_by(email=session['email']).first()
            name = request.form['nm']
            dob = request.form['dob']
            email = request.form['email']
            address = request.form['address']
            ploc = request.form['location']
            pinc = request.form['pcode']
            udate = datetime.strptime(dob, "%Y-%m-%d").date()
            foundusr.name = name
            foundusr.dob = udate
            foundusr.email = email
            foundusr.address = address
            foundusr.ploc = ploc
            foundusr.pinc = pinc
            db.session.commit()
            return redirect(url_for('LogOut'))            
        usr = User.query.filter_by(email = session['email']).first()
        return render_template('userprofile.html', usr = usr)
    else:
        return redirect(url_for('UserLogin'))
    
@app.route('/user/del')
def DelUser():
    if 'email' in session:
        delu = User.query.filter_by(email = session['email']).first()
        if delu:
            db.session.delete(delu)
            db.session.commit()
        return redirect(url_for('LogOut'))
    else:
        return redirect(url_for('UserLogin'))

@app.route("/admin", methods=['POST', 'GET'])
def AdminLogin():
    if 'email' in session:
        if session['email'] == admin['email']:
            return redirect(url_for('AdminHome'))
    else:
        if request.method == 'POST':
            email = request.form['email']
            pwd = request.form['pwd']

            if email == admin['email'] and pwd == admin['password']:
                session['email'] = email
                return redirect(url_for('AdminHome'))
            else:
                return redirect(url_for('UserLogin'))
        return render_template('admin.html')

@app.route("/admin/home", methods=['GET'])
def AdminHome():
    if 'email' in session and session['email'] == admin['email']:
        locs = Location.query.all()

        # Handle selected location
        locate = "None"
        temp = ""
        sel = session.pop('selected_option', None)

        lots = []
        locc = []

        if sel:
            sloc = Location.query.filter_by(lname=sel).first()
            if sloc:
                temp = sloc
                lots = Lot.query.filter_by(location_id=sloc.lid).all()
                locc = Occupancy.query.all()
                locate = sel

        return render_template('adminhome.html', locs=locs, lots=lots, locc=locc, locate=locate, temp=temp)

    return redirect(url_for('UserLogin'))


@app.route('/admin/lot/del/<l>')
def DelLot(l):
    delo = Occupancy.query.filter_by(parking_lot_id = l).all()
    dell = Lot.query.filter_by(pid = l).first()
    if dell:
        for i in delo:
            db.session.delete(i)
            db.session.commit()
        db.session.delete(dell)
        db.session.commit()
    return redirect(url_for('AdminHome'))

@app.route('/admin/loc/del/<lo>')
def DelLoc(lo):
    delp = Location.query.filter_by(lid = lo).first()
    if delp:
        db.session.delete(delp)
        db.session.commit()
    return redirect(url_for('AdminHome'))

@app.route('/admin/home/select', methods=['POST'])
def handle_select():
    selected_option = request.form.get('ans')
    session['selected_option'] = selected_option
    return redirect(url_for('AdminHome'))

@app.route('/admin/home/input', methods=['POST'])
def handle_input():
    ln = request.form['locnm']
    fndloc = Location.query.filter_by(lname=ln).first()
    if fndloc:
        return redirect(url_for('AdminHome'))
    else:
        loc = Location(ln)
        db.session.add(loc)
        db.session.commit()
        return redirect(url_for('AdminHome'))
    
@app.route("/admin/home/addspots/<te>", methods=['GET', 'POST'])
def AddSpots(te):
    if 'email' in session:
        if session['email'] == admin['email']:
            if request.method == 'POST':
                plnm = request.form['plnm']
                pladd = request.form['pladd']
                plcode = request.form['plcode']
                plpr = request.form['plpr']
                mxsp = request.form['mxsp']
                loc = Location.query.filter_by(lid = te).first()
                plot = Lot(plnm, pladd, plcode, int(plpr), int(mxsp), 0, loc.lid)
                db.session.add(plot)
                db.session.commit()
                for _ in range(int(mxsp)):
                    occ = Occupancy(parking_lot_id=plot.pid, user_id=None, ores=0, oveh=None)
                    db.session.add(occ)
                db.session.commit()
                return redirect(url_for('AdminHome'))
            return render_template('addspots.html')
    else:
        return redirect(url_for('UserLogin'))

@app.route("/admin/home/spot/edit/<l>", methods=['GET', 'POST'])
def EditSpots(l):
    if 'email' in session and session['email'] == admin['email']:
        lot = Lot.query.filter_by(pid=l).first()
        if not lot:
            return redirect(url_for('AdminHome'))

        if request.method == 'POST':
            plnm = request.form['plnm']
            pladd = request.form['pladd']
            plcode = request.form['plcode']
            plpr = request.form['plpr']
            new_mxsp = int(request.form['mxsp'])
            old_mxsp = lot.pmax

            # Update lot info
            lot.pname = plnm
            lot.paddress = pladd
            lot.plcode = plcode
            lot.price = int(plpr)
            lot.pmax = new_mxsp

            db.session.commit()

            # Sync Occupancy records
            current_spots = Occupancy.query.filter_by(parking_lot_id=lot.pid).all()
            diff = new_mxsp - len(current_spots)

            if diff > 0:
                # Add extra empty spots
                for _ in range(diff):
                    occ = Occupancy(parking_lot_id=lot.pid, user_id=None, ores=0, oveh=None)
                    db.session.add(occ)
            elif diff < 0:
                # Remove unreserved spots only
                empty_spots = [o for o in current_spots if o.ores == 0]
                to_delete = empty_spots[:abs(diff)]

                if len(to_delete) < abs(diff):
                    return redirect(url_for('AdminHome'))

                for o in to_delete:
                    db.session.delete(o)

            db.session.commit()
            return redirect(url_for('AdminHome'))

        return render_template('editspots.html')
    else:
        return redirect(url_for('UserLogin'))


@app.route("/admin/usrls")
def AdminUsers():
    if 'email' in session:
        if session['email'] == admin['email']:
            user = User.query.all()
            return render_template('adminusers.html', users = user)
    else:
        return redirect(url_for('UserLogin'))

@app.route("/admin/summary")
def AdminSummary():
    if 'email' not in session:
        return redirect(url_for('UserLogin'))

    from sqlalchemy import func

    # Basic counts
    av = Occupancy.query.filter_by(ores=0).count()
    oc = Occupancy.query.filter_by(ores=1).count()
    usrc = User.query.count()

    # Pie Chart data: Earnings per lot
    lot_data = (
        db.session.query(Lot.pname, func.coalesce(Lot.earnings, 0))
        .order_by(Lot.pname)
        .all()
    )
    lot_names = [lot[0] for lot in lot_data]
    lot_earnings = [lot[1] for lot in lot_data]

    return render_template(
        "adminsummary.html",
        av=av,
        oc=oc,
        usrc=usrc,
        lot_names=lot_names,
        lot_earnings=lot_earnings
    )
    
@app.route("/admin/profile")
def AdminProfile():
    if 'email' in session:
        nm = admin['name']
        em = admin['email']
        ad = admin['address']
        pl = admin['ploc']
        pc = admin['pcode']
        return render_template('adminprofile.html', nm = nm, em = em, ad = ad, pl = pl, pc = pc)
    else:
        return redirect(url_for('UserLogin'))

@app.route("/logout")
def LogOut():
    session.pop('email', None)
    return redirect(url_for('UserLogin'))

if __name__ == '__main__':
    app.run(debug = True)