#!/usr/bin/python3
"""
Contains the TestDBStorageDocs and TestDBStorage classes
"""

from datetime import datetime
import inspect
import models
from models.engine import db_storage
from models.amenity import Amenity
from models.base_model import BaseModel
from models.city import City
from models.place import Place
from models.review import Review
from models.state import State
from models.user import User
from contextlib import closing
import MySQLdb
import os
import pep8
import unittest

DBStorage = db_storage.DBStorage
classes = {"Amenity": Amenity, "City": City, "Place": Place,
           "Review": Review, "State": State, "User": User}


class TestDBStorageDocs(unittest.TestCase):
    """Tests to check the documentation and style of DBStorage class"""
    @classmethod
    def setUpClass(cls):
        """Set up for the doc tests"""
        cls.dbs_f = inspect.getmembers(DBStorage, inspect.isfunction)

    def test_pep8_conformance_db_storage(self):
        """Test that models/engine/db_storage.py conforms to PEP8."""
        pep8s = pep8.StyleGuide(quiet=True)
        result = pep8s.check_files(['models/engine/db_storage.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

    def test_pep8_conformance_test_db_storage(self):
        """Test tests/test_models/test_db_storage.py conforms to PEP8."""
        pep8s = pep8.StyleGuide(quiet=True)
        result = pep8s.check_files(['tests/test_models/test_engine/\
test_db_storage.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

    def test_db_storage_module_docstring(self):
        """Test for the db_storage.py module docstring"""
        self.assertIsNot(db_storage.__doc__, None,
                         "db_storage.py needs a docstring")
        self.assertTrue(len(db_storage.__doc__) >= 1,
                        "db_storage.py needs a docstring")

    def test_db_storage_class_docstring(self):
        """Test for the DBStorage class docstring"""
        self.assertIsNot(DBStorage.__doc__, None,
                         "DBStorage class needs a docstring")
        self.assertTrue(len(DBStorage.__doc__) >= 1,
                        "DBStorage class needs a docstring")

    def test_dbs_func_docstrings(self):
        """Test for the presence of docstrings in DBStorage methods"""
        for func in self.dbs_f:
            self.assertIsNot(func[1].__doc__, None,
                             "{:s} method needs a docstring".format(func[0]))
            self.assertTrue(len(func[1].__doc__) >= 1,
                            "{:s} method needs a docstring".format(func[0]))


@unittest.skipIf(models.storage_t != 'db', "not testing db storage")
class TestDBStorage(unittest.TestCase):
    """Test the DBStorage class"""
    def setUp(self):
        """
            Create a new storage variable. Will be deleted after each test.
            Creating a new storage variable for each test ensures that,
            if HBNB_ENV is set to test, all tables in the metadata will
            be deleted, and the tables will start the test empty.
        """
        self.storage = DBStorage()
        self.storage.reload()

    def tearDown(self):
        """ Remove the storage variable created at the start of the test """
        self.storage.close()
        del self.storage

    @staticmethod
    def execute_query(query):
        """
            Open a connection to the test db,
            execute a query, and close the connection
        """
        db_config = {'host': "localhost",
                     'user': "hbnb_test",
                     'passwd': "hbnb_test_pwd",
                     'db': "hbnb_test_db"
                     }

        with closing(MySQLdb.connect(**db_config)) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
        return result

    def test_new_and_save(self):
        """test that new adds an object to the database"""
        florida = State(name="Florida")
        fl_miami = City(name="Miami", state_id=florida.id)
        texas = State(name="Texas")
        tx_austin = City(name="Austin", state_id=texas.id)
        washington = State(name="Washington D.C.")
        data_list = [florida, texas, washington, fl_miami, tx_austin]
        for data in data_list:
            self.storage.new(data)
        self.storage.save()
        result = TestDBStorage.execute_query(
            "SELECT name, id FROM states"
        )
        self.assertTrue(len(result) == 3)
        self.assertTrue(florida.name in [r[0] for r in result])
        self.assertTrue(washington.id in [r[1] for r in result])

        result = TestDBStorage.execute_query(
            "SELECT name, id FROM cities"
        )
        self.assertTrue(len(result) == 2)
        self.assertTrue(tx_austin.name in [r[0] for r in result])

    def test_delete_no_arg(self):
        """Test the delete method on DBStorage"""
        # create state and verify it's saved
        florida = State(name="Florida")
        self.storage.new(florida)
        self.storage.save()
        result = TestDBStorage.execute_query(
            "SELECT name FROM states"
        )
        self.assertEqual(len(result), 1)

        # verify the delete method doesn't do anything if no argument
        self.storage.delete()
        self.storage.save()
        result = TestDBStorage.execute_query(
            "SELECT name FROM states"
        )
        self.assertEqual(len(result), 1)

    def test_delete_with_args(self):
        """Test the delete method with an argument"""
        # create state and verify it's saved
        florida = State(name="Florida")
        self.storage.new(florida)
        self.storage.save()
        result = TestDBStorage.execute_query(
            "SELECT name FROM states"
        )
        self.assertEqual(len(result), 1)

        # test method works correctly
        self.storage.delete(florida)
        self.storage.save()
        result = TestDBStorage.execute_query(
            "SELECT name FROM states"
        )
        self.assertEqual(len(result), 0)

    def test_all(self):
        """Test that all returns a dictionaty"""
        self.assertEqual(len(self.storage.all()), 0)
        florida = State(name="Florida")
        fl_miami = City(name="Miami", state_id=florida.id)
        self.storage.new(florida)
        self.storage.new(fl_miami)
        self.storage.save()
        self.assertEqual(len(self.storage.all()), 2)
        self.assertEqual(len(self.storage.all(State)), 1)
        self.assertEqual(len(self.storage.all(City)), 1)

    def test_get(self):
        """Test the get method"""
        result_not_found = self.storage.get(State, "123")
        self.assertEqual(result_not_found, None)
        florida = State(name="Florida")
        self.storage.new(florida)
        self.storage.save()
        result_found = self.storage.get(State, florida.id)
        self.assertEqual(florida.id, result_found.id)
        result_not_found = self.storage.get(City, florida.id)
        self.assertEqual(result_not_found, None)

    def test_count(self):
        """Test the count method"""
        self.assertEqual(self.storage.count(), 0)
        self.storage.new(State(name="Hawaii"))
        self.storage.save()
        self.assertEqual(self.storage.count(State), 1)
        self.storage.new(State(name="Oregon"))
        self.storage.new(State(name="Washington DC"))
        self.storage.new(State(name="Georgia"))
        self.storage.save()
        self.assertEqual(self.storage.count(State), 4)
        self.assertEqual(self.storage.count(City), 0)
