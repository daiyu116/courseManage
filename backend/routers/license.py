# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
License 授权管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from models import Settings
from utils.license import LicenseService, PREMIUM_FEATURES, FEATURE_NAMES, LICENSE_TYPES, sign_features, verify_features_signature, get_supplier_comm
from routers.auth import get_current_system_admin_user, User, get_current_user
from utils.logger import log_operation
from datetime import datetime
import json
import os
import requests

router = APIRouter(prefix="/license", tags=["系统授权"])

class LicenseActivateRequest(BaseModel):
    license_key: str
    selected_features: Optional[List[str]] = None
    organization_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_wechat: Optional[str] = None
    remarks: Optional[str] = None

class LicenseStatusResponse(BaseModel):
    activated: bool = False
    license_type: str = ""
    license_type_name: str = ""
    organization_name: str = ""
    features: dict = {}
    expiry_date: Optional[str] = None
    issued_at: Optional[str] = None
    machine_code: str = ""
    trial_available: bool = True
    deactivated_licenses: List[dict] = []
    license_key: str = ""
    referral_code: str = ""
    referral_activated: bool = False
    referral_threshold: float = 0
    discount_percent: float = 0
    rebate_percent: float = 0
    total_spending: float = 0
    site_name: str = ""
    contact_person: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    contact_wechat: str = ""

class FeatureCheckResponse(BaseModel):
    feature: str
    enabled: bool

@router.get("/status", response_model=LicenseStatusResponse)
def get_license_status(db: Session = Depends(get_db)):
    """查询当前 License 状态"""
    settings = db.query(Settings).first()
    machine_code = LicenseService.get_machine_code()

    if not settings or not settings.license_key:
        deactivated_licenses = _load_deactivated_licenses(settings, db=db)
        return LicenseStatusResponse(
            activated=False,
            machine_code=machine_code,
            trial_available=True,
            deactivated_licenses=deactivated_licenses,
            referral_code=getattr(settings, 'referral_code', '') or '',
            referral_activated=getattr(settings, 'referral_activated', False) or False,
            referral_threshold=getattr(settings, 'referral_threshold', 0) or 0,
            discount_percent=getattr(settings, 'discount_percent', 0) or 0,
            rebate_percent=getattr(settings, 'rebate_percent', 0) or 0,
            total_spending=getattr(settings, 'total_spending', 0) or 0,
            site_name=getattr(settings, 'site_name', '') or '',
            contact_person=getattr(settings, 'contact_person', '') or '',
            contact_phone=getattr(settings, 'contact_phone', '') or '',
            contact_email=getattr(settings, 'contact_email', '') or '',
            contact_wechat=getattr(settings, 'contact_wechat', '') or '',
        )

    result = LicenseService.verify_license(settings.license_key, machine_code)
    if result:
        features_from_db = {}
        if settings.premium_features:
            try:
                data = json.loads(settings.premium_features)
                if isinstance(data, dict):
                    features_from_db = {k: v for k, v in data.items() if v and k != "_sig"}
                elif isinstance(data, list):
                    features_from_db = {f: True for f in data}
            except (json.JSONDecodeError, TypeError):
                pass
        license_features = {f: True for f in result.get("features", [])}
        if not features_from_db:
            features_from_db = license_features
        else:
            for f in result.get("features", []):
                if f not in features_from_db:
                    features_from_db[f] = True
        deactivated_licenses = _load_deactivated_licenses(settings, db=db)
        return LicenseStatusResponse(
            activated=True,
            license_type=result["license_type"],
            license_type_name=LICENSE_TYPES.get(result["license_type"], {}).get("name", ""),
            organization_name=result.get("organization_name") or result.get("customer_name") or "",
            features=features_from_db,
            expiry_date=result.get("expiry_date"),
            issued_at=result.get("issued_at"),
            machine_code=machine_code,
            trial_available=result["license_type"] != "trial",
            deactivated_licenses=deactivated_licenses,
            license_key=settings.license_key or '',
            referral_code=getattr(settings, 'referral_code', '') or '',
            referral_activated=getattr(settings, 'referral_activated', False) or False,
            referral_threshold=getattr(settings, 'referral_threshold', 0) or 0,
            discount_percent=getattr(settings, 'discount_percent', 0) or 0,
            rebate_percent=getattr(settings, 'rebate_percent', 0) or 0,
            total_spending=getattr(settings, 'total_spending', 0) or 0,
            site_name=getattr(settings, 'site_name', '') or '',
            contact_person=getattr(settings, 'contact_person', '') or '',
            contact_phone=getattr(settings, 'contact_phone', '') or '',
            contact_email=getattr(settings, 'contact_email', '') or '',
            contact_wechat=getattr(settings, 'contact_wechat', '') or '',
        )

    if settings:
        _append_deactivated(settings, settings.license_key)
        settings.license_key = None
        settings.premium_features = "{}"
        db.commit()
    # 返回停用历史
    deactivated_licenses = _load_deactivated_licenses(settings, db=db)
    
    return LicenseStatusResponse(
        activated=False,
        machine_code=machine_code,
        trial_available=True,
        deactivated_licenses=deactivated_licenses,
        referral_code=getattr(settings, 'referral_code', '') or '',
        referral_activated=getattr(settings, 'referral_activated', False) or False,
        referral_threshold=getattr(settings, 'referral_threshold', 0) or 0,
        discount_percent=getattr(settings, 'discount_percent', 0) or 0,
        rebate_percent=getattr(settings, 'rebate_percent', 0) or 0,
        total_spending=getattr(settings, 'total_spending', 0) or 0,
        site_name=getattr(settings, 'site_name', '') or '',
        contact_person=getattr(settings, 'contact_person', '') or '',
        contact_phone=getattr(settings, 'contact_phone', '') or '',
        contact_email=getattr(settings, 'contact_email', '') or '',
        contact_wechat=getattr(settings, 'contact_wechat', '') or '',
    )

