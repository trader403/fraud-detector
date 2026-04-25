import time
import csv
import uuid
import re
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import joblib
import jieba

# ==================== 配置 ====================
EN_MODEL_PATH = 'lgbm_fraud_model_v2.pkl'
EN_VECTORIZER_PATH = 'tfidf_vectorizer_v2.pkl'
EN_THRESHOLD = 0.581

ZH_MODEL_PATH = 'chinese_fraud_model_v2/lgbm_fraud_zh_model.pkl'
ZH_VECTORIZER_PATH = 'chinese_fraud_model_v2/tfidf_vectorizer_zh.pkl'
ZH_THRESHOLD = 0.599

LOG_FILE = 'audit_log.csv'

# ==================== 日志 ====================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fraud-api")

# ==================== 加载模型 ====================
try:
    en_tfidf = joblib.load(EN_VECTORIZER_PATH)
    en_model = joblib.load(EN_MODEL_PATH)
    logger.info(f"✅ 英文模型加载成功 (阈值={EN_THRESHOLD})")

    zh_tfidf = joblib.load(ZH_VECTORIZER_PATH)
    zh_model = joblib.load(ZH_MODEL_PATH)
    logger.info(f"✅ 中文模型加载成功 (阈值={ZH_THRESHOLD})")
except Exception as e:
    logger.error(f"❌ 模型加载失败: {e}")
    raise RuntimeError(f"模型加载失败: {e}")

# ==================== 中文预处理 ====================
def clean_chinese_text(text: str) -> str:
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
    words = jieba.lcut(text)
    words = [w.strip() for w in words if len(w.strip()) > 1]
    return ' '.join(words)

# ==================== 中文高危规则 ====================
CN_HIGH_RISK_PATTERNS = [
    r'兼职.*日.*赚', r'无需.*押金', r'日.*薪.*(过|超|高)', r'加QQ', r'加微信.*赚',
    r'打字.*员', r'在家.*赚钱', r'安全.*可靠.*收益', r'联系.*客服.*领取',
    r'您.*中奖', r'您.*获得.*(奖金|大奖)', r'特价.*优惠.*仅限今天'
]

def cn_rule_check(text: str) -> float:
    for pattern in CN_HIGH_RISK_PATTERNS:
        if re.search(pattern, text):
            return 0.95
    return -1

# ==================== 语言检测 ====================
def detect_language(text: str) -> str:
    if re.search(r'[\u4e00-\u9fa5]', text):
        return "zh"
    return "en"

# ==================== FastAPI ====================
app = FastAPI(title="AI Fraud Detection Engine", version="4.0.0")

# 静态文件服务（前端页面放在同级目录下的 static 文件夹）
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ==================== 请求/响应模型 ====================
class DetectionRequest(BaseModel):
    text: str = Field(..., min_length=1)
    lang: str = Field(default="auto")

class DetectionResult(BaseModel):
    id: str
    text: str
    lang: str
    fraud_probability: float
    is_fraud: bool
    risk_level: str
    threshold: float
    processing_time_ms: float

def classify(prob: float) -> str:
    if prob >= 0.8:
        return "high"
    elif prob >= 0.5:
        return "medium"
    return "low"

# ==================== 日志记录 ====================
def log_request(text, lang, prob, is_fraud):
    file_exists = Path(LOG_FILE).exists()
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "text", "lang", "fraud_probability", "is_fraud"])
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), text, lang, prob, is_fraud])

# ==================== 核心分析函数 ====================
def analyze_text(text: str, lang: str) -> DetectionResult:
    start = time.time()

    if lang == "zh":
        # 规则优先
        rule_prob = cn_rule_check(text)
        if rule_prob > 0:
            prob = rule_prob
        else:
            processed = clean_chinese_text(text)
            vec = zh_tfidf.transform([processed])
            prob = zh_model.predict_proba(vec)[0, 1]
        threshold = ZH_THRESHOLD
    else:
        vec = en_tfidf.transform([text])
        prob = en_model.predict_proba(vec)[0, 1]
        threshold = EN_THRESHOLD

    elapsed = (time.time() - start) * 1000
    is_fraud = prob >= threshold

    # 写入日志
    log_request(text, lang, prob, is_fraud)

    return DetectionResult(
        id=str(uuid.uuid4()),
        text=text,
        lang=lang,
        fraud_probability=round(prob, 4),
        is_fraud=is_fraud,
        risk_level=classify(prob),
        threshold=threshold,
        processing_time_ms=round(elapsed, 2)
    )

# ==================== API 路由 ====================
@app.post("/predict", response_model=DetectionResult)
def predict(req: DetectionRequest):
    lang = req.lang
    if lang == "auto":
        lang = detect_language(req.text)
    if lang not in ["en", "zh"]:
        raise HTTPException(400, "lang 参数仅支持 'en', 'zh', 'auto'")
    return analyze_text(req.text, lang)

@app.get("/")
def serve_index():
    """提供前端页面"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI Fraud Detection API is running. Place index.html in static folder for web UI."}

# ==================== 启动 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)