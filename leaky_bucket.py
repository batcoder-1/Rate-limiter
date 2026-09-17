from base import BaseClass
from pathlib import Path
base_dir=Path(__file__).parent
script=(base_dir/"scripts"/"leaky_bucket.lua").read_text()
class Leaky_Bucket(BaseClass):
  capacity_of_bucket:int
  leakage_rate:int
  def __init__(self,redis_client,nameSpace,capacity,rate):
    if rate == 0:
      raise ValueError("leakage rate cannot be zero")
    super().__init__(redis_client,nameSpace)
    self.capacity_of_bucket=capacity
    self.leakage_rate=rate
    self.script=self.redis_client.register_script(script)
  def isAllow(self, user_id):
    allowed=self.script(
      keys=[f"{self.nameSpace}:{user_id}"],
      args=[f"{self.capacity_of_bucket}",f"{self.leakage_rate}"]
    )
    return bool(allowed)