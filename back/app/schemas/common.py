# app/schemas/common.py
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    next: Optional[str] = None
    prev: Optional[str] = None
