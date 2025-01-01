from typing import List

import httpx
import psycopg2
from datetime import datetime

from langchain.chains.llm import LLMChain
from langchain.chains.question_answering.map_rerank_prompt import output_parser
from langchain.output_parsers import StructuredOutputParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import OpenAI, ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

from config.config import settings

# 设置 OpenAI API Key
# openai.api_key = "your_openai_api_key"

# 使用 Langchain 的 LLM 接口
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    # streaming=True,
    # callbacks=cb,
    openai_api_base=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_KEY
)


# Step 1: 获取 HTML 数据
async def fetch_page_data(url):
    try:
        async with httpx.AsyncClient() as client:

            ga = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
            # cookie = 'WHMCS9YPENnfW6CSV=5f947993b9411e9089e27e2fec9c573f; _ga_6EQXLSG4QC=GS1.1.1733033145.1.0.1733033145.60.0.0; _ga=GA1.1.1002026121.1733033146; sib_cuid=a310d69f-0571-4fec-b0f9-b384b61f9dad; cf_clearance=NPf1GLf59x0_7aUvh9SS786sAKzO28aRBEIBisXg0vU-1733033145-1.2.1.1-kZ.8zi8JVp5ZLeHZhcwf2LaWm_CIUijoZcuKXDdBiOWJmb4Seod7IVH3P6F_pdhyYaBjSNiB0gqNH._hHUkxhl1sxVdAQasjYuVGq9XgYQ4B6SAR3FIB6..s9xZim492K8gunB_TESmGcMfuFgZmOht91TRcKm.mPG5V_uhhckOjqkKQK2mDJYKO_1l_ecz0__zelcNZ.iptkaWL6fh3zdLOg7TTrCt1jo6skqN1Wxj.a_Eplz9a9EIxeVB_gYYtPARalGvvia0VB_LlG_f4EN2ZtwMyPJA8KKVoecQ42RFRX4mfAi8RRgMWXc29guN6dhNl2sb9E1.KZHsHsN75qUXUnrSWXWT52L7gQDpTuJbs9IRrHoiqWG41XdB15TD3tuVN1H6rdVifz6qynL3eKQ'
            response = await client.get(url, headers={'User-Agent': ga})
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as exc:
        print(f"Error fetching page data: {exc.response.status_code}")
        return None
    except Exception as e:
        print(f"Error fetching page data: {e}")
        return None


class VPSPlanModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    vendor: str
    name: str
    cpu_core: int
    ssd: str
    network: str
    virtual_type: str
    price_monthly: float
    price_annually: float
    native_ip: str
    media_support: str
    refund_days: int
    support_region: str
    support_city: str
    remark: str = ''
    memory: str
    hidden_from_list: bool = False
    order_url: str
    traffic: str
    network_optimization_type: str
    pros: str = ''
    discount_code: str = ''
    pid: int


