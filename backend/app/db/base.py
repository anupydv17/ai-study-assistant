"""The declarative base every database model inherits from.

SQLAlchemy uses this class to keep a registry of all tables. When a model
subclasses Base, it is automatically added to Base.metadata, which is how
create_all() knows what tables to build.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Parent class for all ORM models in this project."""
