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
    __tablename__ = 'lis'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    ls_id = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(120), unique=True, nullable=False)
    ean = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.String(120), nullable=True)
    pieces = db.Column(db.Integer, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    owned = db.Column(db.Boolean, nullable=True, default=False)
    owned_pieces = db.Column(db.Integer, nullable=True, default=0)
    owned_list = db.Column(db.String(120), nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Collection(db.Model):
    __tablename__ = 'collection'
    id = db.Column(db.Integer, primary_key=True)
    list_name = db.Column(db.String(120), nullable=False)
    set_id = db.Column(db.Integer, db.ForeignKey('lis.id'), nullable=False)
    added_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lis_set = db.relationship('LIS', backref=db.backref('collections', lazy=True))


@app.route('/search_api', methods=['GET', 'POST'])
def search_api():
    collection_names = db.session.query(Collection.list_name).distinct().all()
    collection_names = [name[0] for name in collection_names if name[0]]
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
                    result.image_url = data.get('image_url')
                    result.last_updated = datetime.utcnow()
                else:
                    result = LIS(
                        api_id=data['setID'],
                        ls_id=data['number'],
                        title=data['name'],
                        ean=data['ean'],
                        price=data['price'],
                        pieces=data.get('pieces', 0),
                        image_url=data.get('image_url'),
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(result)
                db.session.commit()
                return render_template('result.html', result=result, collection_names=collection_names)
            else:
                return "Set not found on Brickset API.", 404

    return render_template('search_api.html', collection_names=collection_names)


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
                selected_list = new_list_name
            else:
                return "Please provide a name for the new list.", 400

        collection_entry = Collection(list_name=selected_list, set_id=set_id)
        db.session.add(collection_entry)
        db.session.commit()

        return redirect(url_for('index'))
    else:
        return "Set not found.", 404


@app.route('/collection_lists', methods=['GET'])
def collection_lists():
    lists = db.session.query(Collection.list_name).distinct().all()
    list_names = [name[0] for name in lists if name[0]]
    return json.dumps(list_names)


@app.route('/collection/<string:list_name>', methods=['GET'])
def collection(list_name):
    page = request.args.get('page', 1, type=int)
    per_page = 17
    sets = Collection.query.filter_by(list_name=list_name).paginate(page=page, per_page=per_page)
    if sets.items:
        return render_template('collection.html', sets=sets, list_name=list_name)
    else:
        return "No sets found in this list.", 404


@app.route('/set/<int:set_id>', methods=['GET', 'POST'])
def set_detail(set_id):
    set_item = LIS.query.get_or_404(set_id)
    collection_names = db.session.query(Collection.list_name).distinct().all()
    collection_names = [name[0] for name in collection_names if name[0]]
    if request.method == 'POST':
        selected_list = request.form.get('owned_list')
        if selected_list == 'create_new':
            new_list_name = request.form.get('new_list_name')
            if new_list_name:
                selected_list = new_list_name
            else:
                return "Please provide a name for the new list.", 400

        existing_collection = Collection.query.filter_by(set_id=set_id, list_name=selected_list).first()
        if existing_collection:
            if 'owned_pieces' in request.form:
                existing_collection.lis_set.owned_pieces = int(request.form.get('owned_pieces'))
                db.session.commit()
        else:
            collection_entry = Collection(list_name=selected_list, set_id=set_id)
            db.session.add(collection_entry)
            db.session.commit()

        return redirect(url_for('set_detail', set_id=set_id))

    return render_template('set_detail.html', set_item=set_item, collection_names=collection_names)


@app.route('/')
def index():
    collection_names = db.session.query(Collection.list_name).distinct().all()
    collection_names = [name[0] for name in collection_names if name[0]]
    return render_template('index.html', collection_names=collection_names)


if __name__ == '__main__':
    app.run(debug=True)
