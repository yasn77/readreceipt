from PIL import Image
from datetime import datetime
from flask import Flask, request, send_file, json, make_response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps, update_wrapper
import uuid
import io

app = Flask(__name__)
#app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config ['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:XXXXXX@XXXXX/readreceipt'
db = SQLAlchemy(app)

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

    entry = Tracking(recipients_id=r_model.id, timestamp=datetime.now(),
                     details=json.dumps(details))

    db.session.add(entry)
    db.session.commit()


    return send_file(img_io, download_name="1.png", mimetype='image/png')

