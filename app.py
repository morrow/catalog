import random
import string
import httplib2
import json
import requests
import os.path

from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, make_response
from flask import session as login_session

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item, KeyValue

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

# Connect to Database and create database session
engine = create_engine('postgres://catalog:udacity@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create flask app object
app = Flask(__name__)

# Define constants
client_secrets_json = open('client_secrets.json', 'r').read()
CLIENT_ID = json.loads(client_secrets_json)['web']['client_id']
APPLICATION_NAME = "Catalog App"


# Helper Functions #


def generateSlug(input):
    """ Generate slug from input. """
    return input.lower().replace(' ', '_')


def generateKey(length):
    """ Generate random string for given length """
    return''.join(random.choice(
        string.ascii_uppercase + string.digits)
            for x in range(length))


def generateResponse(status_code, message, content_type):
    """ Generate response using make_response library """
    response = make_response(json.dumps(message), content_type)
    response.headers['Content-Type'] = content_type
    return response


def findCategoryBySlug(slug):
    """ Find category by it's slug. """
    return session.query(Category).filter_by(slug=slug).first()


def findItemBySlug(category_slug, item_slug):
    """ Find item by category and item slug. """
    category = findCategoryBySlug(category_slug)
    if category:
        return session.query(Item).filter_by(
            category_id=category.id,
            slug=item_slug).first()  # pep8 E501
    return None


def createUser(login_session):
    """ Creates user from a login_session object. """
    newUser = User(name=login_session['name'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserByID(user_id):
    """ Returns a user object given a user_id. """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getCurrentUser():
    """ Get current user from login_session data. """
    if 'email' in login_session:
        try:
            return getUserByID(getUserIDByEmail(login_session['email']))
        except:
            return None
    return None


def getUserIDByEmail(email):
    """ Returns a user_id for a given user's email address. """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def userAuthorized(object):
    """ Returns whether user is authorized to edit object. """
    if 'user_id' in login_session:
        return object.user_id == login_session['user_id']
    return None

def userAuthenticated():
    """ Returns whether user is logged in. """
    return 'name' in login_session


@app.context_processor
def utility_processor():
    def getCategories():
        """ Return all category objects. """
        return session.query(Category).all()

    def getPageTitle():
        """ Return a page title using the current path. """
        if len(request.path.split('/')):
            return 'Catalog App | %s' % ' '.join(request.path.split('/'))
        return 'Catalog App'

    def getUserEmail():
        """ Return current user email from login_session data. """
        if 'email' in login_session:
            return login_session['email']
        return None

    def getClassHTML(slug):
        """ Return current class if path matches slug. """
        split_path = request.path.split('/')
        if len(split_path) > 2 and split_path[2] == slug:
            return ' class="current" '
        return ''

    return dict(getCategories=getCategories,
                getPageTitle=getPageTitle,
                getUserEmail=getUserEmail,
                getCurrentUser=getCurrentUser,
                getClassHTML=getClassHTML,
                userAuthenticated=userAuthenticated,
                userAuthorized=userAuthorized)


# Routes #


@app.route('/')
def index():
    """ Application index page. Displays recent activity. """
    recent_items = session.query(Item)
    recent_items = recent_items.order_by(desc(Item.created))
    recent_items = recent_items.limit(10).all()
    return render_template('index.html', recent_items=recent_items)


@app.route('/.json')
def indexJSON():
    """ JSON version of application index. """
    recent_items = session.query(Item)
    recent_items = recent_items.order_by(desc(Item.created))
    recent_items = recent_items.limit(10).all()
    return jsonify(recent_items=[i.serialize for i in recent_items])


@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    """ Create a new category. """
    if not userAuthenticated():
        return redirect('/login')
    if request.method == 'POST':
        slug = generateSlug(request.form['category-name'])
        if findCategoryBySlug(slug):
            flash('A category by the name "%s" already exists.' %
                  request.form['category-name'])
            return render_template('category/new.html')
        new_category = Category(
            name=request.form['category-name'],
            user_id=login_session['user_id'],
            slug=slug)
        session.add(new_category)
        flash('New Category "%s" Successfully Created' % new_category.name)
        session.commit()
        return redirect(url_for('showCategory', slug=new_category.slug))
    else:
        return render_template('category/new.html')


@app.route('/catalog/')
@app.route('/category/')
def showCategories():
    """ Show all categories. """
    categories = session.query(Category).all()
    return render_template('category/index.html', categories=categories)


@app.route('/catalog.json')
@app.route('/catalog/.json')
@app.route('/category.json')
@app.route('/category/.json')
def showCategoriesJSON():
    """ Show all categories in JSON format. """
    categories = [c.serialize for c in session.query(Category).all()]
    return jsonify(categories=categories)


@app.route('/category/<string:slug>/')
def showCategory(slug):
    """ Show Category by slug. """
    category = findCategoryBySlug(slug)
    if category:
        items = session.query(Item).filter_by(category_id=category.id).all()
        return render_template('category/show.html',
                               category=category,
                               items=items)
    message = 'Category not found: "%s"' % slug
    return render_template('404.html', message=message)


@app.route('/category/<string:slug>.json')
@app.route('/category/<string:slug>/.json')
def showCategoryJSON(slug):
    """ Show Category by slug in JSON format. """
    category = findCategoryBySlug(slug)
    if category:
        items = session.query(Item).filter_by(category_id=category.id).all()
        data = {}
        data['category'] = category.serialize
        data['category']['items'] = [i.serialize for i in items]
        return jsonify(data)
    return jsonify({'Error': '404 Not Found'})


@app.route('/category/<string:slug>/edit/', methods=['GET', 'POST'])
def editCategory(slug):
    """ Edit Category by slug """
    if not userAuthenticated():
        return redirect('/login')
    category = findCategoryBySlug(slug)
    if category:
        if category.user_id != login_session['user_id']:
            flash('You are not authorized to edit this category')
            return redirect(url_for('showCategory', slug=category.slug))
        if request.method == 'POST':
            updated_name = request.form['category-name']
            updated_slug = generateSlug(updated_name)
            if category.name != updated_name:
                if findCategoryBySlug(updated_slug):
                    flash(
                        'Category "%s" already exists.' %
                        updated_name)  # pep8 E501
                    return render_template(
                        'category/edit.html', category=category)
            category.name = request.form['category-name']
            category.slug = generateSlug(category.name)
            flash('Category "%s" successfuly updated' % category.name)
            session.commit()
            return redirect(url_for('showCategory', slug=category.slug))
        else:
            return render_template('category/edit.html', category=category)
    message = message = 'Category not found: "%s"' % slug
    return render_template('404.html', message=message)


@app.route('/category/<string:slug>/delete', methods=['GET', 'POST'])
def deleteCategory(slug):
    """ Delete Category by slug. """
    if not userAuthenticated():
        return redirect('/login')
    category = findCategoryBySlug(slug)
    if category:
        if category.user_id != login_session['user_id']:
            flash('You are not authorized to delete this category')
            return redirect(url_for('showCategory', slug=category.slug))
        if request.method == 'POST':
            session.query(Item).filter_by(category_id=category.id).delete()
            session.delete(category)
            flash('Category "%s" successfuly deleted' % category.name)
            session.commit()
            return redirect(url_for('showCategories'))
        else:
            return render_template('category/delete.html', category=category)
    message = 'Category not found: "%s"' % slug
    return render_template('404.html', message=message)


@app.route('/category/<string:category_slug>/new', methods=['GET', 'POST'])
def newItem(category_slug):
    """ Create Item for a given category. """
    if not userAuthenticated():
        return redirect('/login')
    category = findCategoryBySlug(category_slug)
    if category:
        if request.method == 'POST':
            item = Item(name=request.form['item-name'],
                        slug=generateSlug(request.form['item-name']),
                        description=request.form['item-description'],
                        category_id=category.id,
                        user_id=login_session['user_id'])
            if findItemBySlug(category.slug, item.slug):
                flash_message = 'Item named "%s"' \
                                'already exists for this category.' \
                                % request.form['item-name']
                flash(flash_message)
                return render_template(
                    'item/new.html',
                    category=category,
                    item=item)  # pep8 E501
            session.add(item)
            flash('Item "%s" successfully added to category "%s"' %
                  (item.name, category.name))
            session.commit()
            return redirect(url_for(
                'showItem',
                category_slug=category.slug,
                item_slug=item.slug))
        else:
            return render_template('item/new.html', category=category)


@app.route('/category/<string:category_slug>/<string:item_slug>')
def showItem(category_slug, item_slug):
    """ Show item given category and item slugs. """
    category = findCategoryBySlug(category_slug)
    if category:
        item = findItemBySlug(category_slug, item_slug)
        if item:
            return render_template('item/show.html', item=item)
    return render_template(
        '404.html',
        message='Item not found: "%s/%s"'
        % (category_slug, item_slug))


@app.route('/category/<string:category_slug>/<string:item_slug>.json')
@app.route('/category/<string:category_slug>/<string:item_slug>/.json')
def showItemJSON(category_slug, item_slug):
    """ Show Item given category and item slugs in JSON format. """
    category = findCategoryBySlug(category_slug)
    if category:
        item = findItemBySlug(category_slug, item_slug)
        if item:
            data = {}
            data['item'] = item.serialize
            data['item']['category'] = category.serialize
            data['item']['user'] = item.user.serialize
            return jsonify(data)
    return jsonify({'Error': '404 Not Found'})


@app.route(
    '/category/<string:category_slug>/<string:item_slug>/edit',
    methods=['GET', 'POST'])  # pep8 E501
def editItem(category_slug, item_slug):
    """ Edit Item given category and item slugs. """
    if not userAuthenticated():
        return redirect('/login')
    category = findCategoryBySlug(category_slug)
    if category:
        item = findItemBySlug(category_slug, item_slug)
        if item:
            if item.user_id != login_session['user_id']:
                flash('You are not authorized to edit this category')
                return redirect(
                    url_for(
                        'showItem',
                        category_slug=category.slug,
                        item_slug=item.slug))  # pep8 E501
            if request.method == 'POST':
                updated_category = session.query(Category).filter_by(
                    id=request.form['item-category-id']).first()
                if updated_category.slug != category.slug and findItemBySlug(
                    updated_category.slug,
                    generateSlug(
                        request.form['item-name'])):  # pep8 E501
                        flash((
                            'Error: Item named "%s" '
                            'already exists for category "%s".') % (
                            request.form['item-name'], updated_category.name))
                        return render_template(
                            'item/edit.html',
                            category=category,
                            item=item)  # pep8 E501
                item.name = request.form['item-name']
                item.slug = generateSlug(request.form['item-name'])
                item.description = request.form['item-description']
                item.category_id = request.form['item-category-id']
                session.commit()
                flash('Item "%s" successfully updated' % item.name)
                return redirect(
                    url_for(
                        'showItem',
                        category_slug=item.category.slug,
                        item_slug=item.slug
                    )
                )  # pep8 E501
            else:
                return render_template(
                    'item/edit.html',
                    category=category,
                    item=item)  # pep8 E501
    return render_template(
        '404.html',
        message='Item not found: "%s/%s"' %
        (category_slug,
            item_slug))  # pep8 E501


@app.route(
    '/category/<string:category_slug>/<string:item_slug>/delete',
    methods=['GET', 'POST'])  # pep8 E501
def deleteItem(category_slug, item_slug):
    """ Delete Item given category and item slugs. """
    if not userAuthenticated():
        return redirect('/login')
    category = findCategoryBySlug(category_slug)
    if category:
        item = findItemBySlug(category_slug, item_slug)
        if item:
            if item.user_id != login_session['user_id']:
                flash('You are not authorized to delete this category')
                return redirect(
                    url_for(
                        'showItem',
                        category_slug=category.slug,
                        item_slug=item.slug))  # pep8 E501
            if request.method == 'POST':
                session.delete(item)
                flash('Item "%s" successfully deleted' % item.name)
                session.commit()
                return redirect(url_for('showCategory', slug=category.slug))
            else:
                return render_template(
                    'item/delete.html',
                    category=category,
                    item=item)  # pep8 E501
    return render_template(
        '404.html',
        message='Item not found: "%s/%s"' %
        (category_slug, item_slug))


@app.route('/user/')
def showUser():
    """ Show Current User. """
    user = getCurrentUser()
    if not user:
        flash('No user currently logged in.')
        return redirect(url_for('login'))
    categories = session.query(Category).filter_by(user_id=user.id).all()
    items = session.query(Item).filter_by(user_id=user.id).all()
    return render_template(
        'user/show.html',
        user=user,
        items=items,
        categories=categories)


@app.route('/user.json')
@app.route('/user/.json')
def showUserJSON():
    """ Show current User in JSON format. """
    user = getCurrentUser()
    categories = session.query(Category).filter_by(user_id=user.id).all()
    items = session.query(Item).filter_by(user_id=user.id).all()
    data = {}
    data['user'] = user.serialize
    data['user']['items'] = [i.serialize for i in items]
    data['user']['categories'] = [c.serialize for c in categories]
    return jsonify(data)


@app.route('/user/login/')
def login():
    """ Login user using anti-forgery state token. """
    state = generateKey(32)
    login_session.clear()
    login_session['state'] = state
    return render_template('user/login.html', STATE=state)


@app.route('/user/logout/', methods=['GET', 'POST'])
def logout():
    """ Logout user. """
    if not userAuthenticated():
        return redirect(url_for('login'))
    if request.method == 'POST':
        login_session.clear()
        flash('Successfully logged out.')
        return redirect(url_for('index'))
    return render_template('user/logout.html', user=login_session)


@app.route('/gconnect/', methods=['POST'])
def gconnect():
    """ Login user using google OAuth authorization code. """
    # Invalid state parameter.
    if request.args.get('state') != login_session['state']:
        return generateResponse(
            401,
            'Invalid state parameter.',
            'application/json')
    code = request.data
    # Attempt to ugprade authorization code.
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        return generateResponse(
            401,
            'Failed to upgrade the authorization code.',
            'application/json')
    # Authorization code is upgraded, use token to get user info.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    # Check for errors when getting user info.
    if result.get('error') is not None:
        return generateResponse(
            500,
            result.get('error'),
            'application/json')
    gplus_id = credentials.id_token['sub']
    # Check user id matches token id
    if result['user_id'] != gplus_id:
        return generateResponse(
            401,
            "Token's user ID doesn't match given user ID.",
            'application/json')
    # Check token is issued to app.
    if result['issued_to'] != CLIENT_ID:
        return generateResponse(
            401,
            "Token's client ID does not match app's.",
            'application/json')
    # Check is user is already logged in.
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        return generateResponse(
            200,
            'Current User is already connected',
            'application/json')
    else:
        # Everything worked properly.
        login_session['access_token'] = credentials.access_token
        login_session['gplus_id'] = gplus_id
        # Pull user info using access token.
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)
        data = answer.json()
        # Update login_session data with user info.
        login_session['name'] = data['name']
        login_session['picture'] = data['picture']
        login_session['email'] = data['email']
        # Check for existing user in database.
        user_id = getUserIDByEmail(login_session['email'])
        if not user_id:
            # Create user if none found.
            user_id = createUser(login_session)
        # Update logged in user id.
        login_session['user_id'] = user_id
        flash('You are now logged in as "%s"' % login_session['name'])
        return "success"

if __name__ == '__main__':
    # see if secret_key exists in database
    secret_key = session.query(KeyValue).filter_by(
        key='app_secret_key').first()
    if not secret_key:
        # create a secret key and add to database
        secret_key = KeyValue(
            key='app_secret_key',
            value=generateKey(80))
        session.add(secret_key)
        session.commit()  # pep8 E501
    # run app with secret key
    app.secret_key = secret_key.value
    app.debug = True
    app.run()
