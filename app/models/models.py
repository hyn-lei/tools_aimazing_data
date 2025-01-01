from datetime import datetime
from peewee import *
from app.database import db_new

class BaseModel(Model):
    class Meta:
        database = db_new

class AITool(BaseModel):
    id = AutoField()
    status = CharField(max_length=255, default='draft')
    sort = IntegerField(null=True)
    date_created = DateTimeField(default=datetime.now)
    date_updated = DateTimeField(default=datetime.now)
    title = CharField(max_length=255, null=True)
    slug = CharField(max_length=255, null=True)
    summary = CharField(max_length=255, null=True)
    details = TextField(null=True)
    logo = UUIDField(null=True)  # 外键到 directus_files
    url = CharField(max_length=255, null=True)
    region = CharField(max_length=255, null=True)
    direct_access = IntegerField(default=1)
    free_plan = BooleanField(null=True)

    class Meta:
        table_name = 'ai_tools'

class AITag(BaseModel):
    id = AutoField()
    sort = IntegerField(null=True)
    title = CharField(max_length=255, null=True)
    slug = CharField(max_length=255, null=True, unique=True)

    class Meta:
        table_name = 'ai_tags'

class DataCategory(BaseModel):
    id = AutoField()
    name = CharField(max_length=255, null=True)
    slug = CharField(max_length=255, default='', unique=True)
    parent = ForeignKeyField('self', backref='children', null=True)
    page_content = TextField(null=True)
    sub_name = CharField(max_length=255, null=True)

    class Meta:
        table_name = 'data_categories'

class PricingPlan(BaseModel):
    id = AutoField()
    sort = IntegerField(null=True)
    name = CharField(max_length=255, null=True)
    tool = IntegerField(null=False)
    service = TextField(null=True)
    price_currency = CharField(max_length=255, null=True)
    price_month = CharField(max_length=255, null=True)
    price_year = CharField(max_length=255, null=True)
    price_lifetime = CharField(max_length=255, null=True)
    recommended = BooleanField(default=False)
    price_day = CharField(max_length=255, null=True)

    class Meta:
        table_name = 'pricing_plans'

class AIToolTag(BaseModel):
    id = AutoField()
    ai_tools = ForeignKeyField(AITool, backref='tags', null=True, field='id')
    ai_tags = ForeignKeyField(AITag, backref='tools', null=True, field='id')

    class Meta:
        table_name = 'ai_tools_ai_tags'

class AIToolCategory(BaseModel):
    id = AutoField()
    ai_tools = ForeignKeyField(AITool, backref='categories', null=True, field='id')
    data_categories = ForeignKeyField(DataCategory, backref='tools', null=True, field='id')

    class Meta:
        table_name = 'ai_tools_data_categories'
