# tempmail.id.vn 的 web 侧最小中转服务。
#
# 为什么需要它：浏览器不能持有 API key（那是账号级凭证），也不能在多个 key
# 之间做「满了就删最旧」的决策 —— 那需要先列出该账号下所有邮箱，把所有人的
# 地址暴露给前端，而且任何人都能删别人的。
#
# 所以把这个能力放在这里：前端只看到自己那一个邮箱，池的调度全在服务端。
#
# 只用标准库，不引入额外依赖。

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import luuvan
import tempmailedu
import vnpool

PORT = int(os.environ.get("VNPROXY_PORT", "8091"))
# 只监听容器/本机，由外层反向代理转发进来。
HOST = os.environ.get("VNPROXY_HOST", "0.0.0.0")

MAX_BODY = 64 * 1024


def json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def error(handler, status, message, kind="other"):
    """
    kind 让前端能决定提示文案：
      quota    额度用完 / 限流 —— 建议换来源或重新生成
      notfound 邮箱已被回收 —— 建议重新生成
      auth     服务端没配 key —— 属于部署问题
      other    其余情况，直接显示 message
    """
    json_response(
        handler, status, {"success": False, "message": message, "kind": kind, "data": None}
    )


def success(handler, data):
    json_response(handler, 200, {"success": True, "message": "ok", "data": data})


def read_json(handler):
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    if length > MAX_BODY:
        raise ValueError("请求体过大")
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ValueError("请求体不是合法 JSON")


