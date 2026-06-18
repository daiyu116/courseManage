# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
License 授权验证服务（客户版）
使用 RSA 非对称加密：公钥验证签名，私钥由供应商持有
客户无法自行生成 License Key
"""
import hashlib
import hmac
import json
import base64
import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

LICENSE_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzFFSwFC80ph80YuS1kp
npuG7+ngCx5n7ITiPVxFwBiPTGXcXYNUUmRAGi/E3reuMgtdzkK7MofwxhhXpSm1
eE2Bdca7VdLwuQLAT6VN++O/vo7IiVhJhQ1PY9ab0OEH5b8PYSJCaA8Da0eaIQ/y
rJ20rurj0FkGsuAcipChaDTKNhVZ86yrCFzbmR6b79kF2oGPkQ7ueMUVewf57tmd
sFsyWe8s/V0ZL8tl7Hauf3Ngyr2tiu876GnKDOGXaS4baWOGAtakiwUXxVy95VT7
M1U9pAxE2oO4LJgQBHqdU0JkRN1qEaZASU4I/WYmclbphtQBRZI7w8676A85QCyN
WwIDAQAB
-----END PUBLIC KEY-----"""

LICENSE_TYPES = {
    "trialA":     {"name": "试用授权", "days": 3},
    "trialB":     {"name": "试用授权", "days": 7},
    "monthly":    {"name": "月度订阅", "days": 30},
    "quarterly":  {"name": "季度订阅", "days": 90},
    "semiannual": {"name": "半年订阅", "days": 180},
    "annual":     {"name": "年度订阅", "days": 365},
    "perpetual":  {"name": "永久授权", "days": None},
}

PREMIUM_FEATURES = [
    "grade_trend",
    "fee_management",
    "smart_scheduling",
    "wechat_notify",
    "smart_command",
    "dashboard_view",
    "floating_sphere",
    "database_management",
    "student_evaluation",
]

FEATURE_NAMES = {
    "grade_trend": "学员成绩管理",
    "fee_management": "费用管理",
    "smart_scheduling": "智能算法排课",
    "wechat_notify": "微信通知管理",
    "smart_command": "智能指令管理",
    "dashboard_view": "运营大屏",
    "floating_sphere": "全站快捷按钮",
    "database_management": "数据库管理",
    "student_evaluation": "学员评价管理",
}

_SUpLIER_DISCOVERY = "https://courseManage-discovery.example.com/config"
_SUpLIER_COMM_DEFAULT = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=78f7362b-42a6-4d4b-813a-6a98f399f07c"
_SUpLIER_HB_DEFAULT = "https://courseManage-licence.service.local/api/v1/hb"
_DISCOVERY_INTERVAL = 86400
_HEARTBEAT_INTERVAL = 3600
_last_heartbeat_time = 0
_last_heartbeat_result = True
_cached_comm = None
_cached_hb = None
_last_discovery_time = 0


def _verify_discovery_sig(data: dict, sig: str) -> bool:
    raw = json.dumps({k: data[k] for k in sorted(data.keys())}, ensure_ascii=False)
    expected = hashlib.sha256(("courseManage-discovery-v1:" + raw).encode()).hexdigest()
    return hmac.compare_digest(expected, sig)


def _fetch_discovery() -> None:
    global _cached_comm, _cached_hb, _last_discovery_time
    try:
        import requests as _requests
        import time as _time
        now = _time.time()
        if _cached_comm is not None and now - _last_discovery_time < _DISCOVERY_INTERVAL:
            return
        resp = _requests.get(_SUpLIER_DISCOVERY, timeout=5)
        if resp.status_code != 200:
            return
        result = resp.json()
        sig = result.get("sig", "")
        payload = {k: v for k, v in result.items() if k != "sig"}
        if _verify_discovery_sig(payload, sig):
            if payload.get("comm"):
                _cached_comm = payload["comm"]
            if payload.get("hb"):
                _cached_hb = payload["hb"]
            _last_discovery_time = now
            logger.info("Supplier config refreshed from discovery")
    except Exception:
        logger.debug("Discovery fetch failed, using cached/default")


