from fastapi.encoders import jsonable_encoder
from storage.repository_plugins.sql.models.blueprint_handling import SQLBlueprint, resolve_model, type_mapping
from sqlalchemy import create_engine, Column, String, Table, MetaData, text, select, inspect
from sqlalchemy.orm import sessionmaker,  aliased, selectinload
from storage.repository_interface import RepositoryInterface
from storage.repository_plugins.sql.models.base import Base
from common.utils.encryption import decrypt
import uuid
from storage.repository_plugins.sql.utils.hash import generate_hash

class Repository(RepositoryInterface):
    def __init__(
            self,
            username: str = "",
            password: str = "",
            host: str = "",
            database: str = "",
            port: int = 5432,
            engine=None,
            **kwargs,
    ):
        if engine is None:
            self.engine = create_engine(
                f"postgresql://{username}:{decrypt(password)}@{host}:{port}/{database}",
                connect_args={"options": "-c statement_timeout=5000"}
            )
        else:
            self.engine = engine
        self.get_blueprint = kwargs['get_blueprint']
        self.Session = sessionmaker(bind=self.engine)()
        self.metadata = MetaData()
        self.table_ref = Table(
            "BP_Addresses",
            self.metadata,
            Column('Name', String),
            Column('Address',String),
        )
        self.metadata.create_all(self.engine)

    def get(self,id:str,depth:int=0):
        entity = self.get_entity_by_query(id)
        return entity

    def sql_query(self,blueprint: str, id: str):
        def build_sql_query_from_blueprint(blueprint:str , columns: str):
            bp = self.get_blueprint.get_blueprint(blueprint).to_dict()
            hash = generate_hash(blueprint)
            for (i, attr) in enumerate(bp['attributes']):
                attr_name = attr['name']
                if not attr.get("dimensions") == "*" and attr["attributeType"] in type_mapping:
                    columns += f"'{attr_name}', {hash}.\"{attr_name}\", "
            columns = columns[:-2]
            for attr in bp['attributes']:
                attr_name = attr['name']
                if attr["attributeType"]=='object':
                    attr["attributeType"]="dmss://system/SIMOS/SQLReference"
                if 'dimensions' in attr and attr.get("dimensions") == "*" and attr["attributeType"] not in type_mapping:
                    child_hash = generate_hash(attr["attributeType"])
                    columns += f",'{attr_name}',  COALESCE((SELECT jsonb_agg(jsonb_build_object("
                    columns = build_sql_query_from_blueprint(attr["attributeType"], columns)
                    columns += f")) FROM {child_hash} JOIN {hash}_{child_hash}_map ON {child_hash}.id = {hash}_{child_hash}_map.{child_hash}_id WHERE {hash}.id = {hash}_{child_hash}_map.{hash}_id), '[]') "

                if (attr["attributeType"] not in type_mapping) and attr.get("dimensions") == "":

                    child_hash = generate_hash(attr["attributeType"])
                    columns += f",'{attr_name}', COALESCE((SELECT (jsonb_build_object("
                    columns = build_sql_query_from_blueprint(attr["attributeType"], columns)
                    columns += f")) FROM {child_hash} JOIN {hash}_{child_hash}_map ON {child_hash}.id = {hash}_{child_hash}_map.{child_hash}_id WHERE {hash}.id = {hash}_{child_hash}_map.{hash}_id), '[]') "
                if 'dimensions' in attr and attr["attributeType"] in type_mapping:
                    if attr['dimensions'] == '*' and attr["attributeType"] in type_mapping:
                        attr_name = attr['name']
                        columns += f",'{attr_name}',COALESCE((SELECT jsonb_agg({hash}_{attr_name}.data) FROM {hash}_{attr_name} WHERE {hash}_{attr_name}.{hash}_id = {hash}.id ),  '{{}}'::jsonb)"
            return columns
        s=build_sql_query_from_blueprint(blueprint,'')
        return f"SELECT jsonb_build_object({s}) FROM {generate_hash(blueprint)} WHERE {generate_hash(blueprint)}.id = '{id}';"

    def get_entity_by_query(self, id: str,depth:int=0) -> dict:
        session = self.Session
        metadata_obj = MetaData()
        metadata_obj.reflect(bind=self.engine)
        allowed_tables = [
            i for i in metadata_obj.tables
            if not (i.endswith("_map") or i == "BP_Addresses")
        ]

        try:
            inspector = inspect(self.engine)
            for table in allowed_tables:
                columns = [col['name'] for col in inspector.get_columns(table)]
                if 'id' in columns:
                    query = text(f'SELECT * FROM public."{table}" WHERE id = :id')
                    result = self.Session.execute(query, {'id': id}).first()

                    if result:
                        query = text(f'SELECT "Address" FROM public."BP_Addresses" WHERE "Name" = \'{table}\';')
                        table = session.execute(query).first()[0]
                        query = text(self.sql_query(table,id))
                        object = session.execute(query).first()[0]
                        object=self.replace_references(object)
                        return jsonable_encoder(object)
        except Exception as e:
            raise Exception(f"An error occurred: {str(e)}")

    def add(self,entity: dict, id:str):
        a = self._verify_blueprint(entity)
        if not a:
            self.add_table(entity['type'])
        try:
            self.add_insert(entity, id=id)
        except Exception as e:
            raise Exception(f"An error occurred: {str(e)}")


    def add_table(self, blueprint_address:str):
        session = self.Session
        metadata_obj = MetaData()
        metadata_obj.reflect(bind=self.engine)
        query = text(f'SELECT * FROM public."BP_Addresses" WHERE "Address" = \'{blueprint_address}\';')
        result = session.execute(query).first()
        if result:
            print(f"Blueprint already added to database")
            return jsonable_encoder(f"Blueprint already added to database")
        try:
            bp= self.get_blueprint.get_blueprint(blueprint_address).to_dict()
            bp = SQLBlueprint.from_dict(bp)
            bp.path=blueprint_address
            bp.paths = [[blueprint_address,bp.hash]]
            bp.generate_models_m2m_rel_with_paths(get_blueprint=self.get_blueprint)
            Base.metadata.create_all(self.engine)
            for i in range(len(bp.paths)):
                path,name = bp.paths[i][0], bp.paths[i][1]
                query = text('INSERT INTO public."BP_Addresses"("Name", "Address") VALUES (:name, :path);')
                query = query.bindparams(name=name, path=path)
                session.execute(query)
            session.commit()
            print(f"Blueprints:{bp.paths} succesfully added to sql database")
            return jsonable_encoder(f"Blueprints:{bp.paths} succesfully added to database")
        except Exception as e:
            raise Exception(f"An error occurred: {str(e)}")

    def add_insert(self, entity: dict, commit=True, id=None) -> dict:
        session=self.Session
        if 'type' not in entity:
            raise Exception('Attribute type not provided in entity')
        address = entity['type']
        model,bp = self._resolve_blueprint(address)
        data_table = {}
        children = []
        children_rel_names = []
        data = dict()
        for attr in bp.attributes:
            if attr.attributeType=='dmss://system/SIMOS/SQLReference':
                if attr.dimensions=='*':
                    references = []
                    for object in entity[attr.name]:
                        if object['type']=="dmss://system/SIMOS/SQLReference":
                            references.append(object)
                        # Generate a UUID4
                        else:
                            uid = str(uuid.uuid4())
                            reference={
                                "referenceType": "_object",
                                "type": "dmss://system/SIMOS/SQLReference",
                                "address": uid
                            }
                            references.append(reference)
                            self.add_table(object['type'])
                            self.delete(uid)
                            self.add_insert(object,id=uid)

                    entity[attr.name]=references
                else:
                    if entity[attr.name]['type'] != "dmss://system/SIMOS/SQLReference":
                        uid = str(uuid.uuid4())
                        reference = {
                            "referenceType": "_object",
                            "type": "dmss://system/SIMOS/SQLReference",
                            "address": uid
                        }
                        self.add_table(entity[attr.name]['type'])
                        self.delete(uid)
                        self.add_insert(entity[attr.name], id=uid)
                        entity[attr.name] = reference

        for key, value in entity.items():
            if key == '_id':
                continue

            attr = [attr for attr in bp.attributes if attr.name == key][0]
            if attr.attributeType.lower() in ["string", "integer", "number", "float", "boolean", "foreign_key",
                                              "type", "core:blueprintattribute"]:
                if hasattr(attr, 'dimensions') and attr.dimensions == '*':
                    data_table[key] = value
                else:
                    data[key] = value

            else:
                if isinstance(value, list):
                    children.extend(value)
                    [children_rel_names.append(key) for _ in value]
                elif isinstance(value, dict):
                    children.append(value)
                    children_rel_names.append(key)
                else:
                    raise NotImplementedError(f'Type {type(value)} not supported yet')

        obj_in_data = jsonable_encoder(data)
        db_obj = model(**obj_in_data)

        for child, rel_name in zip(children, children_rel_names):
            child_obj = self.add_insert(child, commit=True,id=None)
            getattr(db_obj, rel_name).append(child_obj)

        for key, value in data_table.items():
            data_table_model = resolve_model(blueprint=bp,get_blueprint=self.get_blueprint,data_table_name=key)
            data_table_objects = [data_table_model(data=item) for item in value]
            getattr(db_obj, key).extend(data_table_objects)
        if 'type' in entity:
            db_obj.type = entity['type']
        if '_id' in entity:
            db_obj.id=entity['_id']
        if id:
            db_obj.id = id
        session.add(db_obj)
        if commit:
            session.commit()
            session.refresh(db_obj)
        return db_obj
    def update(self,id:str,entity:dict):
        self.add_table(entity['type'])
        self.delete(id)
        self.add_insert(entity)

    def delete(self,id: str, table: str = None):
        session = self.Session
        metadata_obj = MetaData()
        metadata_obj.reflect(bind=self.engine)
        allowed_tables = [
            i for i in metadata_obj.tables
            if not (i.endswith("_map") or i == "BP_Addresses")
        ]

        try:
            inspector = inspect(self.engine)  # Assuming `self.engine` is your SQLAlchemy engine

            for table in allowed_tables:
                # Get the columns of the current table
                columns = [col['name'] for col in inspector.get_columns(table)]
                # Check if 'id' column exists
                if 'id' in columns:
                    query = text(f'SELECT * FROM public."{table}" WHERE id = :id')
                    result = self.Session.execute(query, {'id': id}).first()
                    if result:
                        query = text(f'SELECT "Address" FROM public."BP_Addresses" WHERE "Name" = \'{table}\';')
                        address = session.execute(query).first()[0]
                        if address:
                            model,bp=self._resolve_blueprint(address)
                            obj = self.Session.query(model).get(id)
                            parent_mapping_tables = [i for i in metadata_obj.tables if (i.endswith(f"{table}_map"))]
                            for j in parent_mapping_tables:
                                query = text(
                                    f'delete FROM public."{j}" WHERE "{table}_id" = \'{id}\';'
                                )
                                self.Session.execute(query)
                                self.Session.commit()
                            self.Session.delete(obj)
                            self.Session.flush()
                            self.Session.commit()
                            print(f"Successfully deleted {model.__name__}'{id}'")
        except Exception as e:
            raise Exception(f"An error occurred: {str(e)}")
    def _resolve_blueprint(self,address):
        bp = self.get_blueprint.get_blueprint(address).to_dict()
        bp = SQLBlueprint.from_dict(bp)
        bp.path = address
        model = resolve_model(blueprint=bp,data_table_name=None,get_blueprint=self.get_blueprint)
        return model,bp
    def _verify_blueprint(self, entity:dict):
        type=entity['type']
        session = self.Session
        metadata_obj = MetaData()
        metadata_obj.reflect(bind=self.engine)
        query = text(f'SELECT "Name" FROM public."BP_Addresses" WHERE "Address" = \'{type}\';')
        table = session.execute(query).first()
        if table:
            return True
        return False

    def sql_find_query(self,blueprint, search_data=None):
        def build_sql_query_from_blueprint(blueprint, search_data, columns, conditions=[], parent=[]):
            parent = parent
            bp = self.get_blueprint.get_blueprint(blueprint).to_dict()
            hash = generate_hash(blueprint)
            conds = ""
            parent.append(hash)
            for (i, attr) in enumerate(bp['attributes']):
                attr_name = attr['name']
                if not attr.get("dimensions") == "*" and attr["attributeType"] in type_mapping:
                    columns += f"'{attr_name}', {hash}.\"{attr_name}\", "
                    if search_data:
                        if attr_name in search_data:
                            if attr['attributeType'] == 'boolean' and isinstance(search_data[attr_name], str):
                                conds += f"{hash}.\"{attr_name}\"={search_data[attr_name].upper()} AND "
                            if attr['attributeType'] == 'boolean' and isinstance(search_data[attr_name], bool):
                                conds += f"{hash}.\"{attr_name}\"={str(search_data[attr_name])} AND "
                            if attr['attributeType'] == 'number' and isinstance(search_data[attr_name], str):
                                if search_data[attr_name][0] == '<' or '>':
                                    conds += f"{hash}.\"{attr_name}\"{search_data[attr_name][0]}{search_data[attr_name][1:]} AND "
                            if attr['attributeType'] == 'number' and isinstance(search_data[attr_name], float or int):
                                conds += f" {hash}.\"{attr_name}\" = {search_data[attr_name]} AND "
                            if attr['attributeType'] == 'number' and isinstance(search_data[attr_name], list):
                                for condition in search_data[attr_name]:
                                    if condition[0] == '<' or '>':
                                        conds += f"{hash}.\"{attr_name}\"{condition[0]}{condition[1:]} AND "
                            if attr['attributeType'] == 'number' and isinstance(search_data[attr_name], float or int):
                                conds += f" {hash}.\"{attr_name}\" = {search_data[attr_name]} AND "
                            if attr['attributeType'] == 'string' and isinstance(search_data[attr_name], str):
                                conds += f"{hash}.\"{attr_name}\"='{search_data[attr_name]}' AND "
            parent = parent[::-1]
            if len(conds) > 0 and len(parent) > 1:  #
                j = f"FROM {hash}"
                for i in range(len(parent) - 1):
                    if i == 0:
                        j += f" JOIN {parent[i + 1]}_{parent[i]}_map ON {parent[i]}.id={parent[i + 1]}_{parent[i]}_map.{parent[i]}_id"
                    if i > 0:
                        j += f" JOIN {parent[i + 1]}_{parent[i]}_map ON {parent[i]}_{parent[i - 1]}_map.{parent[i]}_id={parent[i + 1]}_{parent[i]}_map.{parent[i]}_id"

                conditions.append(
                    f"{j} WHERE {parent[-1]}.id={parent[-1]}_{parent[-2]}_map.{parent[-1]}_id AND {conds[:-4]}")
            elif len(conds)>0:
                conditions.append(f"FROM {hash} WHERE {conds[:-4]}")
            columns = columns[:-2]
            parent = parent[::-1]

            for attr in bp['attributes']:
                attr_name = attr['name']
                if attr["attributeType"] == 'object':
                    attr["attributeType"] = "dmss://system/SIMOS/SQLReference"
                    if attr_name in search_data:
                        del search_data[attr_name]
                if 'dimensions' in attr and attr.get("dimensions") == "*" and attr["attributeType"] not in type_mapping:
                    child_hash = generate_hash(attr["attributeType"])
                    columns += f",'{attr_name}',  COALESCE((SELECT jsonb_agg(jsonb_build_object("
                    new_search_data1 = None
                    if search_data and attr_name in search_data:
                        new_search_data1 = search_data[attr_name][0]
                    columns, conditions = build_sql_query_from_blueprint(attr["attributeType"], new_search_data1,
                                                                         columns, conditions=conditions, parent=parent)
                    parent.pop()
                    columns += f")) FROM {child_hash} JOIN {hash}_{child_hash}_map ON {child_hash}.id = {hash}_{child_hash}_map.{child_hash}_id WHERE {hash}.id = {hash}_{child_hash}_map.{hash}_id), '[]') "
                if (attr["attributeType"] not in type_mapping) and attr.get("dimensions") == "":
                    child_hash = generate_hash(attr["attributeType"])
                    columns += f",'{attr_name}', COALESCE((SELECT (jsonb_build_object("
                    new_search_data2 = None
                    if attr_name in search_data:
                        new_search_data2 = search_data[attr_name]
                    columns, conditions = build_sql_query_from_blueprint(attr["attributeType"], new_search_data2,
                                                                         columns, conditions=conditions, parent=parent)
                    parent.pop()
                    columns += f")) FROM {child_hash} JOIN {hash}_{child_hash}_map ON {child_hash}.id = {hash}_{child_hash}_map.{child_hash}_id WHERE {hash}.id = {hash}_{child_hash}_map.{hash}_id), '[]') "

                if 'dimensions' in attr and attr["attributeType"] in type_mapping:
                    if attr['dimensions'] == '*' and attr["attributeType"] in type_mapping:
                        attr_name = attr['name']
                        columns += f",'{attr_name}',COALESCE((SELECT jsonb_agg({hash}_{attr_name}.data) FROM {hash}_{attr_name} WHERE {hash}_{attr_name}.{hash}_id = {hash}.id ),  '{{}}'::jsonb))"
            return columns, conditions

        s, conditions = build_sql_query_from_blueprint(blueprint, search_data=search_data, columns='')
        c = ''
        if len(conditions) > 0:
            c = ''
            for i, string in enumerate(conditions):
                if i < 1 and string!='':
                    c += f"{string}"
                if i > 0 and string!='':
                    c += f" AND EXISTS (SELECT 1 {string})"
        return f"SELECT COALESCE((SELECT json_agg(jsonb_build_object({s})) {c}), '[]');"

    def replace_references(self,d: dict):
        if isinstance(d, dict):
            if d.get('type') == 'dmss://system/SIMOS/SQLReference' and d.get("referenceType") == '_object':
                d = self.get_entity_by_query(d.get("address"))
                return d
            return {key: self.replace_references(value) for key, value in d.items()}
        elif isinstance(d, list):
            return [self.replace_references(item) for item in d]
        else:
            return d

    def get_blob(self, uid):
        raise NotImplementedError

    def delete_blob(self, uid: str):
        raise NotImplementedError

    def update_blob(self, uid: str, blob: bytearray):
        raise NotImplementedError

    def find(self, filter: dict, single=None, raw=None) -> list[dict]:
        session = self.Session
        if 'name' in filter and 'isRoot' in filter:
            filter['type']="dmss://system/SIMOS/Package"
        if not 'type' in filter:
            raise Exception('Filter has no type attribute')
        ins = self._verify_blueprint(filter)
        if not ins:
            return []
        try:
            query = text(self.sql_find_query(filter['type'], search_data=filter))
            object = session.execute(query).first()[0]
            object = self.replace_references(object)
            return object
        except Exception as e:
            raise Exception(f"An error occurred: {str(e)}")

    def find_one(self, filters: dict) -> dict:
        raise NotImplementedError



