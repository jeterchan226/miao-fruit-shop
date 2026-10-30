from collections.abc import Iterable

from pydantic import BaseModel


def reject_null_required_fields(model: BaseModel, required_fields: Iterable[str]) -> None:
    # 欄位可省略(不改),但必填欄位不可明確送 null 清空
    nulled = [
        f for f in required_fields if f in model.model_fields_set and getattr(model, f) is None
    ]
    if nulled:
        raise ValueError(f"必填欄位不可為 null: {', '.join(nulled)}")
