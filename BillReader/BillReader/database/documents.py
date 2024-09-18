import uuid
from typing import List, Optional
from config import *
from db import connection
from pydantic import UUID4, BaseModel, ConfigDict, Field
from pymongo import errors

_database = connection.get_database(DATABASE_NAME)

class BaseDocument(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_mongo(cls, data: dict):
        """Convert "_id" (str object) into "id" (UUID object)."""
        if not data:
            return data

        id = data.pop("_id", None)
        return cls(**dict(data, id=id))

    def to_mongo(self, **kwargs) -> dict:
        """Convert "id" (UUID object) into "_id" (str object)."""
        exclude_unset = kwargs.pop("exclude_unset", False)
        by_alias = kwargs.pop("by_alias", True)

        parsed = self.model_dump(
            exclude_unset=exclude_unset, by_alias=by_alias, **kwargs
        )

        if "_id" not in parsed and "id" in parsed:
            parsed["_id"] = str(parsed.pop("id"))

        return parsed

    def save(self, **kwargs):
        collection = _database[self._get_collection_name()]
        try:
            result = collection.insert_one(self.to_mongo(**kwargs))
            return result.inserted_id
        except errors.WriteError as e:
            # logger.error(f"Failed to insert document {e}")
            print(f"Failed to insert document {e}")
            return None

    @classmethod
    def get_or_create(cls, **filter_options) -> Optional[str]:
        collection = _database[cls._get_collection_name()]
        try:
            instance = collection.find_one(filter_options)
            if instance:
                return str(cls.from_mongo(instance).id)
            new_instance = cls(**filter_options)
            new_instance = new_instance.save()
            return new_instance
        except errors.OperationFailure as e:
            # logger.error(f"Failed to retrieve document: {e}")
            print(f"Failed to retrieve document: {e}")
            return None

    @classmethod
    def bulk_insert(cls, documents: List, **kwargs) -> Optional[List[str]]:
        print(cls._get_collection_name())
        collection = _database[cls._get_collection_name()]
        try:
            result = collection.insert_many(
                [doc.to_mongo(**kwargs) for doc in documents]
            )
            print(f"Successfully insert document")
            return result.inserted_ids
        except errors.WriteError as e:
            # logger.error(f"Failed to insert document {e}")
            print(f"Failed to insert document {e}")
            return None

    @classmethod
    def _get_collection_name(cls):
        if not hasattr(cls, "Settings") or not hasattr(cls.Settings, "name"):
            print("Document should define an Settings configuration class with the name of the collection.")

        return cls.Settings.name


class UserDocument(BaseDocument):
    first_name: str
    last_name: str

    class Settings:
        name = "users"


class RepositoryDocument(BaseDocument):
    name: str
    link: str
    content: dict
    owner_id: str = Field(alias="owner_id")

    class Settings:
        name = "repositories"


class PostDocument(BaseDocument):
    platform: str
    content: dict
    author_id: str = Field(alias="author_id")

    class Settings:
        name = "posts"


class ArticleDocument(BaseDocument):
    platform: str
    link: str
    content: dict
    author_id: str = Field(alias="author_id")

    class Settings:
        name = "articles"