# Step 2: 使用 OpenAI 解析 HTML 数据
def extract_data_with_langchain(html_content):
    # 定义 prompt 模板
    prompt_template = """
    从以下 HTML 内容中提取多个 VPS 计划的数据。返回一个符合指定格式的 JSON 数组，且不包含任何解释性文本。

    HTML:
    {html_content}

    返回的 JSON 数据应该包含一个数组，其中每个对象是一个字典，包含以下字段：
    - vendor: 提供商名称，如果包含 CloudCone，填入 14；如果包含 HostDare，填入 10；如果包含 Cubecloud，填入17；\
        如果包含 saltyfish，填入16；\
        如果保护 AlphaVPS，填入 18；
    - title: 计划名称
    - cpu: CPU 核数，单纯数字表示，单位个数
    - storage: SSD 存储大小，单纯数字表示，单位GB
    - network: 网络带宽
    - price_monthly: 每月价格，如果没有设置为None，不需要做计算处理。如果能找到每季度，则使用每季度值/3，填入此字段
    - price_annually: 每年价格，如果没有设置为None，不需要做计算处理。
    - media_support: 支持的媒体，可选类型，Netflix,ChatGPT,Disney，如果没有留空。
    - region: 支持区域，US改成USA
    - city: 支持城市
    - memory: 内存大小，单纯数字表示，单位GB
    - order_url: 订购链接，如果 vendor 包含 CloudCone，在链接后面拼接参数 &ref=12163；如果 vendor 包含 HostDare，在链接后面拼接参数 &aff=3997；\
     如果 vendor 包含 cubecloud，order url 改成 https://www.cubecloud.net/aff.php?aff=2482&pid={{产品id}}；\
     如果 vendor 包含 saltyfish，order url 改成 https://portal.saltyfish.io/aff.php?aff=604&pid={{产品id}}；\
     如果 vendor 包含 AlphaVPS，order url 改成 https://alphavps.com/clients/aff.php?aff=809&pid={{产品id}}；
    - bandwidth: 带宽，单纯数字表示，单位TB
    - pros: 优点描述
    - remark: 备注信息
    - pid: 产品 ID，pid或者gid后面的数值，或者从 order_url 中获取；
    - discount_code: 折扣码，如果没有留空
    - network_optimization_type：网络优化类型，如果没有留空；CN2 GIA/GT表示的是电信网络优化，CU表示联通网络优化，CMI表示移动网络优化；

    请确保返回的 JSON 格式正确，并且每个 VPS 计划是一个字典对象。返回的 JSON 格式示例：

    [
      {{
        "vendor": "Vendor1",
        "title": "Plan 1",
        "cpu": "4",
        "storage": "100",
        "network": "1 Gbps",
        "price_monthly": 10.99,
        "price_annually": 99.99,
        "media_support": true,
        "region": "US",
        "city": "New York",
        "memory": "8",
        "order_url": "http://example.com/order1",
        "bandwidth": "-1",
        "pros": "High performance",
        "remark": "Best VPS plan",
        "pid": "12345",
        "network_optimization_type": "CN2",
        "discount_code": "DISCOUNT10"
      }},
      {{
        "vendor": "Vendor2",
        "title": "Plan 2",
        "cpu": "8",
        "storage": "200",
        "network": "2 Gbps",
        "price_monthly": 19.99,
        "price_annually": 179.99,
        "media_support": true,
        "region": "Europe",
        "city": "London",
        "memory": "16",
        "order_url": "http://example.com/order2",
        "bandwidth": "-1",
        "pros": "Excellent support",
        "remark": "Great value for money",
        "pid": "67890",
        "network_optimization_type": "",
        "discount_code": "DISCOUNT20"
      }}
    ]
    
    只返回上面要求的 JSON 数据格式，**不需要任何解释**。请确保返回的数据没有其他文本或说明。
    """

    out_parser = PydanticOutputParser(pydantic_object=VPSPlanModel)
    # 使用 PromptTemplate 创建 Langchain 的 Prompt
    prompt = PromptTemplate(
        input_variables=["html_content"],
        template=prompt_template,
        # partial_variables={
        #     "format_instructions": out_parser.get_format_instructions()
        # }
    )

    # 使用 Langchain 的 LLM 接口生成对话
    formatted_prompt = prompt.format_prompt(html_content=html_content.strip())

    json_schema = {
        "type": "object",
        "properties": {
            "vps_list": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "vendor": {"type": "string"},
                        "title": {"type": "string"},
                        "cpu": {"type": "string"},
                        "storage": {"type": "string"},
                        "network": {"type": "string"},
                        "price_monthly": {"type": "number"},
                        "price_annually": {"type": "number"},
                        "media_support": {"type": "string"},
                        "region": {"type": "string"},
                        "city": {"type": "string"},
                        "memory": {"type": "string"},
                        "order_url": {"type": "string"},
                        "bandwidth": {"type": "string"},
                        "pros": {"type": "string"},
                        "remark": {"type": "string"},
                        "pid": {"type": "string"},
                        "discount_code": {"type": "string"},
                        "network_optimization_type": {"type": "string"},
                    },
                    "required": [
                        "vendor",
                        "title",
                        "cpu",
                        "storage",
                        "network",
                        "price_monthly",
                        "price_annually",
                        "media_support",
                        "region",
                        "city",
                        "memory",
                        "order_url",
                        "bandwidth",
                        "pros",
                        "remark",
                        "pid",
                        "discount_code",
                        "network_optimization_type"
                    ]
                }
            }
        },
        # 可选的标题和描述
        "title": "VPSListSchema",
        "description": "A schema representing a list of VPS offerings."
    }

    # result= llm.invoke(formatted_prompt)

    # print(result.content)

    chain = prompt | llm.with_structured_output(json_schema)
    # chain = prompt | llm | out_parser
    result = chain.invoke({'html_content': html_content})
    print(result)

    return result
    # return response.strip()


