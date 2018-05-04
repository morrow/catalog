from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()


def createObjectFromProperties(self, properties):
    """ Create object from a list of properties. """
    object = {}
    for prop in properties:
        object[prop] = getattr(self, prop)
    return object


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(
        String(250))
    created = Column(
        DateTime,
        default=datetime.datetime.utcnow)  # pep8 E501
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.now)  # pep8 E501

    @property
    def serialize(self):
        properties = ['id', 'name', 'email', 'picture', 'created', 'updated']
        return createObjectFromProperties(self, properties)


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    slug = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.now)  # pep8 E501

    @property
    def serialize(self):
        properties = ['id', 'name', 'slug', 'user_id', 'created', 'updated']
        return createObjectFromProperties(self, properties)


class Item(Base):
    __tablename__ = 'item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    slug = Column(String(80))
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.now)

    @property
    def serialize(self):
        properties = [
            'id',
            'name',
            'slug',
            'description',
            'category_id',
            'user_id',
            'created',
            'updated']  # pep8 E501
        return createObjectFromProperties(self, properties)


class KeyValue(Base):
    __tablename__ = 'key_value'
    id = Column(Integer, primary_key=True)
    key = Column(String(80))
    value = Column(String(80))


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
