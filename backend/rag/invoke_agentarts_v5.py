"""
华为云 AgentArts 智能体调用（V11-HMAC-SHA256 手动签名）
文档：https://support.huaweicloud.com/api-agentarts/agentarts_07_0005.html
"""
import json
import uuid
import hashlib
import hmac
import datetime
import requests
from urllib.parse import urlparse

GATEWAY_DOMAIN = "defaultgw-mm2tkn3cmn.cn-southwest-2.huaweicloud-agentarts.com"
RUNTIME_NAME = "agent-arts-fb5aaa9d81df4fe19fef78cdcd8628a3"
INVOKE_URL = f"https://{GATEWAY_DOMAIN}/runtimes/{RUNTIME_NAME}/invocations"

AK = "HPUAYAWYTIRAY88QHK8A"
SK = "UYzuf5P9q5uTdkM61SSbQU3uHgQv1bkKvvRds4A4"


def hmac_sha256(key, msg):
    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(msg, str):
        msg = msg.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def sha256_hex(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sign_v11(method, url, headers, body=""):
    """
    V11-HMAC-SHA256 签名（不对body签名，使用UNSIGNED-PAYLOAD）
    """
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path

    sdk_date = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    headers["host"] = host
    headers["x-sdk-date"] = sdk_date
    headers["x-sdk-content-sha256"] = "UNSIGNED-PAYLOAD"

    signed_keys = sorted(k.lower() for k in headers.keys())
    canonical_headers = ""
    for k in signed_keys:
        orig = next(h for h in headers if h.lower() == k)
        val = headers[orig].strip()
        canonical_headers += f"{k}:{val}\n"
    signed_headers_str = ";".join(signed_keys)

    canonical_request = (
        f"{method.upper()}\n"
        f"{path}\n"
        f"\n"
        f"{canonical_headers}\n"
        f"{signed_headers_str}\n"
        f"UNSIGNED-PAYLOAD"
    )

    print(f"[调试] Canonical Request:\n{canonical_request}")
    print(f"[调试] Canonical Request Hash: {sha256_hex(canonical_request)}")

    string_to_sign = f"V11-HMAC-SHA256\n{sdk_date}\n{sha256_hex(canonical_request)}"
    print(f"[调试] String to Sign: {string_to_sign}")

    k_date = hmac_sha256(SK, sdk_date)
    k_signing = hmac_sha256(k_date, "V11-HMAC-SHA256")
    signature = hmac_sha256(k_signing, string_to_sign)
    print(f"[调试] Signature: {signature}")

    auth = (
        f"V11-HMAC-SHA256 "
        f"Credential={AK}/{sdk_date}, "
        f"SignedHeaders={signed_headers_str}, "
        f"Signature={signature}"
    )

    result_headers = {}
    for k, v in headers.items():
        if k.lower() != "host":
            result_headers[k] = v
    result_headers["Authorization"] = auth

    return result_headers


def invoke_agent(input_text, session_id=None):
    if session_id is None:
        session_id = str(uuid.uuid4()).replace("-", "")[:32]

    body = json.dumps({"input": input_text}, ensure_ascii=False)

    headers = {
        "Content-Type": "application/json",
        "X-Hw-Agentarts-Session-Id": session_id,
    }

    print(f"\n请求URL: {INVOKE_URL}")
    print(f"会话ID: {session_id}")
    print(f"输入: {input_text[:200]}")
    print("-" * 60)

    signed_headers = sign_v11("POST", INVOKE_URL, dict(headers), body)

    print("-" * 60)
    print(f"最终请求头:")
    for k, v in sorted(signed_headers.items()):
        print(f"  {k}: {v[:120]}")

    resp = requests.post(
        INVOKE_URL,
        headers=signed_headers,
        data=body.encode("utf-8"),
        timeout=120,
    )
    print(f"\n状态码: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    else:
        print(f"错误响应: {resp.text[:500]}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("V11-HMAC-SHA256 签名测试")
    print("=" * 60)
    invoke_agent("你好")