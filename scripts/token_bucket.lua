user_id=KEYS[1] -- use hset and hmget or hashing as we are going to add ttl for inactive users
bucket_capacity=tonumber(ARGV[1]) 
refill_rate=tonumber(ARGV[2])
time=redis.call("TIME")
current_timestamp=time[1]
response=redis.call("GET",user_id)

if response == false then
    redis.call("MSET",user_id..":current_tokens",bucket_capacity-1,
                user_id..":last_timestamp",current_timestamp)
    return true
else
    current_tokens=redis.call("GET",user_id..":current_tokens")
    last_timestamp=redis.call("GET",user_id..":last_timestamp")
    current_tokens=math.min(bucket_capacity,(current_timestamp-last_timestamp)*refill_rate+current_tokens)
    if current_tokens>=1 then 
        current_tokens=current_tokens-1
        redis.call("MSET",user_id..":current_tokens",current_tokens,
                user_id..":last_timestamp",current_timestamp)
        return true
    end
      redis.call("MSET",user_id..":current_tokens",current_tokens,
                user_id..":last_timestamp",current_timestamp)
end
    return false