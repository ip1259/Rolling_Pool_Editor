import os
import csv
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class AttachEffectFilterCategoryParam(Base):
    __tablename__ = 'AttachEffectFilterCategoryParam'
    ID = Column(String, primary_key=True)
    textId = Column(String)
    category = Column(String)


class AttachEffectFilterParam(Base):
    __tablename__ = 'AttachEffectFilterParam'
    ID = Column(String, primary_key=True)
    filterTextId = Column(String)
    attachEffectFilterCategory = Column(String)


class AttachEffectFilterSubCategoryParam(Base):
    __tablename__ = 'AttachEffectFilterSubCategoryParam'
    ID = Column(String, primary_key=True)
    textId = Column(String)
    filterCategory = Column(String)


class AttachEffectParam(Base):
    __tablename__ = 'AttachEffectParam'
    ID = Column(String, primary_key=True)
    attachTextId = Column(String)
    attachFilterParamId = Column(String)
    passiveSpEffectId_1 = Column(String)


class AttachEffectTableParam(Base):
    __tablename__ = 'AttachEffectTableParam'
    row_id = Column(Integer, primary_key=True, autoincrement=True)
    ID = Column(String)
    attachEffectId = Column(String)
    unknown_0 = Column(String)
    Name = Column(String)
    chanceWeight = Column(Integer)
    chanceWeight_dlc = Column(Integer)


class SpEffectParam(Base):
    __tablename__ = "SpEffectParam"
    ID = Column(String, primary_key=True)
    spCategory = Column(String)

def import_csv_to_db(csv_folder="data/param", db_path="game_data/game_param.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    mapping = {
        "AttachEffectFilterCategoryParam": AttachEffectFilterCategoryParam,
        "AttachEffectFilterParam": AttachEffectFilterParam,
        "AttachEffectFilterSubCategoryParam": AttachEffectFilterSubCategoryParam,
        "AttachEffectParam": AttachEffectParam,
        "AttachEffectTableParam": AttachEffectTableParam,
        "SpEffectParam": SpEffectParam,
    }

    try:
        for file_name, model_cls in mapping.items():
            csv_file_path = os.path.join(csv_folder, f"{file_name}.csv")
            if not os.path.exists(csv_file_path):
                print(f"⚠️ 找不到檔案: {csv_file_path}，跳過此表。")
                continue

            print(f"📦 正在導入 {file_name}...")
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=',')

                records = []
                for row in reader:
                    data = {}
                    for column in model_cls.__table__.columns:
                        val = row.get(column.name)

                        if val is not None and val.strip() != "":
                            if isinstance(column.type, Integer):
                                data[column.name] = int(val)
                            else:
                                data[column.name] = str(val)
                        else:
                            data[column.name] = None

                    records.append(model_cls(**data))

                session.bulk_save_objects(records)

        session.commit()
        print("✅ 資料庫轉換完成！")
    except Exception as e:
        session.rollback()
        print(f"❌ 發生錯誤: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    import_csv_to_db(r"src\game_data_cvrt\data\param",
                     r"src\game_data\game_param.db")