def message_view(message):
    """把上游的邮件结构收敛成前端要的形状。"""
    return {
        "id": str(message.get("id")),
        "from": message.get("from") or "",
        "sender_name": message.get("sender_name") or "",
        "subject": message.get("subject") or "",
        "body": message.get("body") or "",
        "created_at": message.get("created_at") or "",
        "read_at": message.get("read_at"),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "vnproxy"

    def log_message(self, fmt, *args):
        # 不要把完整地址写进日志，临时邮箱地址本身就算敏感信息。
        sys.stderr.write(f"{self.command} {urlparse(self.path).path}\n")

    # --- 路由 ---------------------------------------------------------------

    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        if path == "/domains":
            return self.handle_domains()
        if path == "/messages":
            return self.handle_messages(query)
        if path == "/message":
            return self.handle_message(query)
        if path == "/healthz":
            return success(self, {"ok": True})

        # luuvan.site：读信只要地址（服务端 catch-all），建号才需要 key。
        if path == "/lv/domains":
            return self.handle_lv_domains()
        if path == "/lv/messages":
            return self.handle_lv_messages(query)
        if path == "/lv/message":
            return self.handle_lv_message(query)
        return error(self, 404, "not found")

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/create":
                return self.handle_create()
            if path == "/delete":
                return self.handle_delete()
            if path == "/resolve":
                return self.handle_resolve()
            if path == "/lv/create":
                return self.handle_lv_create()
        except ValueError as exc:
            return error(self, 400, str(exc))
        return error(self, 404, "not found")

    # --- 实现 ---------------------------------------------------------------

    # --- luuvan -------------------------------------------------------------

    def handle_lv_domains(self):
        """
        luuvan 的域名单。读信不需要 key，所以这里没配 key 也算可用 ——
        只有建号才受游客额度限制，前端不该因此把整个来源隐藏掉。
        """
        try:
            return success(self, luuvan.domains())
        except luuvan.LuuvanError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))

    def handle_lv_create(self):
        # 没配 key 也能建号，但那是游客额度（5 个/天/IP、24 小时过期），
        # 通过 viaKey 告诉前端，让它有时间提醒用户。
        body = read_json(self)
        prefix = (body.get("prefix") or "").strip() or None
        domain = (body.get("domain") or "").strip() or None
        try:
            created = luuvan.create(prefix, domain)
        except luuvan.LuuvanError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))

        return success(
            self,
            {
                "address": created["address"],
                "expiresAt": created["expires_at"],
                "viaKey": created["via_key"],
            },
        )

    def handle_lv_messages(self, query):
        address = (query.get("address") or [""])[0].strip()
        if not address:
            return error(self, 400, "缺少 address")
        try:
            items = luuvan.list_messages(address)
        except luuvan.LuuvanError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))
        return success(self, items)

    def handle_lv_message(self, query):
        address = (query.get("address") or [""])[0].strip()
        message_id = (query.get("id") or [""])[0].strip()
        if not address or not message_id:
            return error(self, 400, "缺少 address 或 id")
        try:
            detail = luuvan.get_message(address, message_id)
        except luuvan.LuuvanError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))
        return success(self, detail)

    def handle_domains(self):
        if not vnpool.available():
            return error(self, 503, "未配置 API key")
        # 随便挑一个 slot 读域名即可，域名表是账号无关的。
        api_key = vnpool.key_for(0)
        try:
            return success(self, tempmailedu.list_domains(api_key))
        except tempmailedu.TempMailEduError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))

    def handle_create(self):
        if not vnpool.available():
            return error(self, 503, "未配置 API key")
        body = read_json(self)
        prefix = (body.get("prefix") or "").strip() or None
        domain = (body.get("domain") or "").strip() or None
        try:
            _slot, created = vnpool.create(prefix, domain)
        except tempmailedu.TempMailEduError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))

        # 不把 slot 和 evicted 细节暴露给前端；前端只需要地址。
        return success(self, {"address": created["address"]})

    def handle_resolve(self):
        """按地址查 id。删除后重建 id 会变，所以每次读信前都要解析。"""
        if not vnpool.available():
            return error(self, 503, "未配置 API key")
        body = read_json(self)
        address = (body.get("address") or "").strip()
        slot, mail_id = vnpool.resolve(address)
        if slot is None:
            return error(self, 404, "邮箱不存在或已被回收", "notfound")
        return success(self, {"address": address, "mail_id": mail_id})

    def handle_delete(self):
        if not vnpool.available():
            return error(self, 503, "未配置 API key")
        body = read_json(self)
        address = (body.get("address") or "").strip()
        if not address:
            return error(self, 400, "缺少地址")
        try:
            ok = vnpool.delete(address)
        except tempmailedu.TempMailEduError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))
        if not ok:
            return error(self, 404, "邮箱不存在", "notfound")
        return success(self, {"deleted": True})

    def handle_messages(self, query):
        if not vnpool.available():
            return error(self, 503, "未配置 API key")
        address = (query.get("address") or [""])[0].strip()
        if not address:
            return error(self, 400, "缺少 address")
        slot, mail_id = vnpool.resolve(address)
        if slot is None:
            return error(self, 404, "邮箱不存在或已被回收", "notfound")
        api_key = vnpool.key_for(slot)
        try:
            items = tempmailedu.list_messages(api_key, mail_id)
        except tempmailedu.TempMailEduError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))
        return success(self, [message_view(m) for m in items])

    def handle_message(self, query):
        if not vnpool.available():
            return error(self, 503, "未配置 API key")
        address = (query.get("address") or [""])[0].strip()
        message_id = (query.get("id") or [""])[0].strip()
        if not address or not message_id:
            return error(self, 400, "缺少 address 或 id")
        slot, _mail_id = vnpool.resolve(address)
        if slot is None:
            return error(self, 404, "邮箱不存在或已被回收", "notfound")
        api_key = vnpool.key_for(slot)
        try:
            detail = tempmailedu.get_message(api_key, message_id)
        except tempmailedu.TempMailEduError as exc:
            return error(self, 502, str(exc), getattr(exc, "kind", "other"))
        return success(self, message_view(detail))


def main():
    if not vnpool.available():
        sys.stderr.write("警告：未配置任何 TEMPMAIL_EDU_API_KEY_*，服务将一律返回 503\n")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    sys.stderr.write(f"vnproxy listening on {HOST}:{PORT} ({vnpool.slot_count()} key(s))\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
