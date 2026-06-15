from pydantic import BaseModel, ConfigDict, field_validator

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


class SignedUrlRequest(BaseModel):
    filename: str
    content_type: str

    @field_validator("content_type")
    @classmethod
    def check_content_type(cls, v: str) -> str:
        if v not in _ALLOWED_CONTENT_TYPES:
            raise ValueError(f"不支援的圖片格式，允許：{_ALLOWED_CONTENT_TYPES}")
        return v


class SignedUrlResponse(BaseModel):
    signed_url: str
    public_url: str


class ImageRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    sort_order: int = 0


class AdminImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    sort_order: int


class ImageReorderItem(BaseModel):
    id: int
    sort_order: int


class ImageReorderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ImageReorderItem]
