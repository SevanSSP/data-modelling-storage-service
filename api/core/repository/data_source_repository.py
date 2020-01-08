from typing import List, Dict

from config import Config
from services.database import dmt_database
from core.enums import DataSourceDocumentType, DataSourceType


class DataSourceRepository:
    collection = dmt_database[f"{Config.DATA_SOURCES_COLLECTION}"]

    def list(self, document_type: DataSourceDocumentType) -> List[Dict]:
        all_sources = [
            {"id": "local", "host": "client", "name": "Local workspace", "type": DataSourceType.LOCAL.value}
        ]
        for data_source in self.collection.find(
            filter={"documentType": {"$regex": document_type.value}}, projection=["host", "name", "type"]
        ):
            data_source["id"] = data_source.pop("_id")
            all_sources.append(
                {
                    "id": data_source["id"],
                    "host": data_source["host"],
                    "name": data_source["name"],
                    "type": DataSourceType(data_source["type"]).value,
                }
            )
        return all_sources

    def create(self, id: str, document):
        document["_id"] = id
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    # def update(self, id: str):
    #     document = request.get_json()
    #     validate_mongo_data_source(document)
    #     result = self.collection.replace_one({"_id": id}, document, upsert=True)
    #     return str(result.acknowledged)
    #
    # def delete(self, id: str):
    #     result = self.collection.delete_one(filter={"_id": id})
    #     return result.acknowledged