def get_supplier_comm() -> str:
    _fetch_discovery()
    return _cached_comm or _SUpLIER_COMM_DEFAULT


def get_supplier_hb() -> str:
    _fetch_discovery()
    return _cached_hb or _SUpLIER_HB_DEFAULT


_FEATURES_HMAC_SALT = b"courseManage-features-hmac-v2-8f3a1b7c9d2e"

def _get_hmac_key() -> bytes:
    raw = os.getenv("SECRET_KEY", "courseManage-default-hmac-key")
    combined = raw.encode() + _FEATURES_HMAC_SALT + LICENSE_PUBLIC_KEY_PEM.encode()[:64]
    return hashlib.sha256(combined).digest()


def sign_features(features_json: str) -> str:
    return hmac.new(_get_hmac_key(), features_json.encode(), hashlib.sha256).hexdigest()


def verify_features_signature(features_json: str, signature: str) -> bool:
    expected = sign_features(features_json)
    return hmac.compare_digest(expected, signature)


class LicenseService:
    """License 验证服务（客户版：仅验证，不生成）"""
    
    @staticmethod
    def get_machine_code() -> str:
        """获取服务器唯一标识（机器码）
        基于持久化的UUID生成，容器重建后机器码不变
        """
        machine_id_file = os.path.join(os.environ.get('BACKUP_DIR', '/app/backups'), '.machine_id')
        try:
            if os.path.exists(machine_id_file):
                with open(machine_id_file, 'r') as f:
                    persisted_id = f.read().strip()
                if persisted_id:
                    return hashlib.sha256(persisted_id.encode()).hexdigest()[:16]
        except Exception:
            pass
        new_id = str(uuid.uuid4())
        try:
            os.makedirs(os.path.dirname(machine_id_file), exist_ok=True)
            with open(machine_id_file, 'w') as f:
                f.write(new_id)
        except Exception:
            pass
        return hashlib.sha256(new_id.encode()).hexdigest()[:16]
    
    @staticmethod
    def _get_public_key():
        """加载 RSA 公钥"""
        return serialization.load_pem_public_key(
            LICENSE_PUBLIC_KEY_PEM.encode(),
            backend=default_backend(),
        )
    
    @staticmethod
    def verify_license(license_key: str, machine_code: str) -> Optional[Dict]:
        """
        验证 License Key（使用 RSA 公钥验证签名）
        
        Args:
            license_key: Base64 编码的 License Key
            machine_code: 当前服务器机器码
        
        Returns:
            验证成功返回含 features 等信息的字典，失败返回 None
        """
        try:
            license_data = json.loads(
                base64.urlsafe_b64decode(license_key.encode()).decode()
            )
            payload = license_data["payload"]
            signature_b64 = license_data["signature"]
            signature = base64.urlsafe_b64decode(signature_b64.encode())
            
            payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
            public_key = LicenseService._get_public_key()
            try:
                public_key.verify(
                    signature,
                    payload_str,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )
            except Exception:
                return None
            
            if payload.get("machine_code") != machine_code:
                return None
            
            if payload.get("expiry_date"):
                expiry = datetime.fromisoformat(payload["expiry_date"])
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                now_utc = datetime.now(timezone.utc)
                if now_utc > expiry:
                    return None
            
            return {
                "customer_id": payload.get("customer_id", ""),
                "organization_name": payload.get("organization_name") or payload.get("customer_name", ""),
                "license_type": payload.get("license_type", ""),
                "features": payload["features"],
                "issued_at": payload.get("issued_at", ""),
                "expiry_date": payload.get("expiry_date"),
                "activated": True,
                "referral_code": payload.get("referral_code", ""),
                "referral_threshold": payload.get("referral_threshold", 0),
                "discount_percent": payload.get("referral_discount", 0),
                "rebate_percent": payload.get("referral_rebate", 0),
                "license_price": payload.get("license_price", 0),
            }
        except Exception:
            return None
    
    @staticmethod
    def get_license_info(license_key: str) -> Optional[Dict]:
        """获取 License 信息（仅解析显示，不验证）"""
        try:
            license_data = json.loads(
                base64.urlsafe_b64decode(license_key.encode()).decode()
            )
            payload = license_data["payload"]
            return {
                "customer_id": payload.get("customer_id", ""),
                "organization_name": payload.get("organization_name") or payload.get("customer_name", ""),
                "license_type": payload.get("license_type", ""),
                "license_type_name": LICENSE_TYPES.get(
                    payload.get("license_type", ""), {}
                ).get("name", "未知"),
                "features": payload.get("features", []),
                "issued_at": payload.get("issued_at", ""),
                "expiry_date": payload.get("expiry_date"),
                "version": payload.get("version", ""),
                "referral_code": payload.get("referral_code", ""),
                "referral_threshold": payload.get("referral_threshold", 0),
                "discount_percent": payload.get("referral_discount", 0),
                "rebate_percent": payload.get("referral_rebate", 0),
                "license_price": payload.get("license_price", 0),
            }
        except Exception:
            return None

    @staticmethod
    def heartbeat_check(license_key: str, machine_code: str) -> bool:
        """向授权服务器发送心跳，检测 License 是否被撤销或多人使用"""
        global _last_heartbeat_time, _last_heartbeat_result

        hb_url = get_supplier_hb()
        if not hb_url:
            return True

        import time as _time
        now = _time.time()
        if now - _last_heartbeat_time < _HEARTBEAT_INTERVAL:
            return _last_heartbeat_result

        _last_heartbeat_time = now

        try:
            import requests as _requests
            resp = _requests.post(
                hb_url,
                json={"license_key": license_key, "machine_code": machine_code},
                timeout=5,
            )
            data = resp.json()
            _last_heartbeat_result = not data.get("revoked", False)
        except Exception:
            _last_heartbeat_result = True
            logger.debug("License heartbeat check failed, allowing continuation")

        return _last_heartbeat_result


