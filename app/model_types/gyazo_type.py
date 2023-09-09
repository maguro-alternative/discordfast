from pydantic import BaseModel

class GyazoJson(BaseModel):
    """
    Gyazoのjsonのデータ
    https://gyazo.com/api/docs/image
    """
    image_id        :str
    permalink_url   :str
    thumb_url       :str
    url             :str
    type            :str