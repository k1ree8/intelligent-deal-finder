from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AdRead(BaseModel):
    id: int
    title: str
    price: Optional[int] = None
    avito_id: int
    url: str
    published_at: datetime
    location: str

    class Config:
        orm_mode = True