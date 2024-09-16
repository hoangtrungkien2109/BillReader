# from aws_lambda_powertools import Logger
from config import *
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


class MongoDatabaseConnector:
    _instance: MongoClient | None = None

    def __new__(cls, *args, **kwargs) -> MongoClient:
        if cls._instance is None:
            try:
                cls._instance = MongoClient(DATABASE_HOST)
            except ConnectionFailure as e:
                print(f"Couldn't connect to the database: {str(e)}")
                raise

        print(f"Connection to database with uri: {DATABASE_HOST} successful")
        return cls._instance

    def close(self):
        if self._instance:
            self._instance.close()
            print("Connection to database has been closed.")


connection = MongoDatabaseConnector()
