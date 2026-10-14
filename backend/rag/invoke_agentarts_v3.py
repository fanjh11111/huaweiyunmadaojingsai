"""
华为云 AgentArts 智能体调用脚本
方式：AK/SK签名获取IAM Token → X-Auth-Token调用智能体
"""
import json
import uuid
import requests
from huaweicloudsdkcore.signer.signer import Signer
from huaweicloudsdkcore.sdk_request import SdkRequest
from huaweicloudsdkcore.auth.credentials import BasicCredentials

REGION = "cn-southwest-2"
GATEWAY_DOMAIN = f"defaultgw-mm2tkn3cmn.{REGION}.huaweicloud-agentarts.com"
RUNTIME_NAME = "agent-arts-fb5aaa9d81df4fe19fef78cdcd8628a3"
INVOKE_URL = f"https://{GATEWAY_DOMAIN}/runtimes/{RUNTIME_NAME}/invocations"
IAM_ENDPOINT = f"https://iam.{REGION}.myhuaweicloud.com"

AK = "HPUAYAWYTIRAY88QHK8A"
SK = "UYzuf5P9q5uTdkM61SSbQU3uHgQv1bkKvvRds4A4"


def get_iam_token():
    """用AK/SK签名调用IAM API获取Token"""
    url = f"{IAM_ENDPOINT}/v3/auth/tokens"
    body = json.dumps({
        "auth": {
            "identity": {
                "methods": ["hw_ak_sk"],
                "hw_ak_sk": {
                    "access": {"key": AK},
                    "secret": {"key": SK},
                }
            },
            "scope": {
                "project": {
                    "name": REGION
                }
            }
        }
    }, ensure_ascii=False)

    headers = {"Content-Type": "application/json"}

    credentials = BasicCredentials(ak=AK, sk=SK)
    signer = Signer(credentials)

    sdk_request = SdkRequest(
        method="POST",
        schema="https",
        host=f"iam.{REGION}.myhuaweicloud.com",
        resource_path="/v3/auth/tokens",
        uri="",
        query_params=[],
        header_params=headers,
        body=body,
    )

    signed_request = signer.sign(sdk_request)
    signed_headers = dict(signed_request.header_params)

    print("获取IAM Token...")
    resp = requests.post(
        url,
        headers=signed_headers,
        data=body.encode("utf-8"),
        timeout=30,
    )
    print(f"IAM响应状态码: {resp.status_code}")

    if resp.status_code == 201:
        token = resp.headers.get("X-Subject-Token")
        print(f"Token获取成功: {token[:30]}...")
        return token
    else:
        print(f"Token获取失败: {resp.text[:500]}")
        return None


def invoke_agent_with_token(token, input_text, session_id=None):
    """用IAM Token调用智能体"""
    if session_id is None:
        session_id = str(uuid.uuid4()).replace("-", "")[:32]

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token,
        "X-Hw-Agentarts-Session-Id": session_id,
    }

    body = json.dumps({"input": input_text}, ensure_ascii=False)

    print(f"\n请求URL: {INVOKE_URL}")
    print(f"会话ID: {session_id}")
    print(f"输入: {input_text[:200]}")
    print("-" * 60)

    resp = requests.post(
        INVOKE_URL,
        headers=headers,
        data=body.encode("utf-8"),
        timeout=120,
    )
    print(f"状态码: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    else:
        print(f"错误响应: {resp.text[:500]}")
        return None


def invoke_agent_with_aksk(input_text, session_id=None):
    """直接用AK/SK签名调用智能体"""
    if session_id is None:
        session_id = str(uuid.uuid4()).replace("-", "")[:32]

    headers = {
        "Content-Type": "application/json",
        "X-Hw-Agentarts-Session-Id": session_id,
    }

    body = json.dumps({"input": input_text}, ensure_ascii=False)

    credentials = BasicCredentials(ak=AK, sk=SK)
    signer = Signer(credentials)

    sdk_request = SdkRequest(
        method="POST",
        schema="https",
        host=GATEWAY_DOMAIN,
        resource_path=f"/runtimes/{RUNTIME_NAME}/invocations",
        uri="",
        query_params=[],
        header_params=headers,
        body=body,
    )

    signed_request = signer.sign(sdk_request)
    signed_headers = dict(signed_request.header_params)

    print(f"\n请求URL: {INVOKE_URL}")
    print(f"会话ID: {session_id}")
    print(f"输入: {input_text[:200]}")
    print("-" * 60)

    resp = requests.post(
        INVOKE_URL,
        headers=signed_headers,
        data=body.encode("utf-8"),
        timeout=120,
    )
    print(f"状态码: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    else:
        print(f"错误响应: {resp.text[:500]}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("方式1: AK/SK签名直接调用")
    print("=" * 60)
    invoke_agent_with_aksk("你好")

    print("\n" + "=" * 60)
    print("方式2: AK/SK获取Token → Token调用")
    print("=" * 60)
    token = get_iam_token()
    if token:
        invoke_agent_with_token(token, "你好，请介绍一下你自己")