from playhouse.pool import PooledPostgresqlDatabase
import logging
from contextlib import contextmanager

# 数据库连接配置
db_new = PooledPostgresqlDatabase(
    'main_site',
    max_connections=8,
    stale_timeout=300,  # 5分钟超时
    timeout=30,  # 连接超时时间
    user='postgres',
    password='postRy78XT',
    host='192.210.248.10',
    port=5432,
    options="-c search_path=aimazing -c statement_timeout=30000"  # 30秒查询超时
)

def get_db():
    """获取数据库连接"""
    try:
        db_new.connect(reuse_if_open=True)
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        # 如果连接失败，尝试关闭后重新连接
        try:
            db_new.close()
            db_new.connect()
        except Exception as e:
            logging.error(f"Failed to reconnect to database: {str(e)}")
            raise

def close_db():
    """关闭数据库连接"""
    if not db_new.is_closed():
        db_new.close()

@contextmanager
def db_connection():
    """数据库连接的上下文管理器，自动处理连接和重连"""
    try:
        get_db()
        yield db_new
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise
    finally:
        close_db()

# 数据库连接事件处理
@db_new.connection_context()
def initialize_db():
    """初始化数据库连接"""
    try:
        db_new.connect()
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise

def close_db_pool():
    """关闭数据库连接池"""
    try:
        db_new.close_all()
        logging.info("Database connection pool closed")
    except Exception as e:
        logging.error(f"Error closing database pool: {str(e)}")
