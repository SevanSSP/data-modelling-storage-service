from typing import List

from core.domain.blueprint import Blueprint
from core.repository.mongo.mongo_repository_base import MongoRepositoryBase


class MongoBlueprintRepository(MongoRepositoryBase):
    class Meta:
        model = Blueprint

    def __init__(self, db):
        super().__init__(db)

    def get(self, uid: str) -> Blueprint:
        result = self.c().get(uid)
        if result:
            return self.convert_to_model(result)

    def update(self, document: Blueprint) -> None:
        self.c().update(document.uid, document.to_dict())

    def add(self, document: Blueprint) -> None:
        self.c().add(document.to_dict())

    def delete(self, document: Blueprint) -> None:
        self.c().delete(document.uid)

    def list(self):
        return [Blueprint.from_dict(document) for document in self.c().find(filters={})]

    def find_one(self, name: str) -> Blueprint:
        filters = {"name": name}
        adict = self.c().find_one(filters=filters)
        if adict:
            return Blueprint.from_dict(adict)

    def find(self, name: str) -> List[Blueprint]:
        filters = {"name": name}
        result = []
        for item in self.c().find(filters=filters):
            result.append(Blueprint.from_dict(item))
        return result