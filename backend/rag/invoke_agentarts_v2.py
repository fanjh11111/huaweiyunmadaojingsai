"""
华为云 AgentArts 智能体调用脚本（使用官方SDK签名）
"""
import json
import uuid
import requests
from huaweicloudsdkcore.signer.signer import Signer
from huaweicloudsdkcore.sdk_request import SdkRequest
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.signer.algorithm import SigningAlgorithm

GATEWAY_DOMAIN = "defaultgw-mm2tkn3cmn.cn-southwest-2.huaweicloud-agentarts.com"
RUNTIME_NAME = "agent-arts-fb5aaa9d81df4fe19fef78cdcd8628a3"
INVOKE_URL = f"https://{GATEWAY_DOMAIN}/runtimes/{RUNTIME_NAME}/invocations"

AK = "HPUAYAWYTIRAY88QHK8A"
SK = "UYzuf5P9q5uTdkM61SSbQU3uHgQv1bkKvvRds4A4"


def invoke_agent(input_text, session_id=None, user_id=None):
    if session_id is None:
        session_id = str(uuid.uuid4()).replace("-", "")[:32]

    body = json.dumps({"input": input_text}, ensure_ascii=False)

    headers = {
        "Content-Type": "application/json",
        "X-Hw-Agentarts-Session-Id": session_id,
        "X-Sdk-Content-Sha256": "UNSIGNED-PAYLOAD",
    }
    if user_id:
        headers["X-Hw-Agentgateway-User-Id"] = user_id

    print(f"请求URL: {INVOKE_URL}")
    print(f"会话ID: {session_id}")
    print(f"输入: {input_text[:200]}")
    print("-" * 60)

    try:
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
            signing_algorithm=SigningAlgorithm.ECDSA_P256_SHA256,
        )

        signed_request = signer.sign(sdk_request)
        signed_headers = dict(signed_request.header_params)

        print(f"签名头: Authorization={signed_headers.get('Authorization', '')[:100]}...")
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
            print(f"错误响应: {resp.text}")
            if resp.status_code == 401:
                print("\n认证失败！")
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()

    return None


def invoke_rag_advice(component, fault_type, risk_level, confidence,
                      abnormal_features, description):
    input_data = {
        "component": component,
        "fault_type": fault_type,
        "risk_level": risk_level,
        "confidence": confidence,
        "abnormal_features": abnormal_features,
        "description": description,
    }
    return invoke_agent(json.dumps(input_data, ensure_ascii=False))


if __name__ == "__main__":
    print("=" * 60)
    print("测试1: 简单对话")
    print("=" * 60)
    invoke_agent("你好，请介绍一下你自己")

    print("\n" + "=" * 60)
    print("测试2: 航空发动机维修建议（高压涡轮叶片）")
    print("=" * 60)
    invoke_rag_advice(
        component="高压涡轮一级转子叶片",
        fault_type="叶片裂纹风险",
        risk_level="高",
        confidence=0.88,
        abnormal_features=["HPT_Blade_Vibration", "EGT_Margin_Drop"],
        description="高压涡轮一级转子叶片振动异常，EGT裕度下降",
    )