@router.post("/activate")
def activate_license(
    request: LicenseActivateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user),
):
    """激活 License"""
    machine_code = LicenseService.get_machine_code()
    result = LicenseService.verify_license(request.license_key, machine_code)

    if not result:
        license_machine_code = "N/A"
        try:
            import base64
            license_data = json.loads(base64.urlsafe_b64decode(request.license_key.encode()).decode())
            license_machine_code = license_data.get("payload", {}).get("machine_code", "N/A")
        except Exception:
            pass
        
        log_operation(
            db, "系统授权", "激活失败",
            f"License验证失败 | 服务器机器码: {machine_code} | License中机器码: {license_machine_code}",
            current_user.username, "ERROR",
        )
        raise HTTPException(
            status_code=400,
            detail=f"License Key 无效、已过期或与当前服务器不匹配。服务器机器码: {machine_code}，License中机器码: {license_machine_code}。请联系供应商获取正确的 License Key。"
        )

    settings = db.query(Settings).first()

    # 验证联系信息（首次激活时必填）
    is_first_activation = not settings or not settings.license_key
    if is_first_activation:
        if not request.organization_name:
            raise HTTPException(status_code=400, detail="首次激活请填写机构名称")
        if not request.contact_person:
            raise HTTPException(status_code=400, detail="首次激活请填写联系人")
        if not request.contact_phone and not request.contact_email and not request.contact_wechat:
            raise HTTPException(status_code=400, detail="联系电话、电子邮件、联系微信至少填写一项")
    if not settings:
        features_dict = {f: True for f in result["features"]}
        features_json = json.dumps(features_dict, sort_keys=True, ensure_ascii=False)
        sig = sign_features(features_json)
        signed_dict = json.loads(features_json)
        signed_dict["_sig"] = sig
        settings = Settings(
            site_name="默认机构",
            license_key=request.license_key,
            premium_features=json.dumps(signed_dict),
        )
        db.add(settings)
    else:
        existing_features = []
        if settings.premium_features:
            try:
                data = json.loads(settings.premium_features)
                if isinstance(data, dict):
                    existing_features = [k for k, v in data.items() if v and k != "_sig"]
                elif isinstance(data, list):
                    existing_features = data
                else:
                    existing_features = []
            except (json.JSONDecodeError, TypeError):
                existing_features = []
        add_features = request.selected_features if request.selected_features else result["features"]
        merged = list(set(existing_features + add_features))
        features_dict = {f: True for f in merged}
        features_json = json.dumps(features_dict, sort_keys=True, ensure_ascii=False)
        sig = sign_features(features_json)
        signed_dict = json.loads(features_json)
        signed_dict["_sig"] = sig
        settings.license_key = request.license_key
        settings.premium_features = json.dumps(signed_dict)

    settings.referral_code = result.get("referral_code") or ""
    settings.referral_threshold = result.get("referral_threshold") or 0
    settings.discount_percent = result.get("discount_percent") or 0
    settings.rebate_percent = result.get("rebate_percent") or 0

    license_price = result.get("license_price", 0) or 0
    if license_price > 0:
        current_spending = getattr(settings, 'total_spending', 0) or 0
        settings.total_spending = current_spending + license_price

    if settings.referral_code:
        threshold = settings.referral_threshold or 0
        if threshold > 0 and settings.total_spending >= threshold:
            settings.referral_activated = True
        else:
            settings.referral_activated = False

    db.commit()
    
    type_name = LICENSE_TYPES.get(result["license_type"], {}).get("name", "未知")
    log_operation(
        db, "系统授权", "激活成功",
        f"客户: {result['organization_name']}, 类型: {type_name}, 功能: {result['features']}",
        current_user.username, "INFO",
    )
    webhook_data = {
        "action": "授权激活成功",
        "organization_name": request.organization_name or "",
        "contact_person": request.contact_person or "",
        "contact_phone": request.contact_phone or "",
        "contact_email": request.contact_email or "",
        "contact_wechat": request.contact_wechat or "",
        "remarks": request.remarks or "",
        "license_type": type_name,
        "features": result["features"],
        "machine_code": machine_code,
    }
    if result.get("expiry_date"):
        webhook_data["activated_date"] = result.get("issued_at") or datetime.now().strftime("%Y-%m-%d")
        webhook_data["expiry_date"] = result["expiry_date"]
    _send_webhook(webhook_data)
    return {
        "message": "License 激活成功",
        "license_type": result["license_type"],
        "license_type_name": type_name,
        "organization_name": result["organization_name"],
        "features": result["features"],
        "expiry_date": result.get("expiry_date"),
    }

