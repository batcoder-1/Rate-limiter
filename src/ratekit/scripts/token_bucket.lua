local user_id=KEYS[1]
local bucket_capacity=tonumber(ARGV[1]) 
local refill_rate=tonumber(ARGV[2])
local time=redis.call("TIME")
local current_timestamp=time[1]+time[2]/1000000
local response=redis.call("HGET",user_id,"current_tokens")
local ttl_time
if refill_rate == 0 then
    ttl_time=bucket_capacity

else
    ttl_time=math.ceil(bucket_capacity/refill_rate)+5
end
    if response == false then
    redis.call("HSET",user_id,"current_tokens",bucket_capacity-1,"last_timestamp",current_timestamp)
    redis.call("EXPIRE",user_id,ttl_time)
    return true
else
    local current_tokens=tonumber(redis.call("HGET",user_id,"current_tokens"))
    local last_timestamp=tonumber(redis.call("HGET",user_id,"last_timestamp"))
    current_tokens=math.min(bucket_capacity,(current_timestamp-last_timestamp)*refill_rate+current_tokens)
    if current_tokens>=1 then 
        redis.call("HSET",user_id,"current_tokens",current_tokens-1,"last_timestamp",current_timestamp)
        redis.call("EXPIRE",user_id,ttl_time)
        return true
    end
      redis.call("HSET",user_id,"current_tokens",current_tokens,"last_timestamp",current_timestamp)
      redis.call("EXPIRE",user_id,ttl_time)
end
    return false