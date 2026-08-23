local user_id=KEYS[1] -- use hset and hmget or hashing as we are going to add ttl for inactive users
local bucket_capacity=tonumber(ARGV[1]) 
local refill_rate=tonumber(ARGV[2])
local time=redis.call("TIME")
local current_timestamp=time[1]
local response=redis.call("GET",user_id..":current_tokens")

if response == false then
    redis.call("MSET",user_id..":current_tokens",bucket_capacity-1,
                user_id..":last_timestamp",current_timestamp)
    return true
else
    local current_tokens=tonumber(redis.call("GET",user_id..":current_tokens"))
    local last_timestamp=tonumber(redis.call("GET",user_id..":last_timestamp"))
    current_tokens=math.min(bucket_capacity,(current_timestamp-last_timestamp)*refill_rate+current_tokens)
    if current_tokens>=1 then 
        redis.call("MSET",user_id..":current_tokens",current_tokens-1,
                user_id..":last_timestamp",current_timestamp)
        return true
    end
      redis.call("MSET",user_id..":current_tokens",current_tokens,
                user_id..":last_timestamp",current_timestamp)
end
    return false