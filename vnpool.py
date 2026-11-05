# tempmail.id.vn 多账号池调度。
#
# 核心约束：邮箱归属于建它的那个 key，读信也必须用同一个 key。
# 所以「轮询」只能作用于「建号时挑哪个账号」，读信必须回到原 slot。
#
# 分摊的是两样东西：
#   1. 读信额度（900 次/月/账号）—— 轮询的真正目的
#   2. 邮箱数量上限（50 个/账号）—— 满了就删该账号下最旧的邮箱腾位置
#
# 删除只能按邮箱地址（接口不接受 id）。删除后同名重建会拿到新 id，
# 所以调用方不能缓存 mail_id，应该用地址重新解析。
#
# 这个模块同时被 bot 进程和 web 侧的轻服务 import，不要在这里引入
# 任何与 pyrogram / HTTP 框架相关的东西。

import os
import threading

import tempmailedu

MAX_SLOTS = 8
# 免费版每个账号 50 个邮箱；留 1 个余量避免刚好卡在上限上建号失败。
DEFAULT_MAILBOX_LIMIT = 49


def _load_keys():
    keys = []
    for slot in range(MAX_SLOTS):
        value = os.environ.get(f"TEMPMAIL_EDU_API_KEY_{slot}", "").strip()
        if value:
            keys.append((slot, value))
    return keys


_KEYS = _load_keys()
_lock = threading.Lock()
_cursor = 0

# 地址 → slot 的内存缓存。
#
# 没有它的话，每次读信都要把每个 key 的邮箱列表拉一遍才能定位到 id，
# 一次读信就会花掉 N+1 次请求 —— 在 900 次/月的额度下这是不可接受的。
# 只有缓存未命中（或该账号里查不到）时才回退到全量扫描。
_route_cache = {}


def _remember(address, slot):
    _route_cache[address.strip().lower()] = slot


def _forget(address):
    _route_cache.pop(address.strip().lower(), None)


def available():
    return bool(_KEYS)


def slot_count():
    return len(_KEYS)


def key_for(slot):
    """按 slot 取 key；该 slot 被移除时返回 None。"""
    for known_slot, key in _KEYS:
        if known_slot == slot:
            return key
    return None


def _mailbox_limit():
    raw = os.environ.get("TEMPMAIL_EDU_MAILBOX_LIMIT", "").strip()
    if raw.isdigit():
        return max(1, min(int(raw), 50))
    return DEFAULT_MAILBOX_LIMIT


def _make_room(slot, api_key, need=1):
    """
    确保该账号还能再放 need 个邮箱：不够就删最旧的。
    created_at 是 ISO 字符串，格式统一，可以直接按字符串排序。
    返回被删掉的地址列表。
    """
    limit = _mailbox_limit()
    mailboxes = tempmailedu.list_mailboxes(api_key)
    if len(mailboxes) + need <= limit:
        return []

    # 最旧的排前面：created_at 为空的一律当最旧，优先清掉。
    mailboxes.sort(key=lambda m: (m.get("created_at") or "", m["id"]))
    excess = len(mailboxes) + need - limit
    victims = [m["address"] for m in mailboxes[:excess]]
    if victims:
        tempmailedu.delete_mailboxes(api_key, victims)
    return victims


def create(prefix=None, domain=None):
    """
    创建（或取回）邮箱，自动在多个 key 之间分摊。

    返回 (slot, {'address', 'id', 'evicted': [...]})。
    全部 key 都失败时抛出最后一个错误。
    """
    global _cursor

    if not _KEYS:
        raise tempmailedu.TempMailEduError("未配置任何 tempmail.id.vn API key", retryable=False)

    with _lock:
        total = len(_KEYS)
        start = _cursor
        last_error = None

        for offset in range(total):
            slot, api_key = _KEYS[(start + offset) % total]
            try:
                evicted = _make_room(slot, api_key)
                created = tempmailedu.create_mailbox(api_key, prefix, domain)
            except tempmailedu.TempMailEduError as exc:
                # key 失效 / 域名不存在属于配置问题，换 key 也没用。
                if not exc.retryable:
                    raise
                last_error = exc
                continue

            _cursor = (start + offset + 1) % total
            # 建号时顺手记下地址归属，省掉第一次读信的全量扫描。
            _remember(created["address"], slot)
            created["evicted"] = evicted
            return slot, created

        raise last_error or tempmailedu.TempMailEduError("所有账号都不可用")


def resolve(address):
    """
    按完整邮箱地址找出它属于哪个 slot、当前 id 是多少。

    返回 (slot, id)；找不到返回 (None, None)。
    删除后重建的地址 id 会变，所以读信前用它重新解析比缓存 id 更可靠。
    """
    target = (address or "").strip().lower()
    if not target:
        return None, None

    # 优先走内存缓存：正常路径下只需要 1 次请求就能定位。
    cached_slot = _route_cache.get(target)
    if cached_slot is not None:
        api_key = key_for(cached_slot)
        if api_key:
            try:
                for item in tempmailedu.list_mailboxes(api_key):
                    if item["address"].lower() == target:
                        return cached_slot, item["id"]
            except tempmailedu.TempMailEduError:
                pass
        # 缓存失效（邮箱被删 / key 被移除），回退到全量扫描并纠正。
        _forget(target)

    for slot, api_key in _KEYS:
        try:
            mailboxes = tempmailedu.list_mailboxes(api_key)
        except tempmailedu.TempMailEduError:
            continue
        for item in mailboxes:
            if item["address"].lower() == target:
                _remember(target, slot)
                return slot, item["id"]

    return None, None


def delete(address):
    """删除一个邮箱。返回是否删除成功。"""
    slot, _mail_id = resolve(address)
    if slot is None:
        return False
    api_key = key_for(slot)
    if not api_key:
        return False
    tempmailedu.delete_mailboxes(api_key, [address])
    _forget(address)
    return True


def domains():
    """
    当前可用的域名单。域名表是账号无关的，读一个 slot 就够；
    读失败不影响主流程，返回空列表由调用方回落到其他来源。
    """
    if not _KEYS:
        return []
    api_key = _KEYS[0][1]
    try:
        return tempmailedu.list_domains(api_key)
    except tempmailedu.TempMailEduError:
        return []
