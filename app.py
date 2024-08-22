import json
from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import config
from bricksAPI import api_usage

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lis.db'
db = SQLAlchemy(app)


class LIS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    ls_id = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(120), unique=True, nullable=False)
    ean = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.String(120), nullable=True)
    pieces = db.Column(db.Integer, nullable=True)

    owned = db.Column(db.Boolean, nullable=True, default=False)
    owned_pieces = db.Column(db.Integer, nullable=True, default=0)
    owned_list = db.Column(db.String(120), nullable=True)

    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


@app.route('/search_api', methods=['GET', 'POST'])
def search_api():
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            data = api_usage.get_set_data(query)
            if data:
                result = LIS.query.filter(
                    (LIS.ean == data['ean']) | (LIS.ls_id == data['number'])).first()
                if result:
                    result.api_id = data['setID']
                    result.ls_id = data['number']
                    result.title = data['name']
                    result.price = data['price']
                    result.ean = data['ean']
                    result.pieces = data.get('pieces', 0)
                    result.last_updated = datetime.utcnow()
                else:
                    result = LIS(
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


@app.route('/search_db', methods=['GET', 'POST'])
def search_db():
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            result = LIS.query.filter(
                (LIS.ean == query) | (LIS.ls_id == query)
            ).first()
            if result:
                return render_template('result.html', result=result)
            else:
                return "Set not found in local database.", 404

    return render_template('search_db.html')


@app.route('/add_to_collection/<int:set_id>', methods=['POST'])
def add_to_collection(set_id):
    set_item = LIS.query.get(set_id)
    if set_item:
        selected_list = request.form.get('owned_list')
        if selected_list == 'create_new':
            new_list_name = request.form.get('new_list_name')
            if new_list_name:
                set_item.owned_list = new_list_name
            else:
                return "Please provide a name for the new list.", 400
        else:
            set_item.owned_list = selected_list

        set_item.owned = True
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return "Set not found.", 404


@app.route('/collection_lists', methods=['GET'])
def collection_lists():
    lists = db.session.query(LIS.owned_list).distinct().all()
    lists = [l[0] for l in lists if l[0]]
    return json.dumps(lists)


@app.route('/')
def index():
    return redirect(url_for('search_api'))


if __name__ == '__main__':
    app.run(debug=True)
