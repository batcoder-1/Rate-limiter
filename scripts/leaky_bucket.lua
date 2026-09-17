local user=KEYS[1]
local bucket_capacity=tonumber(ARGV[1])
local leakage_rate=tonumber(ARGV[2])
local time=redis.call("TIME")
local current_timestamp=time[1]+time[2]/1000000
local response=redis.call("HGET",user,"current_capacity")
