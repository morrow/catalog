# Catalog App

## Installation

This application requires [`Python3`](https://www.python.org/download/releases/3.0/) and installation of the following libraries:
    
    flask
    oauth2client
    sqlalchemy
    requests


If you are using Vagrant, these should already be installed in your virtual machine.
Otherwise these can be installed using the `requirements.txt` file and `pip3`:

    pip3 install -r requirements.txt

1) Once evertying is installed, create the database file by running `python3 database_setup.py`.
2) Then start the application using `python3 app.py`
3) Navigate to `http://localhost:5000` in your web browser to use the application.


## About

This is a simple CRUD application that uses [**Flask**](http://flask.pocoo.org/) and [**OAuth2**](https://oauth.net/2/) to allow authenticated users to create, read, update and destroy catalog objects.

A `User` object is automatically created when a user logins via a third party authentication service. The third-party service used in this application is [**Google**](https://developers.google.com/identity/protocols/OAuth2), so users of this application will need a [**Google**](https://accounts.google.com/SignUp?hl=en) account to create/edit/destroy objects.

The two types of objects `Users` can create, update, and destroy are: `Category` and `Item` objects:

### Category
    class Category(Base):
        id          # automatically incremented integer
        name        # string for name of object
        slug        # formatted version of name used to access object by name via URL
        user_id     # integer referring to the user that created the object
        user        # relationship to user
        created     # datetime when object was created
        updated     # datetime when object was last updated
### Item
    class Item(Base):
        id          # automatically incremented integer
        name        # string for name of object
        description # description of object
        category_id # integer referring to parent category
        category    # relationship to parent category
        slug        # formatted version of name used to access object by name via URL
        user_id     # integer referring to the user that created the object
        user        # relationship to user
        created     # datetime when object was created
        updated     # datetime when object was last updated
        
These objects are accessed via the following route patterns:

## HTML Routes
    deleteCategory                 GET,POST          /category/[slug]/delete
    deleteItem                     GET,POST          /category/[category_slug]/[item_slug]/delete
    editCategory                   GET,POST          /category/[slug]/edit/
    editItem                       GET,POST          /category/[category_slug]/[item_slug]/edit
    gconnect                       POST              /gconnect/
    index                          GET               /
    login                          GET               /user/login/
    logout                         GET,POST          /user/logout/
    newCategory                    GET,POST          /category/new/
    newItem                        GET,POST          /category/[category_slug]/new
    showCategories                 GET               /catalog/
    showCategories                 GET               /category/
    showCategory                   GET               /category/[slug]/
    showItem                       GET               /category/[category_slug]/[item_slug]
    showUser                       GET               /user/
    static                         GET               /static/[filename]
    
## JSON Routes
    indexJSON                      GET               /.json
    showCategoriesJSON             GET               /category.json
    showCategoriesJSON             GET               /category/.json
    showCategoriesJSON             GET               /catalog.json
    showCategoriesJSON             GET               /catalog/.json
    showCategoryJSON               GET               /category/[slug].json
    showCategoryJSON               GET               /category/[slug]/.json
    showItemJSON                   GET               /category/[category_slug]/[item_slug].json
    showItemJSON                   GET               /category/[category_slug]/[item_slug]/.json
    showUserJSON                   GET               /user/.json
    showUserJSON                   GET               /user/.json
