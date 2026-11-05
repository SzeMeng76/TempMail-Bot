# tempmail.id.vn API 客户端。
#
# 与 mail.tm 的根本差异：
#   - 没有密码、没有 token。身份是「API key 属于哪个账号」，邮箱挂在账号下。
#   - 读信靠 mail_id，且必须用建号时那个 key —— 换 key 就查不到。
#   - 没有迁移接口。想换账号只能删掉重建，且重建后 mail_id 会变（不是同一个邮箱）。
#   - 免费额度很紧：900 次读/月、20 次/分、50 个邮箱。绝不能轮询。

import requests
from requests.adapters import HTTPAdapter

BASE_URL = "https://tempmail.id.vn/api"
# 连接超时压到 5 秒：比 nginx 的 30 秒短得多。上游不可用时快速失败并返回
# 结构化错误，而不是让用户干等 30 秒才看到 502。
TIMEOUT = (5, 15)

# retries=0：连接超时不该被重试放大成 N 倍。
_session = requests.Session()
_adapter = HTTPAdapter(max_retries=0)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)


class TempMailEduError(Exception):
    """
    API 错误。

    retryable 表示「换个 key 再试可能有救」：额度满、限流属于这类；
    key 无效、域名不存在换了也白换，调度层据此决定是否顺延。

    kind 供调用方决定给用户看什么提示：
      auth     key 无效 / 未配置 —— 配置问题，用户无能为力
      quota    当月读信额度用尽或请求过快 —— 建议换个邮箱或换来源
      notfound 邮箱已被回收 —— 建议重新生成
      other    其余情况，直接把服务端消息透出去
    """

    def __init__(self, message, retryable=True, status=None, kind="other"):
        super().__init__(message)
        self.retryable = retryable
        self.status = status
        self.kind = kind


def _headers(api_key):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }


def _request(api_key, method, path, **kwargs):
    if not api_key:
        raise TempMailEduError("未配置 API key", retryable=False, kind="auth")

    try:
        response = _session.request(
            method, f"{BASE_URL}{path}", headers=_headers(api_key), timeout=TIMEOUT, **kwargs
        )
    except requests.RequestException as exc:
        # 网络层失败：上游挂了或超时，换 key 也没用，但过一会儿可能就好。
        raise TempMailEduError(f"网络不可达 ({exc.__class__.__name__})", retryable=False, kind="other")

    try:
        payload = response.json()
    except ValueError:
        raise TempMailEduError(
            f"响应不是 JSON (HTTP {response.status_code})",
            status=response.status_code,
            kind="other",
        )

    if response.status_code == 401:
        raise TempMailEduError("API key 无效", retryable=False, status=401, kind="auth")
    if response.status_code == 429:
        # 20 次/分的速率限制。等一会儿再试就行，不是月额度用完。
        raise TempMailEduError("请求过于频繁", status=429, kind="quota")
    if response.status_code == 404:
        raise TempMailEduError(
            payload.get("message") or "not found",
            retryable=False,
            status=404,
            kind="notfound",
        )
    if not response.ok or not payload.get("success", False):
        raise TempMailEduError(
            payload.get("message") or f"HTTP {response.status_code}",
            status=response.status_code,
            kind="other",
        )

    return payload.get("data")


def list_domains(api_key):
    """可用域名列表，如 ['tempmail.id.vn', '1trick.net', ...]。"""
    data = _request(api_key, "GET", "/domain") or []
    return [item["name"] for item in data if item.get("name")]


def create_mailbox(api_key, username=None, domain=None):
    """
    创建（或取回）邮箱。同名同域在**同一账号内**是幂等的，返回原邮箱。
    返回 {'address', 'id', 'created_at'}。
    """
    body = {}
    if username:
        body["user"] = username
    if domain:
        body["domain"] = domain

    data = _request(api_key, "POST", "/email/create", json=body)
    if not data or not data.get("email"):
        raise TempMailEduError("服务端未返回邮箱地址")

    return {
        "address": data["email"],
        "id": data["id"],
        "created_at": data.get("created_at") or "",
    }


def list_mailboxes(api_key):
    """该 key 账号下的全部邮箱。用于统计占用、挑选最旧的、以及按地址反查 id。"""
    data = _request(api_key, "GET", "/email") or []
    result = []
    for item in data:
        if not item.get("email") or item.get("id") is None:
            continue
        result.append(
            {
                "address": item["email"],
                "id": item["id"],
                "created_at": item.get("created_at") or "",
            }
        )
    return result


def delete_mailboxes(api_key, addresses):
    """
    按**邮箱地址**删除（接口不接受 id，传 id 会 422）。
    只能删自己账号下的邮箱，否则整批失败。
    """
    if not addresses:
        return []
    _request(api_key, "POST", "/email/delete", json={"emails": list(addresses)})
    return list(addresses)


def list_messages(api_key, mail_id):
    """某个邮箱的邮件列表。返回结构带分页，这里只取当前页。"""
    data = _request(api_key, "GET", f"/email/{mail_id}") or {}
    return data.get("items") or []


def get_message(api_key, message_id):
    """单封邮件详情。body 可能是 HTML，也可能是纯文本。"""
    return _request(api_key, "GET", f"/message/{message_id}") or {}


def sender_address(message):
    return message.get("from") or ""


def sender_name(message):
    return message.get("sender_name") or sender_address(message)


def subject(message):
    return message.get("subject") or ""