@router.post("/deactivate")
def deactivate_license(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user),
):
    """停用 License（保留历史记录）"""
    settings = db.query(Settings).first()
    if settings and settings.license_key:
        entry = _build_deactivated_entry(settings.license_key)
        _append_deactivated(settings, entry)
        old_key = settings.license_key
        settings.license_key = None
        settings.premium_features = "{}"
        db.commit()
        log_operation(db, "系统授权", "停用", f"License已停用: {old_key[:16]}...", current_user.username, "INFO")
    return {"message": "License 已停用（历史记录已保留）"}

@router.post("/deactivate-feature/{feature_name}")
def deactivate_feature(
    feature_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user),
):
    """停用某个高级功能（同时停用该 License 下所有功能）"""
    if feature_name not in PREMIUM_FEATURES:
        raise HTTPException(status_code=400, detail=f"不支持的功能: {feature_name}")
    settings = db.query(Settings).first()
    if not settings or not settings.license_key:
        raise HTTPException(status_code=400, detail="当前无已授权功能")
    try:
        data = json.loads(settings.premium_features)
        if isinstance(data, dict):
            features = [k for k, v in data.items() if v]
        elif isinstance(data, list):
            features = data
        else:
            features = []
    except (json.JSONDecodeError, TypeError):
        features = []
    if feature_name not in features:
        raise HTTPException(status_code=400, detail="该功能未授权")
    entry = _build_deactivated_entry(settings.license_key)
    _append_deactivated(settings, entry)
    old_key = settings.license_key
    settings.license_key = None
    settings.premium_features = "{}"
    db.commit()
    log_operation(
        db, "系统授权", "停用功能",
        f"停用功能: {feature_name}，已同时停用该 License 下所有功能: {features}",
        current_user.username, "INFO",
    )
    return {"message": "该功能及关联的所有功能已停用", "deactivated_features": features}


@router.get("/machine-code")
def get_machine_code(current_user: User = Depends(get_current_user)):
    """获取当前服务器机器码"""
    return {"machine_code": LicenseService.get_machine_code()}

