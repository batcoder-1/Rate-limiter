from base import BaseClass
from pathlib import Path

base_dir=Path(__file__).parent
script_path=(base_dir/"scripts"/"token_bucket.lua").read_text()
class Token_Bucket(BaseClass):
    bucket_capacity:int
    refill_rate:float
    def __init__(self,bucket_capacity,refill_rate,redis_client,nameSpace):
        super().__init__(redis_client,nameSpace)
        self.bucket_capacity=bucket_capacity
        self.refill_rate=refill_rate
        self.script=self.redis_client.register_script(script_path)

    def isAllow(self,user_id)->bool:
       allowed=self.script(
           keys=[f"{self.nameSpace}:{user_id}"],
           args=[f"{self.bucket_capacity}",f"{self.refill_rate}"]
       )
       return bool(allowed)