_INTEGRITY_SALT = b"courseManage-integrity-v1"


def compute_module_hash(module_path: str) -> str:
    """计算模块文件的 SHA256 摘要（用于完整性校验）"""
    h = hashlib.sha256(_INTEGRITY_SALT)
    try:
        with open(module_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except FileNotFoundError:
        return ""
    return h.hexdigest()[:32]


def verify_compiled_modules() -> dict:
    """
    校验 Cython 编译后的关键模块是否被篡改
    在 Docker 环境中，这些模块应为 .so/.pyd 二进制文件
    返回 {"valid": bool, "details": dict}
    """
    import importlib
    critical_modules = [
        "utils.license",
        "routers.license",
        "optimizer",
        "utils.smart_command",
        "utils.wechat_notifier",
        "utils.remainder",
    ]
    details = {}
    all_valid = True
    for mod_name in critical_modules:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec and spec.origin:
                is_compiled = spec.origin.endswith((".so", ".pyd"))
                mod_hash = compute_module_hash(spec.origin)
                details[mod_name] = {
                    "path": spec.origin,
                    "compiled": is_compiled,
                    "hash": mod_hash,
                }
                if not is_compiled:
                    all_valid = False
                    details[mod_name]["warning"] = "Module is not compiled (source .py instead of .so/.pyd)"
            else:
                details[mod_name] = {"path": None, "compiled": False, "hash": "", "warning": "Module not found"}
                all_valid = False
        except Exception as e:
            details[mod_name] = {"path": None, "compiled": False, "hash": "", "error": str(e)}
            all_valid = False
    return {"valid": all_valid, "details": details}