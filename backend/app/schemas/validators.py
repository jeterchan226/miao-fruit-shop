from typing import ClassVar, Self

from pydantic import BaseModel, model_validator


class RejectNullRequiredFields(BaseModel):
    required_fields: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _required_fields_not_null(self) -> Self:
        # 欄位可省略(不改),但必填欄位不可明確送 null 清空
        nulled = [
            f
            for f in self.required_fields
            if f in self.model_fields_set and getattr(self, f) is None
        ]
        if nulled:
            raise ValueError(f"必填欄位不可為 null: {', '.join(nulled)}")
        return self
