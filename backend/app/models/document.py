from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Text

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    filename: str = Field(index=True, max_length=255)
    content_type: Optional[str] = Field(default=None, max_length=100)
    size_bytes: int = Field(ge=0)

    text: Optional[str] = Field(default=None, sa_type=Text)

    agreement_type: Optional[str] = Field(default=None, index=True, max_length=100)
    governing_law: Optional[str] = Field(default=None, index=True, max_length=100)
    geography: Optional[str] = Field(default=None, index=True, max_length=100)
    industry: Optional[str] = Field(default=None, index=True, max_length=100)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
