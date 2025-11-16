"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# Example schemas (keep for reference)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# AgentForge domain schemas

class Finding(BaseModel):
    rule_id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    line: Optional[int] = None
    description: str
    recommendation: str

class AgentStep(BaseModel):
    agent: str
    action: str
    output: str
    elapsed_ms: int

class Analysis(BaseModel):
    code: str
    language: str
    findings: List[Finding] = []
    steps: List[AgentStep] = []
    score: int = 0

class Metric(BaseModel):
    key: str
    value: int
