# luuvan.site API 客户端（Lưu Vân Mail）。
#
# 跟另外两个来源的根本差异，是「地址本身就是读信凭证」：
#   - GET /api/public/inbox?address=xxx  完全匿名，不需要 key、不需要 token、
#     也不需要事先建号。服务端是域名级 catch-all，收信按收件地址落库。
#   - GET /api/public/messages/:id?address=xxx  同上，取出正文。
#
# 这一点决定了它特别适合发卡密：卡密里直接写地址，买家拿到就能读，
# 我们不需要为每个卡密预留建号额度、也不用存任何「地址 → 凭证」的映射。
#
# 建号才需要 Bearer key，而且只有带 key 建的邮箱才是永久的：
#   - 带 key：POST /mailboxes        → expiresAt 在 100 年后
#   - 不带 key：POST /api/mailboxes  → 5 个/天/IP，且 24 小时过期
# 所以建号一律优先用 key；没有 key 时才退回游客建号。
#
# 注意：key 是账号级凭证，和 tempmail.id.vn 一样绝不能暴露给浏览器，
# web 侧建号必须经过 vnproxy 中转。

import os
import threading
import time

import requests
from requests.adapters import HTTPAdapter

BASE_URL = os.environ.get("LUUVAN_BASE_URL", "https://luuvan.site").rstrip("/")
API_KEY = os.environ.get("LUUVAN_API_KEY", "").strip()

# 跟 tempmailedu 一致：连接超时压短，上游挂掉时快速失败而不是让用户干等。
TIMEOUT = (5, 15)

# retries=0：超时不该被重试放大。
_session = requests.Session()
_adapter = HTTPAdapter(max_retries=0)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)


class LuuvanError(Exception):
    """
    kind 供调用方决定给用户看什么提示，跟 TempMailEduError 保持一致：
      auth      key 无效 —— 配置问题
      quota     游客建号额度用完 / 限流 —— 建议换来源或稍后再试
      notfound  邮箱或邮件不存在
      other    其余情况，直接把服务端消息透出去
    """

    def __init__(self, message, retryable=False, status=None, kind="other"):
        super().__init__(message)
        self.retryable = retryable
        self.status = status
        self.kind = kind


def _headers(with_key=False):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if with_key:
        if not API_KEY:
            raise LuuvanError("未配置 LUUVAN_API_KEY", retryable=False, kind="auth")
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def _request(method, path, with_key=False, **kwargs):
    try:
        response = _session.request(
            method, f"{BASE_URL}{path}", headers=_headers(with_key), timeout=TIMEOUT, **kwargs
        )
    except requests.RequestException as exc:
        raise LuuvanError(f"网络不可达 ({exc.__class__.__name__})", kind="other")

    try:
        payload = response.json()
    except ValueError:
        raise LuuvanError(f"响应不是 JSON (HTTP {response.status_code})", status=response.status_code)

    if response.ok:
        return payload

    message = payload.get("error") if isinstance(payload, dict) else None
    message = message or f"HTTP {response.status_code}"

    if response.status_code == 401:
        raise LuuvanError(message, status=401, kind="auth")
    if response.status_code == 403:
        raise LuuvanError(message, status=403, kind="auth")
    if response.status_code == 429:
        # 游客建号额度用完（5 个/天/IP）。换 key 或等明天。
        raise LuuvanError(message, retryable=True, status=429, kind="quota")
    if response.status_code == 404:
        raise LuuvanError(message, status=404, kind="notfound")

    raise LuuvanError(message, status=response.status_code)


def has_key():
    """是否有可用的 Bearer key。没有 key 也能读信，只是建号受游客额度限制。"""
    return bool(API_KEY)


# 域名表会被前端频繁拉取，缓存 10 分钟。官方域名不会几分钟变一次。
_domains_cache = {"value": [], "expires": 0.0}
_domains_lock = threading.Lock()


def domains():
    """
    当前可用的域名单（已排除 DNS 未生效的 pending 域名）：
    ['n0ai.cloud', 'animee.tokyo', ...]。读失败返回空列表，不影响主流程。
    """
    now = time.time()
    with _domains_lock:
        if _domains_cache["value"] and now < _domains_cache["expires"]:
            return list(_domains_cache["value"])

    try:
        payload = _request("GET", "/api/domains")
    except LuuvanError:
        return []

    pending = set(payload.get("pendingDomains") or [])
    values = [d for d in (payload.get("domains") or []) if d and d not in pending]

    with _domains_lock:
        _domains_cache["value"] = values
        _domains_cache["expires"] = now + 600
    return list(values)


def default_domain():
    values = domains()
    return values[0] if values else "n0ai.cloud"


def create(prefix=None, domain=None, ttl_minutes=None):
    """
    创建邮箱，返回 {'address', 'expires_at', 'recovery_key', 'via_key'}。

    带 key 走 /mailboxes（永久）；没有 key 才退回游客接口（5 个/天/IP、24h 过期）。
    同名同域重复创建按服务端行为返回已存在的那个。
    """
    body = {}
    if prefix:
        body["prefix"] = prefix
    if domain:
        body["domain"] = domain

    via_key = has_key()
    if via_key:
        payload = _request("POST", "/mailboxes", with_key=True, json=body)
        mailbox = payload.get("mailbox") or {}
        address = mailbox.get("address")
        expires_at = mailbox.get("expiresAt") or ""
        recovery_key = payload.get("recoveryKey") or ""
    else:
        if ttl_minutes:
            body["ttlMinutes"] = ttl_minutes
        payload = _request("POST", "/api/mailboxes", json=body)
        address = payload.get("address")
        expires_at = payload.get("expiresAt") or ""
        recovery_key = payload.get("recoveryKey") or ""

    if not address:
        raise LuuvanError("服务端未返回邮箱地址")

    return {
        "address": address,
        "expires_at": expires_at,
        "recovery_key": recovery_key,
        "via_key": via_key,
    }


def list_messages(address):
    """
    按地址读整个收件箱 —— 不需要 key，也不需要事先建号。

    返回 [{'id','from','subject','received_at','intro'}]，最新的在前。
    地址格式不合法时服务端会回 400，这里当成空列表处理更友好。
    """
    try:
        payload = _request(
            "GET", "/api/public/inbox", params={"address": address}
        )
    except LuuvanError as exc:
        if exc.status == 400:
            return []
        raise

    result = []
    for item in payload.get("messages") or []:
        result.append(
            {
                "id": str(item.get("id") or ""),
                "from": item.get("from") or "",
                "subject": item.get("subject") or "",
                "received_at": item.get("receivedAt") or "",
                "intro": item.get("intro") or "",
            }
        )
    return result


def get_message(address, message_id):
    """
    单封邮件详情。必须同时带 address —— 服务端拿它校验这封信属于该邮箱。

    返回 {'id','from','subject','received_at','text','html'}。
    """
    payload = _request(
        "GET",
        f"/api/public/messages/{message_id}",
        params={"address": address},
    )
    message = payload.get("message") or {}
    return {
        "id": str(message.get("id") or message_id),
        "from": message.get("from") or "",
        "subject": message.get("subject") or "",
        "received_at": message.get("receivedAt") or "",
        "text": message.get("text") or "",
        "html": message.get("html") or "",
    }


def delete(address):
    """删除邮箱（需要 key，且只能删自己 key 名下的）。返回是否成功。"""
    if not has_key():
        return False
    _request("DELETE", f"/mailboxes/{requests.utils.quote(address, safe='')}", with_key=True)
    return True


def sender_address(message):
    return message.get("from") or ""


def subject(message):
    return message.get("subject") or ""
