from base import BaseClass
from pathlib import Path
base_dir=Path(__file__).parent
script=(base_dir/"scripts"/"leaky_bucket.lua").read_text()
class Leaky_Bucket(BaseClass):
  capacity_of_bucket:int
  leakage_rate:int
  def __init__(self,redis_client,nameSpace,bucket_capacity,leakage_rate):
    if leakage_rate <= 0 or bucket_capacity <= 0:
      raise ValueError("leakage rate and capacity cannot be zero")
    super().__init__(redis_client,nameSpace)
    self.capacity_of_bucket=bucket_capacity
    self.leakage_rate=leakage_rate
    self.script=self.redis_client.register_script(script)
  def isAllow(self, user_id):
    allowed=self.script(
      keys=[f"{self.nameSpace}:{user_id}"],
      args=[f"{self.capacity_of_bucket}",f"{self.leakage_rate}"]
    )
    return bool(allowed)