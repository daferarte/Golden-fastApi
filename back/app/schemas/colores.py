from pydantic import BaseModel

class RGBColorRequest(BaseModel):
    red: int
    green: int
    blue: int
