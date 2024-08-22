import json
from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import config
from bricksAPI import api_usage

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lis.db'
db = SQLAlchemy(app)


class Searched(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    ls_id = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(120), unique=True, nullable=False)
    ean = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.String(120), nullable=True)
    pieces = db.Column(db.Integer, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_part_numbers(self, part_numbers):
        self.part_numbers = json.dumps(part_numbers)

    def get_part_numbers(self):
        return json.loads(self.part_numbers) if self.part_numbers else []


@app.route('/search_api', methods=['GET', 'POST'])
def search_api():
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            data = api_usage.get_set_data(query)
            if data:
                result = Searched.query.filter(
                    (Searched.ean == data['ean']) | (Searched.ls_id == data['number'])).first()
                if result:
                    result.api_id = data['setID']
                    result.ls_id = data['number']
                    result.title = data['name']
                    result.price = data['price']
                    result.ean = data['ean']
                    result.pieces = data.get('pieces', 0)
                    result.last_updated = datetime.utcnow()
                else:
                    result = Searched(
                        api_id=data['setID'],
                        ls_id=data['number'],
                        title=data['name'],
                        ean=data['ean'],
                        price=data['price'],
                        pieces=data.get('pieces', 0),
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(result)
                db.session.commit()
                return render_template('result.html', result=result)
            else:
                return "Set not found on Brickset API.", 404

    return render_template('search_api.html')


@app.route('/')
def index():
    return redirect(url_for('search_api'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
