"""阶段 1 · 《多模态视觉API》· 动手任务 2

任务：小票 OCR + 结构化校验。
1. 找一张购物小票或发票照片
2. 让视觉模型做 OCR 并输出结构化 JSON（商家、日期、商品明细列表、总金额）
3. 定义对应的 pydantic 模型校验输出，**复用 `ex07_pydantic_extract.py` 里的重试函数**
4. 校验成功后做一次业务检查：明细金额加起来等于总金额吗？不等说明什么？

要求/提示：
- 金额用 `Decimal` 或至少 float，别用 str；日期用 `date`/`datetime`
- 复用 ex07 的重试函数意味着你得把它写成可导入的形式——顺手体会一下"练习也要能被复用"
- 图片放哪：本目录下的 `data/` 已被根 `.gitignore` 忽略，图片放那里不会进 Git
- 完成标准：拿到一个通过校验的 pydantic 对象；金额核对逻辑跑通并打印结论
"""

import base64
import os
import pathlib
from datetime import date
from decimal import Decimal

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, ValidationError

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=600.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def img_to_data_url(path: pathlib.Path) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = path.suffix[1:].lower()
    return f"data:image/{'jpeg' if ext == 'jpg' else ext};base64,{b64}"


class Party(BaseModel):
    name: str = Field(..., description="Company name")
    taxpayer_id: str = Field(
        ..., description="Unified social credit code / taxpayer ID"
    )


class InvoiceItem(BaseModel):
    item_name: str
    specification: str | None = None
    unit: str | None = None
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    tax_rate: Decimal = Field(..., description="Tax rate, e.g. 0.06 for 6%")
    tax_amount: Decimal


class InvoiceTotal(BaseModel):
    amount: Decimal
    tax_amount: Decimal


class TotalWithTax(BaseModel):
    amount_in_words: str
    amount: Decimal


class Invoice(BaseModel):
    invoice_type: str
    invoice_number: str
    issue_date: date
    buyer: Party
    seller: Party
    items: list[InvoiceItem]
    total: InvoiceTotal
    total_with_tax: TotalWithTax
    remarks: str | None = None
    drawer: str
    download_count: int


def invoice_recognition(max_retries: int = 3) -> Invoice:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"识别图中信息，输出JSON，符合此Schema：\n{Invoice.model_json_schema()}",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img_to_data_url(
                            pathlib.Path(__file__).parent / "data" / "invoice.png"
                        )
                    },
                },
            ],
        }
    ]
    for attempt in range(max_retries):
        resp = client.chat.completions.create(
            model=os.environ["LLM_MODEL"],
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        if resp.choices[0].message.content is None:
            print(f"尝试 {attempt + 1}/{max_retries}，模型未返回内容")
            continue
        raw = resp.choices[0].message.content
        print(f"尝试 {attempt + 1}/{max_retries}，模型输出：{raw}")
        try:
            return Invoice.model_validate_json(raw)
        except ValidationError as e:
            # 把错误喂回去让模型自己改，比盲目重跑有效
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": f"输出未通过校验：{e}。请修正后重新输出JSON。",
                }
            )
    raise RuntimeError(f"结构化输出失败，已重试 {max_retries} 次")


def main() -> None:
    # 正常数据
    resume = invoice_recognition()
    print(resume)


if __name__ == "__main__":
    main()

# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run  .\ex09_ocr_json.py
# 尝试 1/3，模型输出：{
#   "invoice_type": "电子发票（普通发票）",
#   "invoice_number": "20000000000000000000",
#   "issue_date": "2026-07-30",
#   "buyer": {
#     "name": "示例科技有限公司",
#     "taxpayer_id": "91530100XXXXXXXXXA"
#   },
#   "seller": {
#     "name": "示例信息技术有限公司",
#     "taxpayer_id": "91110108XXXXXXXXXB"
#   },
#   "items": [
#     {
#       "item_name": "*生产生活服务*技术服务费",
#       "specification": null,
#       "unit": null,
#       "quantity": 1,
#       "unit_price": 1062.2641509434,
#       "amount": 1062.26,
#       "tax_rate": 0.06,
#       "tax_amount": 63.74
#     }
#   ],
#   "total": {
#     "amount": 1062.26,
#     "tax_amount": 63.74
#   },
#   "total_with_tax": {
#     "amount_in_words": "壹仟壹佰贰拾陆圆整",
#     "amount": 1126.00
#   },
#   "remarks": null,
#   "drawer": "张三",
#   "download_count": 1
# }
# invoice_type='电子发票（普通发票）' invoice_number='20000000000000000000' issue_date=datetime.date(2026, 7, 30) buyer=Party(name='示例科技有限公司', taxpayer_id='91530100XXXXXXXXXA') seller=Party(name='示例信息技术有限公司', taxpayer_id='91110108XXXXXXXXXB') items=[InvoiceItem(item_name='*生产生活服务*技术服务费', specification=None, unit=None, quantity=Decimal('1'), unit_price=Decimal('1062.2641509434'), amount=Decimal('1062.26'), tax_rate=Decimal('0.06'), tax_amount=Decimal('63.74'))] total=InvoiceTotal(amount=Decimal('1062.26'), tax_amount=Decimal('63.74')) total_with_tax=TotalWithTax(amount_in_words='壹仟壹佰贰拾陆圆整', amount=Decimal('1126')) remarks=None drawer='张三' download_count=1
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api>

# 明细加起来不等于总金额，因为明细+税才是总金额