@router.get("/check/{feature_name}", response_model=FeatureCheckResponse)
def check_feature(feature_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """检查某个高级功能是否已授权"""
    enabled = _check_premium_feature(feature_name, db)
    return FeatureCheckResponse(feature=feature_name, enabled=enabled)

class LicenseApplyRequest(BaseModel):
    organization_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_wechat: Optional[str] = None
    remarks: Optional[str] = None
    selected_features: List[str] = []
    license_type: Optional[str] = None
    apply_type: str = "new"
    referral_code: Optional[str] = None

class SupplierViewNotifyRequest(BaseModel):
    organization_name: str
    contact_person: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_wechat: Optional[str] = None
    machine_code: str
    view_time: str

@router.post("/notify-supplier-view")
def notify_supplier_view(request: SupplierViewNotifyRequest, db: Session = Depends(get_db)):
    """通知供应商，有客户查看了联系信息"""
    _send_webhook({
        "action": "客户查看供应商联系信息",
        "organization_name": request.organization_name,
        "contact_person": request.contact_person,
        "contact_phone": request.contact_phone or "",
        "contact_email": request.contact_email or "",
        "contact_wechat": request.contact_wechat or "",
        "machine_code": request.machine_code,
        "view_time": request.view_time,
        "reminder": "请检查该客户是否有相关的授权申请并及时处理",
    })
    log_operation(
        db, "系统授权", "查看供应商信息",
        f"客户 {request.organization_name} 查看了供应商联系信息",
        "system", "INFO",
    )
    return {"status": "success"}


class AddonPreviewRequest(BaseModel):
    license_key: str
 
class AddonPreviewResponse(BaseModel):
    ok: bool
    organization_name: str
    license_type_name: str
    features: List[str]
 
@router.post("/preview-addon", response_model=AddonPreviewResponse)
def preview_addon_license(
    request: AddonPreviewRequest,
    db: Session = Depends(get_db),
):
    """预览追加授权的License信息"""
    machine_code = LicenseService.get_machine_code()
    result = LicenseService.verify_license(request.license_key, machine_code)
    if not result:
        raise HTTPException(status_code=400, detail="License Key 无效、已过期或与当前服务器不匹配")
    return AddonPreviewResponse(
        ok=True,
        organization_name=result["organization_name"],
        license_type_name=LICENSE_TYPES.get(result["license_type"], {}).get("name", "未知"),
        features=result["features"],
    )

@router.post("/apply")
def apply_license(
    request: LicenseApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user),
):
    """发起授权申请，向供应商发送 webhook"""
    if not request.organization_name:
        raise HTTPException(status_code=400, detail="请填写机构名称")
    if not request.contact_person:
        raise HTTPException(status_code=400, detail="请填写联系人")
    if not request.contact_phone and not request.contact_email and not request.contact_wechat:
        raise HTTPException(status_code=400, detail="联系电话、电子邮件、联系微信至少填写一项")
    if not request.selected_features:
        raise HTTPException(status_code=400, detail="请至少选择一个功能模块")
    if not request.license_type:
        raise HTTPException(status_code=400, detail="请选择授权类型")

    settings = db.query(Settings).first()
    own_referral_code = getattr(settings, 'referral_code', '') or ''
    if request.referral_code and own_referral_code and request.referral_code.strip() == own_referral_code.strip():
        raise HTTPException(status_code=400, detail="不能使用自己的推荐码")
 
    machine_code = LicenseService.get_machine_code()
    action_label = "申请追加授权" if request.apply_type == "addon" else "授权申请意向"
    feature_names = []
    for f in request.selected_features:
        feature_names.append(FEATURE_NAMES.get(f, f))
 
    lt_info = LICENSE_TYPES.get(request.license_type, {})
    lt_name = lt_info.get("name", request.license_type)
    lt_days = lt_info.get("days")
    license_type_label = f"{lt_name}({lt_days}天)" if lt_days else f"{lt_name}(永久)"
 
    _send_webhook({
        "action": action_label,
        "organization_name": request.organization_name or "",
        "contact_person": request.contact_person or "",
        "contact_phone": request.contact_phone or "",
        "contact_email": request.contact_email or "",
        "contact_wechat": request.contact_wechat or "",
        "remarks": request.remarks or "",
        "features": feature_names,
        "license_type": license_type_label,
        "machine_code": machine_code,
        "referral_code": request.referral_code or "",
    })
    if settings:
        if request.contact_person:
            settings.contact_person = request.contact_person
        if request.contact_phone:
            settings.contact_phone = request.contact_phone
        if request.contact_email:
            settings.contact_email = request.contact_email
        if request.contact_wechat:
            settings.contact_wechat = request.contact_wechat
        db.commit()
    log_operation(
        db, "系统授权", action_label,
        f"客户: {request.organization_name}, 功能: {feature_names}",
        current_user.username, "INFO",
    )

    email_sent = False
    try:
        email_settings = db.query(Settings).first()
        if email_settings and email_settings.email_config:
            email_config = json.loads(email_settings.email_config) if isinstance(email_settings.email_config, str) else email_settings.email_config
            if email_config.get("smtp_host") and email_config.get("smtp_user"):
                from utils.email_notifier import EmailNotifier
                notifier = EmailNotifier()
                notifier.load_config(json.dumps(email_config), email_settings.organization_name or "课程排课系统")
                notifier.load_promotion_info(
                    website=getattr(email_settings, 'organization_website', '') or '',
                    wechat_qr=getattr(email_settings, 'wechat_qrcode', '') or '',
                    work_wechat_qr=getattr(email_settings, 'work_wechat_qrcode', '') or '',
                )
                subject = f"【{action_label}】{request.organization_name or '客户'} - {license_type_label}"
                referral_row = f'<tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">推荐码</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.referral_code or "无"}</td></tr>' if request.referral_code else ''
                html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e4e7ed; border-radius: 8px;">
                    <h3 style="color: #409eff; border-bottom: 2px solid #409eff; padding-bottom: 8px;">{action_label}</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; width: 120px; background: #f5f7fa;">客户机构</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.organization_name or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">联系人</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.contact_person or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">联系电话</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.contact_phone or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">电子邮件</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.contact_email or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">联系微信</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.contact_wechat or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">授权类型</td><td style="padding: 8px; border: 1px solid #ebeef5;">{license_type_label}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">功能模块</td><td style="padding: 8px; border: 1px solid #ebeef5;">{', '.join(feature_names)}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">机器码</td><td style="padding: 8px; border: 1px solid #ebeef5; word-break: break-all;">{machine_code}</td></tr>
                        {referral_row}
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">备注</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.remarks or '无'}</td></tr>
                    </table>
                </div>
                """
                supplier_email = os.getenv("SUPPLIER_FEEDBACK_EMAIL", "meitianqiusuo@163.com")
                result = notifier.send_email([supplier_email], subject, html)
                if any(result.values()):
                    email_sent = True
    except Exception:
        pass

    return {"message": "申请已成功发送，请等待供应商联系您", "webhook_sent": bool(_get_webhook_url()), "email_sent": email_sent}


@router.get("/features", response_model=List[FeatureCheckResponse])
def list_features(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """列出所有高级功能及其授权状态"""
    return [
        FeatureCheckResponse(feature=f, enabled=_check_premium_feature(f, db))
        for f in PREMIUM_FEATURES
    ]
def _load_deactivated_licenses(settings, auto_repair=True, db=None) -> List[dict]:
    """从 settings 加载停用历史数组，并自动补全缺失的元数据"""
    if not settings or not settings.deactivated_licenses:
        return []
    try:
        data = json.loads(settings.deactivated_licenses)
        records = data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
    if not auto_repair:
        return records
    repaired = False
    for rec in records:
        if rec.get("license_key") and not rec.get("organization_name") and not rec.get("license_type_name"):
            info = LicenseService.get_license_info(rec["license_key"])
            if info:
                rec["organization_name"] = info.get("organization_name") or info.get("customer_name", "")
                rec["license_type"] = info.get("license_type", "")
                rec["license_type_name"] = LICENSE_TYPES.get(info.get("license_type"), {}).get("name", "")
                rec["issued_at"] = info.get("issued_at", "")
                rec["expiry_date"] = info.get("expiry_date")
                features = info.get("features", [])
                rec["features"] = features
                rec["feature_names"] = [FEATURE_NAMES.get(f, f) for f in features] if features else []
                repaired = True
        elif rec.get("license_key") and not rec.get("features"):
            info = LicenseService.get_license_info(rec["license_key"])
            if info:
                features = info.get("features", [])
                rec["features"] = features
                rec["feature_names"] = [FEATURE_NAMES.get(f, f) for f in features] if features else []
                if not rec.get("issued_at"):
                    rec["issued_at"] = info.get("issued_at", "")
                repaired = True
        elif rec.get("license_key") and not rec.get("issued_at"):
            info = LicenseService.get_license_info(rec["license_key"])
            if info:
                rec["issued_at"] = info.get("issued_at", "")
                repaired = True
    if repaired:
        settings.deactivated_licenses = json.dumps(records)
        if db:
            db.commit()
    return records
 
def _build_deactivated_entry(license_key: str) -> dict:
    """根据 license_key 构建停用记录，优先用 verify_license，失败则用 get_license_info 提取元数据"""
    entry = {"license_key": license_key, "deactivated_at": datetime.now().isoformat()}
    machine_code = LicenseService.get_machine_code()
    entry["machine_code"] = machine_code
    result = LicenseService.verify_license(license_key, machine_code)
    if not result:
        result = LicenseService.get_license_info(license_key)
    if result:
        features = result.get("features", [])
        feature_names = [FEATURE_NAMES.get(f, f) for f in features] if features else []
        entry.update({
            "organization_name": result.get("organization_name") or result.get("customer_name", ""),
            "license_type": result.get("license_type"),
            "license_type_name": LICENSE_TYPES.get(result.get("license_type"), {}).get("name", ""),
            "issued_at": result.get("issued_at", ""),
            "expiry_date": result.get("expiry_date"),
            "features": features,
            "feature_names": feature_names,
        })
    return entry

def _append_deactivated(settings, entry):
    """追加一条停用记录到 settings.deactivated_licenses"""
    if not settings:
        return
    existing = _load_deactivated_licenses(settings)
    if isinstance(entry, str):
        entry = _build_deactivated_entry(entry)
    # 避免重复追加同一个 key
    if not any(e.get("license_key") == entry.get("license_key") for e in existing):
        existing.append(entry)
        settings.deactivated_licenses = json.dumps(existing)
 
def _check_premium_feature(feature_name: str, db: Session) -> bool:
    """检查是否拥有指定高级功能（供其他路由模块调用）
    验证链：License Key RSA签名 → 心跳检测 → 数据库HMAC签名 → License授权范围校验
    """
    settings = db.query(Settings).first()
    if not settings or not settings.license_key:
        return False
    machine_code = LicenseService.get_machine_code()
    result = LicenseService.verify_license(settings.license_key, machine_code)
    if not result:
        _append_deactivated(settings, settings.license_key)
        settings.license_key = None
        settings.premium_features = "{}"
        db.commit()
        return False
    if not LicenseService.heartbeat_check(settings.license_key, machine_code):
        _append_deactivated(settings, settings.license_key)
        settings.license_key = None
        settings.premium_features = "{}"
        db.commit()
        return False
    licensed_features = set(result.get("features", []))
    if feature_name not in licensed_features:
        return False
    if not settings.premium_features:
        return feature_name in licensed_features
    try:
        data = json.loads(settings.premium_features)
        if isinstance(data, dict):
            if "_sig" in data:
                stored_sig = data.pop("_sig")
                clean_json = json.dumps(data, sort_keys=True, ensure_ascii=False)
                if not verify_features_signature(clean_json, stored_sig):
                    return False
                data = {k: v for k, v in data.items() if v}
            else:
                data = {k: v for k, v in data.items() if v}
            features = list(data.keys())
        elif isinstance(data, list):
            features = data
        else:
            return False
    except (json.JSONDecodeError, TypeError):
        return False
    return feature_name in features


class FeatureFeedbackRequest(BaseModel):
    organization_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_info: Optional[str] = None
    feature_module: Optional[str] = None
    feedback_time: Optional[str] = None
    feedback: str
    suggestion: str
    feedback_type: str = "feature"

class SystemFeedbackRequest(BaseModel):
    organization_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_info: Optional[str] = None
    feedback_time: Optional[str] = None
    feedback: str
    suggestion: str
    feedback_type: str = "system"


@router.post("/feedback")
def submit_feedback(request: FeatureFeedbackRequest, db: Session = Depends(get_db)):
    """提交功能使用反馈或系统使用反馈，发送到供应商webhook和客户配置的邮箱"""
    action_label = "功能使用反馈" if request.feedback_type == "feature" else "系统使用反馈"
    feature_label = request.feature_module or "整体系统"

    webhook_data = {
        "action": f"客户{action_label}",
        "organization_name": request.organization_name or "未填写",
        "contact_person": request.contact_person or "未填写",
        "contact_info": request.contact_info or "未填写",
        "remarks": f"功能模块: {feature_label}",
    }
    if request.feedback:
        webhook_data["feedback"] = request.feedback
    if request.suggestion:
        webhook_data["suggestion"] = request.suggestion

    lines = [
        f"## 客户{action_label}",
        f"> 客户机构: {request.organization_name or '未填写'}",
        f"> 客户联系人: {request.contact_person or '未填写'}",
        f"> 联系方式: {request.contact_info or '未填写'}",
        f"> 功能模块: {feature_label}",
        f"> 反馈时间: {request.feedback_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if request.feedback:
        lines.append(f"> 使用反馈: {request.feedback}")
    if request.suggestion:
        lines.append(f"> 功能建议或需求: {request.suggestion}")

    _wh_url = _get_webhook_url()
    if _wh_url:
        try:
            requests.post(_wh_url, json={
                "msgtype": "markdown",
                "markdown": {"content": '\n'.join(lines)}
            }, timeout=5)
        except Exception:
            pass

    email_sent = False
    try:
        settings = db.query(Settings).first()
        if settings and settings.email_config:
            email_config = json.loads(settings.email_config) if isinstance(settings.email_config, str) else settings.email_config
            if email_config.get("smtp_host") and email_config.get("smtp_user"):
                from utils.email_notifier import EmailNotifier
                notifier = EmailNotifier()
                notifier.load_config(json.dumps(email_config), settings.organization_name or "课程排课系统")
                notifier.load_promotion_info(
                    website=getattr(settings, 'organization_website', '') or '',
                    wechat_qr=getattr(settings, 'wechat_qrcode', '') or '',
                    work_wechat_qr=getattr(settings, 'work_wechat_qrcode', '') or '',
                )
                subject = f"【{action_label}】{request.organization_name or '客户'} - {feature_label}"
                html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e4e7ed; border-radius: 8px;">
                    <h3 style="color: #409eff; border-bottom: 2px solid #409eff; padding-bottom: 8px;">{action_label}</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; width: 120px; background: #f5f7fa;">客户机构</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.organization_name or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">客户联系人</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.contact_person or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">联系方式</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.contact_info or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">功能模块</td><td style="padding: 8px; border: 1px solid #ebeef5;">{feature_label}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">反馈时间</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.feedback_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">使用反馈</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.feedback or '无'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">功能建议或需求</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.suggestion or '无'}</td></tr>
                    </table>
                </div>
                """
                supplier_email = os.getenv("SUPPLIER_FEEDBACK_EMAIL", "meitianqiusuo@163.com")
                result = notifier.send_email([supplier_email], subject, html)
                if any(result.values()):
                    email_sent = True
    except Exception:
        pass

    log_operation(
        db, "系统授权", action_label,
        f"客户 {request.organization_name or '未知'} 提交了{action_label}，功能模块: {feature_label}",
        "system", "INFO",
    )
    return {"status": "success", "webhook_sent": bool(_get_webhook_url()), "email_sent": email_sent}


