from PIL import Image
from datetime import datetime
from flask import Flask, request, send_file, json, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps, update_wrapper
from sqlalchemy_utils import IPAddressType, CountryType, Country
from ua_parser import user_agent_parser
import uuid
import io
import os

app = Flask(__name__)
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:XXXXXX@XXXXX/readreceipt'
app.config ['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Recipients(db.Model):
    id = db.Column('recipient_id', db.Integer, primary_key = True)
    r_uuid = db.Column(db.String(36))
    description = db.Column(db.String(200))
    email = db.Column(db.String(100))

    def __repr__(self):
        return f'<Recipients {self.r_uuid}>'

class Tracking(db.Model):
    id = db.Column('tracking_id', db.Integer, primary_key = True)
    recipients_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    ip_country = db.Column('IPCountry', CountryType)
    connecting_ip = db.Column('ConnectingIP', IPAddressType)
    user_agent = db.Column(db.String(255))
    details = db.Column(db.JSON)

    def __repr__(self):
        return f'<Tracking {self.id}>'

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)

@app.route("/")
def root_path():
    return ''

@app.route("/new-uuid")
def new_uuid():
    this_uuid = str(uuid.uuid4())
    description = request.args.get('description')
    email = request.args.get('email')

    entry = Recipients(r_uuid=this_uuid, description=description, email=email)

    r = f"""
    <p>{this_uuid}<p>

    {description} {email}
    """
    db.session.add(entry)
    db.session.commit()
    return r

@app.route("/img/<this_uuid>")
@nocache
def send_img(this_uuid):
    r_model = Recipients.query.filter_by(r_uuid=this_uuid).first()
    details = dict()
    details['user_agent'] = request.headers.get('User-Agent')
    details['headers'] = dict(request.headers)
    details['remote_addr'] = request.remote_addr
    details['referrer'] = request.referrer
    details['values'] = request.values
    details['date'] = request.date

    print(r_model.id)
    print(json.dumps(details))

    img_io = io.BytesIO()
    img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    img.save(img_io, format="PNG")
    img_io.seek(0)

    ua = user_agent_parser.Parse(details['user_agent'])

    if not ua["user_agent"]["family"] == "GmailImageProxy":
        entry = Tracking(
            recipients_id=r_model.id, 
            timestamp=datetime.now(),
            ip_country = request.headers.get('Cf-Ipcountry'),
            connecting_ip = request.headers.get('Cf-Connecting-Ip'),
            user_agent = details['user_agent'],
            details=json.dumps(details)
        )
        db.session.add(entry)
        db.session.commit()

    return send_file(img_io, download_name="1.png", mimetype='image/png')
