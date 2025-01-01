from peewee import PostgresqlDatabase

# 数据库连接配置
db_new = PostgresqlDatabase(
    'main_site',
    user='postgres',
    password='postRy78XT',
    host='192.210.248.10',
    port=5432,
    options="-c search_path=aimazing",

)

def get_db():
    try:
        db_new.connect(reuse_if_open=True)
        return db_new
    except Exception as e:
        print(f"Database connection error: {e}")
        raise e
    
def close_db():
    if not db_new.is_closed():
        db_new.close()