def _get_webhook_url():
    return get_supplier_comm()


def _send_webhook(data: dict):
    url = _get_webhook_url()
    if not url:
        return
    try:
        lines = [
            f"## {data.get('action', '')}",
            f"> 客户机构: {data.get('organization_name', '')}",
            f"> 联系人: {data.get('contact_person', '')}",
        ]
        if data.get('contact_phone'):
            lines.append(f"> 电话: {data['contact_phone']}")
        if data.get('contact_email'):
            lines.append(f"> 邮箱: {data['contact_email']}")
        if data.get('contact_wechat'):
            lines.append(f"> 微信: {data['contact_wechat']}")
        if data.get('remarks'):
            lines.append(f"> 备注: {data['remarks']}")
        if data.get('license_type'):
            lines.append(f"> 类型: {data['license_type']}")
        feats = data.get('features', [])
        if feats:
            lines.append(f"> 功能: {', '.join(feats)}")
        if data.get('activated_date'):
            lines.append(f"> 激活日期: {data['activated_date']}")
        if data.get('expiry_date'):
            lines.append(f"> 到期日期: {data['expiry_date']}")
        if data.get('machine_code'):
            lines.append(f"> 机器码: {data['machine_code']}")
        if data.get('referral_code'):
            lines.append(f"> 推荐码: {data['referral_code']}")
        if data.get('view_time'):
            lines.append(f"> 查看时间: {data['view_time']}")
        if data.get('reminder'):
            lines.append(f"> ⚠️ {data['reminder']}")
        requests.post(url, json={
            "msgtype": "markdown",
            "markdown": {"content": '\n'.join(lines)}
        }, timeout=5)
    except Exception:
        pass


