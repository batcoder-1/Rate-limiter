from base import BaseClass
from pathlib import Path
base_dir=Path(__file__).parent
script=(base_dir/"scripts"/"sliding_window_log.lua").read_text()
class Sliding_Window_Log(BaseClass):
   rate_limit:int
   window_size:int
   def __init__(self,nameSpace,redis_client,rate_limit,window_size):
    if rate_limit <= 0 or window_size <= 0 :
            raise ValueError("Rate limit or Window size cannot be zero")
    super().__init__(redis_client,nameSpace)
    self.rate_limit=rate_limit
    self.window_size=window_size
    self.script=self.redis_client.register_script(script)
   def isAllow(self, user_id):
       allowed=self.script(
           keys=[f"{self.nameSpace}:{user_id}"],
           args=[f"{self.rate_limit}",f"{self.window_size}"]
       )
       return bool(allowed)