# Step 3: 插入数据到数据库
def insert_vps_plan(data):
    try:
        # 连接到数据库，设置 search_path
        connection = psycopg2.connect(
            host="192.210.248.10",
            database="main_site",
            user="aimazing",
            password="aimazing_R!",
            options="-c search_path=vps_1kcode"
        )
        cursor = connection.cursor()

        # 创建插入语句
        insert_query = """
        INSERT INTO vps_plan (
            created_at,
            updated_at,
            vendor,
            name,
            cpu_core,
            ssd,
            network,
            virtual_type,
            price_monthly,
            price_annually,
            native_ip,
            media_support,
            refund_days,
            support_region,
            support_city,
            remark,
            memory,
            hidden_from_list,
            order_url,
            traffic,
            network_optimization_type,
            pros,
            discount_code,
            pid
        ) VALUES (
            %(created_at)s,
            %(updated_at)s,
            %(vendor)s,
            %(name)s,
            %(cpu_core)s,
            %(ssd)s,
            %(network)s,
            %(virtual_type)s,
            %(price_monthly)s,
            %(price_annually)s,
            %(native_ip)s,
            %(media_support)s,
            %(refund_days)s,
            %(support_region)s,
            %(support_city)s,
            %(remark)s,
            %(memory)s,
            %(hidden_from_list)s,
            %(order_url)s,
            %(traffic)s,
            %(network_optimization_type)s,
            %(pros)s,
            %(discount_code)s,
            %(pid)s
        )
        """

        # 执行插入操作
        cursor.execute(insert_query, data)
        connection.commit()
        print("数据插入成功")

    except Exception as e:
        print(f"插入数据时发生错误：{e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# Step 4: 使用提取的数据插入数据库
def insert_db(extracted_data):
    try:
        # 将返回的数据转换为 Python 对象
        data_list = extracted_data['vps_list']

        # 遍历数据列表，将每条数据插入数据库
        for outside_data in data_list:
            now = int(datetime.now().timestamp() * 1000)
            data = {
                'created_at': now,
                'updated_at': now,
                'vendor': outside_data['vendor'],
                'name': outside_data['title'],
                'cpu_core': outside_data['cpu'],
                'ssd': outside_data['storage'],
                'network': outside_data['network'],
                'virtual_type': 'KVM',
                'price_monthly': outside_data['price_monthly'],
                'price_annually': outside_data['price_annually'],
                'native_ip': True,
                'media_support': outside_data['media_support'],
                'refund_days': 0,
                'support_region': outside_data['region'],
                'support_city': outside_data["city"],
                'memory': outside_data['memory'],
                'hidden_from_list': False,
                'order_url': outside_data['order_url'],
                'traffic': outside_data['bandwidth'],
                'pros': outside_data['pros'],
                'remark': outside_data['remark'],
                'pid': outside_data['pid'],
                'discount_code': outside_data['discount_code'],
                'network_optimization_type': outside_data['network_optimization_type']
            }

            # 调用插入方法
            print(data)
            insert_vps_plan(data)
    except Exception as e:
        print(f"处理提取数据时发生错误：{e}")


# 主函数，URL 作为参数
async def process_vps_data(url):
    # Step 1: 获取 HTML 内容
    html_content = await fetch_page_data(url)
    # html_content=''''''
    print(html_content)
    # Step 2: 使用 Langchain 与 OpenAI 解析 HTML
    if html_content:
        extracted_data = extract_data_with_langchain(html_content)

        # Step 3: 插入数据到数据库
        if extracted_data:
            insert_db(extracted_data)


# 如果要调用主函数
if __name__ == "__main__":
    import asyncio

    # 示例 URL
    # url = "https://hello.cloudcone.com/bf-vps-sale-2024/"
    # url='https://hostdare.com/blackfriday.html'
    # url='https://www.cubecloud.net/store/lax-lite'
    # url='https://www.cubecloud.net/store/lax-pro'
    # url = 'https://www.cubecloud.net/store/hk-pro'
    # url = 'https://portal.saltyfish.io/store/sjc-elite'
    # url='https://portal.saltyfish.io/store/sjc-premium'
    # url='https://portal.saltyfish.io/store/sjc-standard'
    # url='https://portal.saltyfish.io/store/ams-premium'
    url = 'https://alphavps.com/clients/store/bf-2024'
    # 调用主函数
    asyncio.run(process_vps_data(url))
