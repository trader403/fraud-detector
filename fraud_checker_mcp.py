import requests
import json

# 你的本地欺诈检测 API 地址
FRAUD_API_URL = "http://localhost:8000/predict"

def check_fraud(text: str) -> str:
    """
    调用本地欺诈检测 API，返回检测结果
    """
    try:
        response = requests.post(
            FRAUD_API_URL,
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2, ensure_ascii=False)
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "无法连接到欺诈检测 API，请确保 API 服务已启动。"})
    except requests.exceptions.Timeout:
        return json.dumps({"error": "欺诈检测 API 请求超时。"})
    except Exception as e:
        return json.dumps({"error": f"调用 API 时发生未知错误: {str(e)}"})

if __name__ == "__main__":
    # 可在此处进行本地测试
    test_text = "Your urgent bank account update is required. Click here to verify."
    print(check_fraud(test_text))