class ReplaceLicenseRequest(BaseModel):
    organization_name: Optional[str] = None
    contact_person: Optional[str] = None
    original_license_key: Optional[str] = None
    license_type_name: Optional[str] = None
    original_machine_code: Optional[str] = None
    expiry_date: Optional[str] = None


@router.post("/request-replace")
def request_replace_license(request: ReplaceLicenseRequest, db: Session = Depends(get_db)):
    """申请更换License，发送通知到供应商webhook和客户配置的邮箱"""
    current_machine_code = LicenseService.get_machine_code()
    expiry_label = request.expiry_date if request.expiry_date else "永久有效"

    lines = [
        "## 客户申请更换License",
        f"> 客户机构: {request.organization_name or '未填写'}",
        f"> 客户联系人: {request.contact_person or '未填写'}",
        f"> 原License Key: {request.original_license_key or '未填写'}",
        f"> 原授权类型: {request.license_type_name or '未填写'}",
        f"> 原机器码: {request.original_machine_code or '未填写'}",
        f"> 当前机器码: {current_machine_code}",
        f"> 原有效期: {expiry_label}",
        f"> 申请时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    _wh_url = _get_webhook_url()
    if _wh_url:
        try:
            requests.post(_wh_url, json={
                "msgtype": "markdown",
                "markdown": {"content": '\n'.join(lines)}
            }, timeout=5)
        except Exception:
            pass

    email_sent = False
    try:
        settings = db.query(Settings).first()
        if settings and settings.email_config:
            email_config = json.loads(settings.email_config) if isinstance(settings.email_config, str) else settings.email_config
            if email_config.get("smtp_host") and email_config.get("smtp_user"):
                from utils.email_notifier import EmailNotifier
                notifier = EmailNotifier()
                notifier.load_config(json.dumps(email_config), settings.organization_name or "课程排课系统")
                notifier.load_promotion_info(
                    website=getattr(settings, 'organization_website', '') or '',
                    wechat_qr=getattr(settings, 'wechat_qrcode', '') or '',
                    work_wechat_qr=getattr(settings, 'work_wechat_qrcode', '') or '',
                )
                subject = f"【申请更换License】{request.organization_name or '客户'}"
                html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e4e7ed; border-radius: 8px;">
                    <h3 style="color: #E6A23C; border-bottom: 2px solid #E6A23C; padding-bottom: 8px;">申请更换License</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; width: 120px; background: #f5f7fa;">客户机构</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.organization_name or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">客户联系人</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.contact_person or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">原License Key</td><td style="padding: 8px; border: 1px solid #ebeef5; word-break: break-all;">{request.original_license_key or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">原授权类型</td><td style="padding: 8px; border: 1px solid #ebeef5;">{request.license_type_name or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">原机器码</td><td style="padding: 8px; border: 1px solid #ebeef5; word-break: break-all;">{request.original_machine_code or '未填写'}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">当前机器码</td><td style="padding: 8px; border: 1px solid #ebeef5; word-break: break-all;">{current_machine_code}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">原有效期</td><td style="padding: 8px; border: 1px solid #ebeef5;">{expiry_label}</td></tr>
                        <tr><td style="padding: 8px; border: 1px solid #ebeef5; font-weight: bold; background: #f5f7fa;">申请时间</td><td style="padding: 8px; border: 1px solid #ebeef5;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                    </table>
                </div>
                """
                supplier_email = os.getenv("SUPPLIER_FEEDBACK_EMAIL", "meitianqiusuo@163.com")
                result = notifier.send_email([supplier_email], subject, html)
                if any(result.values()):
                    email_sent = True
    except Exception:
        pass

    log_operation(
        db, "系统授权", "申请更换",
        f"客户 {request.organization_name or '未知'} 申请更换License，原机器码: {request.original_machine_code or '未知'}",
        "system", "INFO",
    )
    return {"status": "success", "webhook_sent": bool(_get_webhook_url()), "email_sent": email_sent}