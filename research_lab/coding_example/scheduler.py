def plan_runs(jobs, memory_limit):
    if memory_limit <= 0:
        raise ValueError("memory_limit must be positive")
    job_map = {j["id"]: j for j in jobs}
    if len(job_map) != len(jobs):
        raise ValueError("duplicate job IDs")
    for j in jobs:
        if j["ram"] <= 0 or j["ram"] > memory_limit:
            raise ValueError("nonpositive or excessive RAM")
        for n in j["needs"]:
            if n not in job_map:
                raise ValueError("unknown prerequisite")
    for j in jobs:
        if j["id"] in j["needs"]:
            raise ValueError("self-dependency")

    done = set()
    waves = []
    all_jobs = set(job_map.keys())

    while all_jobs:
        ready = []
        for j in job_map.values():
            if j["id"] in done:
                continue
            if all(n in done for n in j["needs"]):
                ready.append(j)

        if not ready:
            raise ValueError("dependency cycle")

        ready.sort(key=lambda x: (-x["priority"], x["id"]))

        wave = []
        current_ram = 0
        for j in ready:
            if current_ram + j["ram"] <= memory_limit:
                wave.append(j["id"])
                current_ram += j["ram"]

        if not wave:
            raise ValueError("dependency cycle")

        waves.append(wave)
        for j_id in wave:
            done.add(j_id)

        for j in job_map.values():
            if j["id"] in done:
                continue
            if any(n in done for n in j["needs"]):
                if not any(n in done for n in j["needs"]):
                    continue
                break

        all_jobs -= set(wave)

    return waves
